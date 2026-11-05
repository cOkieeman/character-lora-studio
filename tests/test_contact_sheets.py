"""Observable checks for review-sheet fidelity and non-destructive outputs."""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw

SKILL = (
    Path(__file__).resolve().parents[1]
    / "plugins/character-lora-studio/skills/character-lora-studio"
)
SPEC = importlib.util.spec_from_file_location(
    "make_contact_sheets", SKILL / "scripts/make_contact_sheets.py"
)
SHEETS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SHEETS)


class ContactSheetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dataset = self.root / "训练图"
        self.dataset.mkdir()
        self.output = self.root / "review"

    def put_image(self, name="01.png", color="red", size=(80, 100)):
        path = self.dataset / name
        Image.new("RGB", size, color).save(path)
        return path

    def test_natural_sort_handles_numeric_prefixes_and_mixed_names(self):
        names = ["a10.png", "10.png", "a2.png", "2.png", "角色10.png", "角色2.png"]
        result = [p.name for p in sorted(map(Path, names), key=SHEETS.natural_key)]
        self.assertLess(result.index("2.png"), result.index("10.png"))
        self.assertLess(result.index("a2.png"), result.index("a10.png"))
        self.assertLess(result.index("角色2.png"), result.index("角色10.png"))

    def test_transparent_pixels_are_composited_on_light_tile(self):
        path = self.dataset / "alpha.png"
        image = Image.new("RGBA", (20, 20), (255, 0, 0, 0))
        image.putpixel((10, 10), (0, 0, 255, 255))
        image.save(path)
        tile = SHEETS.read_thumbnail(path, (20, 20))
        self.assertEqual(tile.getpixel((0, 0)), SHEETS.TILE_BACKGROUND)
        self.assertEqual(tile.getpixel((10, 10)), (0, 0, 255))

    def test_exif_rotation_is_applied(self):
        path = self.dataset / "rotated.jpg"
        source = Image.new("RGB", (40, 20), "red")
        exif = Image.Exif()
        exif[274] = 6
        source.save(path, exif=exif)
        tile = SHEETS.read_thumbnail(path, (40, 40))
        self.assertEqual(tile.getpixel((1, 20)), SHEETS.TILE_BACKGROUND)
        self.assertGreater(tile.getpixel((20, 1))[0], 240)

    def test_pages_include_full_unicode_labels_and_preserve_sources(self):
        for name in ("角色2.png", "角色10.png", "很长的角色姓名和服装标记.png"):
            self.put_image(name)
        before = {p.name: p.read_bytes() for p in self.dataset.iterdir()}
        drawn = []
        original = ImageDraw.ImageDraw.text

        def record(draw, xy, text, *args, **kwargs):
            drawn.append(text)
            return original(draw, xy, text, *args, **kwargs)

        with mock.patch.object(ImageDraw.ImageDraw, "text", record):
            outputs = SHEETS.make_contact_sheets(
                self.dataset,
                self.output,
                per_sheet=2,
                columns=2,
                thumb_width=120,
                thumb_height=140,
                image_format="png",
            )
        self.assertEqual(len(outputs), 2)
        self.assertEqual(
            before, {p.name: p.read_bytes() for p in self.dataset.iterdir()}
        )
        rendered = "".join(drawn)
        for name in before:
            self.assertIn(name, rendered)
        for output in outputs:
            with Image.open(output) as sheet:
                sheet.verify()

    def test_existing_review_cannot_be_overwritten(self):
        self.put_image()
        outputs = SHEETS.make_contact_sheets(self.dataset, self.output)
        original = outputs[0].read_bytes()
        with self.assertRaisesRegex(ValueError, "new or empty"):
            SHEETS.make_contact_sheets(self.dataset, self.output)
        self.assertEqual(outputs[0].read_bytes(), original)

    def test_output_cannot_contaminate_dataset(self):
        self.put_image()
        for output in (self.dataset, self.dataset / "sheets"):
            with (
                self.subTest(output=output),
                self.assertRaisesRegex(ValueError, "outside"),
            ):
                SHEETS.make_contact_sheets(self.dataset, output)

    def test_corrupt_image_fails_before_any_output(self):
        self.put_image()
        (self.dataset / "broken.png").write_bytes(b"not an image")
        with self.assertRaisesRegex(OSError, "broken.png"):
            SHEETS.make_contact_sheets(self.dataset, self.output)
        self.assertFalse(self.output.exists())

    def test_invalid_counts_empty_dataset_and_missing_font(self):
        with self.assertRaisesRegex(ValueError, "No supported"):
            SHEETS.make_contact_sheets(self.dataset, self.output)
        self.put_image()
        with self.assertRaisesRegex(ValueError, "positive"):
            SHEETS.make_contact_sheets(self.dataset, self.output, columns=0)
        with self.assertRaisesRegex(ValueError, "Font does not exist"):
            SHEETS.make_contact_sheets(
                self.dataset, self.output, font_path=self.root / "missing.ttf"
            )

    def test_nested_images_do_not_get_silently_omitted(self):
        self.put_image()
        (self.dataset / "nested").mkdir()
        self.put_image("nested/other.png")
        with self.assertRaisesRegex(ValueError, "Nested"):
            SHEETS.make_contact_sheets(self.dataset, self.output)

    def test_cli_exit_status_and_missing_pillow_message(self):
        self.put_image()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(SHEETS.main([str(self.dataset), str(self.output)]), 0)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(SHEETS.main([str(self.dataset), str(self.output)]), 2)
        self.assertIn("new or empty", stderr.getvalue())
        with (
            mock.patch.dict("sys.modules", {"PIL": None}),
            self.assertRaisesRegex(ImportError, "uv run"),
        ):
            SHEETS.pillow_modules()


if __name__ == "__main__":
    unittest.main()
