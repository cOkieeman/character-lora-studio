"""Behavior tests for flat Krea 2 export checks, with real Pillow image decoding."""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugins/character-lora-studio/skills/character-lora-studio/scripts/audit_dataset.py"
)
SPEC = importlib.util.spec_from_file_location("dataset_audit", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(SCRIPT.parent))
try:
    SPEC.loader.exec_module(AUDIT)
finally:
    sys.path.pop(0)


class DatasetAuditTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.dataset = self.root / "训练 dataset"
        self.dataset.mkdir()

    def pair(
        self,
        name="one.png",
        caption="kzara woman is standing.",
        size=(512, 512),
        color="red",
    ):
        path = self.dataset / name
        Image.new("RGB", size, color).save(path)
        path.with_suffix(".txt").write_text(caption, encoding="utf-8")
        return path

    def audit(self, **kwargs):
        kwargs.setdefault("triggers", ["kzara"])
        return AUDIT.audit_dataset(self.dataset, **kwargs)

    def cast(self, images=None):
        path = self.root / "cast.json"
        data = {
            "characters": {"a": "kzara", "b": "mivon"},
            "images": images
            or {"a.png": ["a"], "b.png": ["b"], "pair.png": ["a", "b"]},
        }
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = AUDIT.main([str(self.dataset), *args])
        return result, out.getvalue(), err.getvalue()

    def test_valid_pair_passes_without_modifying_files(self):
        self.pair()
        before = {p.name: p.read_bytes() for p in self.dataset.iterdir()}
        report = self.audit()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["paired_count"], 1)
        self.assertEqual(
            before, {p.name: p.read_bytes() for p in self.dataset.iterdir()}
        )

    def test_casefold_duplicate_stems_do_not_hide_an_image(self):
        self.pair("one.png")
        Image.new("RGB", (512, 512), "blue").save(self.dataset / "ONE.jpg")
        report = self.audit()
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["image_count"], 2)
        self.assertEqual(len(report["duplicate_stems"]["one"]), 2)

    def test_caption_stem_case_mismatch_is_not_a_portable_pair(self):
        Image.new("RGB", (512, 512), "red").save(self.dataset / "Hero.png")
        (self.dataset / "hero.txt").write_text("kzara stands.", encoding="utf-8")
        report = self.audit()
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["paired_count"], 0)
        self.assertEqual(report["case_mismatches"], {"Hero.png": "hero.txt"})

    def test_uppercase_caption_extension_is_not_a_portable_pair(self):
        Image.new("RGB", (512, 512), "red").save(self.dataset / "Hero.png")
        (self.dataset / "Hero.TXT").write_text("kzara stands.", encoding="utf-8")
        report = self.audit()
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["paired_count"], 0)
        self.assertEqual(report["case_mismatches"], {"Hero.png": "Hero.TXT"})

    def test_trigger_substrings_and_case_changes_fail(self):
        for caption in ("notkzara", "kzara_outfit", "kzara-dress", "Kzara woman"):
            with self.subTest(caption=caption):
                self.pair(caption=caption)
                self.assertTrue(self.audit()["missing_triggers"])
        self.pair(caption="(kzara), a woman looking left.")
        self.assertEqual(self.audit()["status"], "PASS")

    def test_repeat_triggers_are_all_required(self):
        self.pair(caption="kzara wears ordinary clothes.")
        self.assertEqual(self.audit(triggers=["kzara", "dressone"])["status"], "FAIL")
        self.pair(caption="kzara wears dressone.")
        self.assertEqual(self.audit(triggers=["kzara", "dressone"])["status"], "PASS")

    def test_missing_pillow_cannot_return_pass(self):
        self.pair()
        with patch.dict(sys.modules, {"PIL": None}):
            status, _, error = self.cli("--trigger", "kzara")
        self.assertEqual(status, 2)
        self.assertIn("Pillow is required", error)

    def test_empty_and_undersized_datasets_fail(self):
        self.assertEqual(self.audit()["status"], "FAIL")
        self.pair(size=(511, 512))
        report = self.audit()
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["undersized_images"], {"one.png": [511, 512]})

    def test_corrupt_image_and_invalid_utf8_fail(self):
        path = self.pair()
        path.write_bytes(b"not an image")
        path.with_suffix(".txt").write_bytes(b"\xff")
        report = self.audit()
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["unreadable_images"], ["one.png"])
        self.assertEqual(report["unreadable_captions"], ["one.txt"])

    def test_missing_or_empty_captions_and_orphans_fail(self):
        self.pair(caption=" ")
        (self.dataset / "orphan.txt").write_text("kzara")
        Image.new("RGB", (512, 512), "blue").save(self.dataset / "unpaired.png")
        report = self.audit()
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["empty_captions"], ["one.txt"])
        self.assertEqual(report["missing_images"], ["orphan.txt"])
        self.assertEqual(report["missing_captions"], ["unpaired.png"])

    def test_duplicate_captions_warn_or_fail_in_strict_mode(self):
        self.pair("one.png", color="red")
        self.pair("two.png", color="blue")
        self.assertEqual(self.audit()["status"], "PASS")
        self.assertTrue(self.audit()["duplicate_captions"])
        self.assertEqual(self.audit(strict=True)["status"], "FAIL")

    def test_duplicate_image_hashes_fail_with_distinct_captions(self):
        self.pair("one.png", caption="kzara stands.")
        self.pair("two.png", caption="kzara sits.")
        self.assertEqual(self.audit()["status"], "FAIL")
        self.assertTrue(self.audit()["duplicate_images"])

    def test_explicit_zero_outfit_count_is_checked(self):
        self.pair()
        report = self.audit(outfit_tokens=["blueoutfit"], expected_per_outfit=1)
        self.assertEqual(report["count_mismatches"], {"blueoutfit": 0})
        self.assertEqual(report["status"], "FAIL")
        with self.assertRaises(ValueError):
            self.audit(expected_per_outfit=15)

    def test_opt_in_regex_counts_complete_matches_with_groups(self):
        self.pair(caption="kzara wears SomeDress2.")
        report = self.audit(outfit_regex=r"SomeDress(\d+)")
        self.assertEqual(report["outfit_counts"], {"SomeDress2": 1})

    def test_nested_images_cannot_be_silently_ignored(self):
        self.pair()
        nested = self.dataset / "hidden"
        nested.mkdir()
        Image.new("RGB", (512, 512), "blue").save(nested / "missing.png")
        self.assertEqual(self.audit()["status"], "FAIL")

    def test_cast_solos_and_both_position_orders_pass(self):
        self.pair("a.png", "kzara woman sits.", color="red")
        self.pair("b.png", "mivon man walks.", color="blue")
        self.pair(
            "pair.png",
            "kzara woman stands left; mivon man stands right.",
            color="green",
        )
        cast = self.cast()
        self.assertEqual(
            self.audit(triggers=None, cast_manifest=cast)["status"], "PASS"
        )
        (self.dataset / "pair.txt").write_text(
            "mivon man stands left; kzara woman stands right."
        )
        self.assertEqual(
            self.audit(triggers=None, cast_manifest=cast)["status"], "PASS"
        )
        (self.dataset / "a.txt").write_text("kzara woman stands with mivon man.")
        report = self.audit(triggers=None, cast_manifest=cast)
        self.assertEqual(report["absent_character_triggers"], {"a.txt": ["mivon"]})
        self.assertEqual(report["status"], "FAIL")

    def test_cast_pair_missing_identity_and_stale_mapping_fail(self):
        self.pair("pair.png", "kzara woman stands.")
        cast = self.cast({"pair.png": ["a", "b"]})
        report = self.audit(triggers=None, cast_manifest=cast)
        self.assertEqual(report["missing_triggers"], {"pair.txt": ["mivon"]})
        cast = self.cast({"missing.png": ["a"]})
        report = self.audit(triggers=None, cast_manifest=cast)
        self.assertEqual(report["cast_missing_images"], ["pair.png"])
        self.assertEqual(report["cast_stale_images"], ["missing.png"])

    def test_invalid_cast_manifests_are_configuration_errors(self):
        for images in (
            {"../a.png": ["a"]},
            {"a.png": ["unknown"]},
            {"a.png": []},
            {"a.png": ["a", "a"]},
        ):
            with self.subTest(images=images):
                path = self.cast(images)
                with self.assertRaises(ValueError):
                    AUDIT.load_cast_manifest(path)
        path.write_text(
            '{"characters":{"a":"kzara","b":"mivon"},"images":{"a.png":["a"],"a.png":["b"]}}'
        )
        with self.assertRaises(ValueError):
            AUDIT.load_cast_manifest(path)

    def test_cli_codes_and_safe_json_destination(self):
        self.pair()
        self.assertEqual(self.cli("--trigger", "kzara")[0], 0)
        self.assertEqual(self.cli("--trigger", "wrong")[0], 1)
        self.assertEqual(self.cli("--trigger", "kzara", "--outfit-regex", "[")[0], 2)
        caption = self.dataset / "one.txt"
        original = caption.read_bytes()
        self.assertEqual(
            self.cli("--trigger", "kzara", "--json-output", str(caption))[0], 2
        )
        self.assertEqual(caption.read_bytes(), original)
        output = self.root / "audit.json"
        self.assertEqual(
            self.cli("--trigger", "kzara", "--json-output", str(output))[0], 0
        )
        self.assertEqual(
            json.loads(output.read_text(encoding="utf-8"))["status"], "PASS"
        )
        self.assertEqual(
            self.cli("--trigger", "kzara", "--json-output", str(output))[0], 2
        )


if __name__ == "__main__":
    unittest.main()
