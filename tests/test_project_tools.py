"""Behavior checks for non-destructive initialization and dataset audit gates."""

import base64
import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "plugins/character-lora-studio/skills/character-lora-studio"
sys.path.insert(0, str(SKILL / "scripts"))
from caption_triggers import (
    check_caption_triggers,
    load_cast_manifest,
    validate_cast_manifest,
)

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
        config = (self.management / "角色配置.yaml").read_text(encoding="utf-8")
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

    def cast_manifest(self, row, identities=None):
        return {"characters": {"a": "kzara", "b": "mivon"},
                "images": {row["file"]: identities or ["a"]}}

    def cast_row(self, text="kzara woman is standing."):
        row = self.approved()
        for family in ("anima", "krea2"):
            self.put(row[f"{family}_caption_file"], text)
        self.write_rows([row])
        return row

    def test_cast_init_uses_no_global_or_project_id_trigger(self):
        cast_root = self.root.parent / "cast"
        TOOLS.initialize(cast_root, "my_cast", "Two characters", concept="cast")
        config = (cast_root / TOOLS.MANAGEMENT / "角色配置.yaml").read_text(encoding="utf-8")
        self.assertIn("type: cast", config)
        self.assertIn('trigger: ""', config)
        self.assertIn("forbidden_tags: []", config)
        self.assertNotIn("1girl, , solo", config)
        self.assertNotIn("{{", config)
        with self.assertRaisesRegex(ValueError, "per-character"):
            TOOLS.initialize(cast_root, "my_cast", "Two characters", "my_cast", "cast")

    def test_single_init_still_requires_trigger_and_valid_concept(self):
        with self.assertRaises(ValueError):
            TOOLS.initialize(self.root.parent / "invalid", "example", "Example")
        with self.assertRaisesRegex(ValueError, "concept"):
            TOOLS.initialize(self.root.parent / "invalid", "example", "Example", "example", "bad")

    def test_cast_solo_and_pair_require_only_visible_identities(self):
        row = self.cast_row()
        manifest = self.cast_manifest(row)
        report = TOOLS.audit(self.root, ["krea2"], True, "", cast_manifest=manifest)
        self.assertEqual(report["errors"], [])
        for family in ("anima", "krea2"):
            self.put(row[f"{family}_caption_file"], "kzara woman stands left; mivon man stands right.")
        manifest["images"][row["file"]] = ["a", "b"]
        self.assertEqual(TOOLS.audit(self.root, ["krea2"], True, "", cast_manifest=manifest)["errors"], [])

    def test_cast_detects_missing_and_wrong_identity_tokens(self):
        row = self.cast_row("kzara_outfit woman stands beside mivon man.")
        report = TOOLS.audit(self.root, ["krea2"], True, "", cast_manifest=self.cast_manifest(row))
        self.assertTrue(any("missing exact trigger: 'kzara'" in error for error in report["errors"]))
        self.assertTrue(any("unexpected cast trigger: 'mivon'" in error for error in report["errors"]))
        row = self.cast_row("kzara woman stands left.")
        report = TOOLS.audit(self.root, ["krea2"], True, "", cast_manifest=self.cast_manifest(row, ["a", "b"]))
        self.assertTrue(any("missing exact trigger: 'mivon'" in error for error in report["errors"]))

    def test_cast_export_manifest_matches_approved_training_membership(self):
        row = self.cast_row()
        manifest = self.cast_manifest(row)
        manifest["images"] = {"03_训练候选/stale.png": ["a"]}
        report = TOOLS.audit(self.root, ["krea2"], True, "", cast_manifest=manifest)
        self.assertTrue(any("missing cast mapping" in error for error in report["errors"]))
        self.assertTrue(any("Stale cast mapping" in error for error in report["errors"]))
        report = TOOLS.audit(self.root, [], False, "", cast_manifest=manifest)
        self.assertTrue(any("missing cast mapping" in warning for warning in report["warnings"]))

    def test_nonapproved_caption_is_checked_only_if_mapped(self):
        row = self.cast_row("unmapped candidate caption")
        row.update(status="candidate")
        self.write_rows([row])
        manifest = self.cast_manifest(row)
        manifest["images"] = {"03_训练候选/other.png": ["a"]}
        self.assertEqual(TOOLS.audit(self.root, [], False, "", cast_manifest=manifest)["errors"], [])
        manifest["images"][row["file"]] = ["a"]
        errors = TOOLS.audit(self.root, [], False, "", cast_manifest=manifest)["errors"]
        self.assertTrue(any("missing exact trigger" in error for error in errors))

    def test_cast_and_global_trigger_are_mutually_exclusive(self):
        row = self.cast_row()
        with self.assertRaisesRegex(ValueError, "either trigger or cast_manifest"):
            TOOLS.audit(self.root, ["krea2"], True, "example", cast_manifest=self.cast_manifest(row))

    def regularization_row(self, training_row, text="An ordinary person in a blue coat."):
        row = training_row.copy()
        path = self.put("06_正则集/prior.png", PNG + b"prior")
        row.update(image_id="prior001", file="06_正则集/prior.png", category="regularization",
                   source_kind="source", batch_id="", prompt_file="", pack="", sha256=TOOLS.digest(path))
        for family in ("anima", "krea2"):
            relative = f"06_正则集/{family}/prior.txt"
            self.put(relative, text)
            row[f"{family}_caption_file"] = relative
        self.write_rows([training_row, row])
        return row

    def test_single_regularization_excludes_identity_trigger(self):
        training = self.approved()
        prior = self.regularization_row(training)
        self.assertEqual(self.audit(ready=True)["errors"], [])
        self.put(prior["krea2_caption_file"], "example is standing in a blue coat.")
        errors = self.audit(ready=True)["errors"]
        self.assertTrue(any("regularization caption contains forbidden project trigger: 'example'" in e for e in errors))
        self.assertFalse(any("missing exact trigger" in e for e in errors))

    def test_cast_regularization_excludes_all_cast_triggers(self):
        training = self.cast_row()
        prior = self.regularization_row(training)
        manifest = self.cast_manifest(training)
        self.assertEqual(TOOLS.audit(self.root, ["krea2"], True, "", cast_manifest=manifest)["errors"], [])
        for token in ("kzara", "mivon"):
            with self.subTest(trigger=token):
                self.put(prior["krea2_caption_file"], f"{token} stands in a blue coat.")
                errors = TOOLS.audit(self.root, ["krea2"], True, "", cast_manifest=manifest)["errors"]
                self.assertTrue(any(f"forbidden project trigger: '{token}'" in e for e in errors))
        self.put(prior["krea2_caption_file"], "A woman wears kzara_style and a mivon-like coat.")
        self.assertEqual(TOOLS.audit(self.root, ["krea2"], True, "", cast_manifest=manifest)["errors"], [])

    def test_reference_categories_do_not_require_training_trigger(self):
        training = self.approved()
        reference = self.regularization_row(training)
        for category in ("evaluation", "source", "design"):
            with self.subTest(category=category):
                reference["category"] = category
                self.write_rows([training, reference])
                self.assertEqual(self.audit(ready=True)["errors"], [])
        cast_training = self.cast_row()
        reference = self.regularization_row(cast_training)
        manifest = self.cast_manifest(cast_training)
        for category in ("evaluation", "source", "design"):
            with self.subTest(cast_category=category):
                reference["category"] = category
                self.write_rows([cast_training, reference])
                self.assertEqual(TOOLS.audit(self.root, ["krea2"], True, "", cast_manifest=manifest)["errors"], [])

    def test_cast_cli_init_and_export_audit(self):
        row = self.cast_row()
        manifest_path = self.put("00_项目管理/cast.json", json.dumps(self.cast_manifest(row)))
        command = [sys.executable, str(SKILL / "scripts/project_tools.py")]
        result = subprocess.run(command + ["audit", str(self.root), "--ready-for-export", "--family", "krea2",
                                          "--cast-manifest", str(manifest_path)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(json.loads(result.stdout)["status"], "PASS")
        invalid = subprocess.run(command + ["audit", str(self.root), "--trigger", "example",
                                           "--cast-manifest", str(manifest_path)], capture_output=True, text=True, check=False)
        self.assertEqual(invalid.returncode, 2)
        new_root = self.root.parent / "cli-cast"
        initialized = subprocess.run(command + ["init", str(new_root), "--concept", "cast",
                                               "--character-id", "duo", "--display-name", "Duo"],
                                     capture_output=True, text=True, check=False)
        self.assertEqual(initialized.returncode, 0, initialized.stderr)


class CastManifestTests(unittest.TestCase):
    def valid(self):
        return {"characters": {"a": "kzara", "b": "mivon"}, "images": {"solo.png": ["a"]}}

    def test_exact_boundaries_and_case(self):
        self.assertEqual(check_caption_triggers("kzara, waves.", ["kzara"], ["mivon"]), [])
        for text in ("akzara", "kzara2", "kzara_outfit", "kzara-outfit", "KZARA"):
            with self.subTest(text=text):
                self.assertTrue(check_caption_triggers(text, ["kzara"], []))

    def test_manifest_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cast.json"
            for payload in (
                '{"characters":{"a":"kzara","a":"mivon"},"images":{"solo.png":["a"]}}',
                '{"characters":{"a":"kzara","b":"mivon"},"images":{"solo.png":["a"],"solo.png":["b"]}}',
            ):
                path.write_text(payload, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
                    load_cast_manifest(path)

    def test_manifest_rejects_invalid_identities_and_empty_mappings(self):
        bad = [None, {}, {"characters": {}, "images": {}},
               {"characters": {"a": "kzara"}, "images": {"solo.png": ["a"]}}]
        for field, value in (("characters", {"a": "kzara", "b": "kzara"}),
                             ("characters", {"a": "kzara", "b": "kzara woman"}),
                             ("characters", {"a": "", "b": "mivon"}),
                             ("images", {}), ("images", {"solo.png": []}),
                             ("images", {"solo.png": ["unknown"]}),
                             ("images", {"solo.png": ["a", "a"]}),
                             ("images", {"solo.png": "a"})):
            manifest = self.valid()
            manifest[field] = value
            bad.append(manifest)
        for manifest in bad:
            with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                validate_cast_manifest(manifest)

    def test_manifest_rejects_unsafe_or_ambiguous_paths(self):
        for relative in ("/solo.png", "../solo.png", "folder/../solo.png", "folder\\solo.png",
                         "C:/solo.png", "C:solo.png", "./solo.png", "folder//solo.png", "", "x\n.png"):
            manifest = self.valid()
            manifest["images"] = {relative: ["a"]}
            with self.subTest(path=relative), self.assertRaises(ValueError):
                validate_cast_manifest(manifest)
        manifest = self.valid()
        manifest["images"]["SOLO.PNG"] = ["b"]
        with self.assertRaisesRegex(ValueError, "case-insensitive"):
            validate_cast_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
