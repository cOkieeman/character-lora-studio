"""Behavior checks for non-destructive initialization and dataset audit gates."""

import base64
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "plugins/character-lora-studio/skills/character-lora-studio"
SPEC = importlib.util.spec_from_file_location("project_tools", SKILL / "scripts/project_tools.py")
TOOLS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOLS)
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1sAAAAASUVORK5CYII=")


class ProjectToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "角色 project"
        TOOLS.initialize(self.root, "example", '角色 "quoted"', "example")
        self.management = self.root / TOOLS.MANAGEMENT
        self.header = next(csv.reader((SKILL / "assets/inventory.template.csv").read_text().splitlines()))

    def put(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode())
        return path

    def write_rows(self, rows):
        with (self.management / "图片清单.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, self.header)
            writer.writeheader()
            writer.writerows(rows)

    def candidate(self):
        path = self.put("03_训练候选/example.png", PNG)
        self.put("00_项目管理/prompts/b001.txt", "Executed image prompt")
        self.put("00_项目管理/生成批次.csv", "batch_id,pack\nb001,A\n")
        row = dict.fromkeys(self.header, "")
        row.update(image_id="img001", file="03_训练候选/example.png", category="training_candidate",
                   status="candidate", source_kind="generated", pack="A", batch_id="b001",
                   prompt_file="00_项目管理/prompts/b001.txt", sha256=TOOLS.digest(path),
                   anima_caption_status="pending", krea2_caption_status="pending",
                   hub_image_review_status="not_requested", hub_anima_review_status="not_requested",
                   hub_krea2_review_status="not_requested")
        return row

    def approved(self):
        row = self.candidate()
        row.update(status="approved", review_source="plugin")
        for family, text in (("anima", "1girl, example, solo, white background"),
                             ("krea2", "example is standing against a white background.")):
            relative = f"04_正式训练集/captions/{family}/example.txt"
            self.put(relative, text)
            row[f"{family}_caption_file"] = relative
            row[f"{family}_caption_status"] = "reviewed"
        return row

    def audit(self, ready=False, hub=False):
        return TOOLS.audit(self.root, ["anima", "krea2"], ready, "example", hub)

    def test_init_preserves_user_files_and_is_idempotent(self):
        self.put("原始设定.md", "unchanged")
        self.put("00_项目管理/角色配置.yaml", "custom: true\n")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        TOOLS.initialize(self.root, "example", "角色", "example")
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_yaml_display_name_is_escaped(self):
        import json
        config = (self.management / "角色配置.yaml").read_text()
        value = next(line.split(": ", 1)[1] for line in config.splitlines() if line.startswith("display_name:"))
        self.assertEqual(json.loads(value), '角色 "quoted"')

    def test_empty_project_is_not_export_ready(self):
        self.assertEqual(self.audit()["status"], "PASS")
        self.assertEqual(self.audit(ready=True)["status"], "FAIL")

    def test_candidate_not_double_counted_by_captions_or_derivatives(self):
        row = self.approved()
        derived = row.copy()
        path = self.put("03_训练候选/crop.png", PNG + b"derived")
        derived.update(image_id="img002", file="03_训练候选/crop.png", source_kind="derived",
                       parent_id="img001", sha256=TOOLS.digest(path), status="needs_review",
                       anima_caption_file="", krea2_caption_file="",
                       anima_caption_status="pending", krea2_caption_status="pending")
        self.write_rows([row, derived])
        report = self.audit()
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["generated_candidate_images_unique"], 1)
        self.assertEqual(report["approved_training_images_unique"], 1)

    def test_hub_second_review_is_optional_and_dimension_specific(self):
        row = self.approved()
        self.write_rows([row])
        self.assertEqual(self.audit(ready=True)["status"], "PASS")
        self.assertEqual(self.audit(ready=True, hub=True)["status"], "FAIL")
        row.update(hub_image_review_status="approved", hub_anima_review_status="approved")
        self.write_rows([row])
        self.assertTrue(any("Hub krea2" in error for error in self.audit(ready=True, hub=True)["errors"]))
        row["hub_krea2_review_status"] = "approved"
        self.write_rows([row])
        self.assertEqual(self.audit(ready=True, hub=True)["status"], "PASS")

    def test_families_cannot_share_caption_or_inherit_review(self):
        row = self.approved()
        row["krea2_caption_file"] = row["anima_caption_file"]
        self.write_rows([row])
        self.assertTrue(any("share one caption" in e for e in self.audit()["errors"]))
        row["krea2_caption_file"] = ""
        self.write_rows([row])
        self.assertEqual(self.audit(ready=True)["status"], "FAIL")

    def test_exact_trigger_and_stale_hash_are_detected(self):
        row = self.approved()
        self.put(row["anima_caption_file"], "1girl, example_outfit, solo")
        self.put(row["file"], PNG + b"changed")
        self.write_rows([row])
        errors = self.audit()["errors"]
        self.assertTrue(any("exact trigger" in e for e in errors))
        self.assertTrue(any("SHA-256" in e for e in errors))

    def test_duplicate_approved_pixels_fail(self):
        row = self.approved()
        other = row.copy()
        self.put("03_训练候选/copy.png", PNG)
        other.update(image_id="img002", file="03_训练候选/copy.png", anima_caption_file="",
                     krea2_caption_file="", anima_caption_status="pending", krea2_caption_status="pending")
        self.write_rows([row, other])
        report = self.audit()
        self.assertEqual(report["generated_candidate_images_unique"], 1)
        self.assertTrue(any("duplicates approved" in e for e in report["errors"]))

    def test_unknown_batch_and_missing_parent_fail(self):
        row = self.candidate()
        row.update(batch_id="missing", parent_id="missing")
        self.write_rows([row])
        errors = self.audit()["errors"]
        self.assertTrue(any("batch_id" in e for e in errors))
        self.assertTrue(any("parent_id" in e for e in errors))

    def test_paths_cannot_leave_project(self):
        outside = self.root.parent / "outside.png"
        outside.write_bytes(PNG)
        row = self.candidate()
        row["file"] = "../outside.png"
        self.write_rows([row])
        self.assertTrue(any("leaves project" in e for e in self.audit()["errors"]))

    def test_unregistered_images_block_export(self):
        row = self.approved()
        self.write_rows([row])
        self.put("03_训练候选/forgotten.png", PNG)
        self.assertEqual(self.audit(ready=True)["status"], "FAIL")

    def test_legacy_inventory_is_not_silently_migrated(self):
        path = self.management / "图片清单.csv"
        path.write_text("file,status\nold.png,approved\n")
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "Legacy"):
            self.audit()
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
