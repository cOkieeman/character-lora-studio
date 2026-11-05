#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["Pillow>=10"]
# ///
"""Create filename-labeled contact sheets for visual review of a flat image folder.

The output must be a new or empty folder outside the dataset. This tool does not
approve images or certify a dataset; inspect suspicious details at full resolution.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sys
from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
BACKGROUND = (28, 28, 32)
TILE_BACKGROUND = (240, 240, 244)


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def natural_key(path: Path) -> tuple:
    # Tagged segments never compare integers to strings, including numeric names.
    return tuple(
        (1, int(part)) if part.isdigit() else (0, part.casefold())
        for part in re.split(r"(\d+)", path.name)
    ) + ((2, path.name),)


def pillow_modules():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError as exc:
        raise ImportError(
            'Pillow is required. Run: uv run "<path>/make_contact_sheets.py" '
            '"<dataset>" "<review-output>"'
        ) from exc
    return Image, ImageDraw, ImageFont, ImageOps


def select_font(image_font, path: Path | None, size: int = 20):
    if path is not None:
        if not path.is_file():
            raise ValueError(f"Font does not exist: {path}")
        return image_font.truetype(str(path), size)
    windows = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    candidates = [
        windows / "msyh.ttc",
        windows / "simhei.ttf",
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return image_font.truetype(str(candidate), size)
    print(
        "WARNING: Using a fallback font; use --font for Chinese filename labels.",
        file=sys.stderr,
    )
    return image_font.load_default()


def wrap_label(draw, text: str, font, width: int) -> list[str]:
    lines, line = [], ""
    for char in text:
        if line and draw.textlength(line + char, font=font) > width:
            lines.append(line)
            line = char
        else:
            line += char
    lines.append(line)
    return lines


def read_thumbnail(path: Path, thumb: tuple[int, int]):
    image_api, _, _, image_ops = pillow_modules()
    try:
        with image_api.open(path) as source:
            source.verify()
        with image_api.open(path) as source:
            source.load()
            oriented = image_ops.exif_transpose(source).convert("RGBA")
            oriented.thumbnail(thumb, image_api.Resampling.LANCZOS)
            tile = image_api.new("RGB", thumb, TILE_BACKGROUND)
            position = (
                (thumb[0] - oriented.width) // 2,
                (thumb[1] - oriented.height) // 2,
            )
            tile.paste(oriented, position, oriented.getchannel("A"))
            return tile
    except Exception as exc:
        raise OSError(f"Cannot decode image {path.name}: {exc}") from exc


def make_contact_sheets(
    dataset: Path,
    output: Path,
    per_sheet: int = 15,
    columns: int = 5,
    thumb_width: int = 320,
    thumb_height: int = 480,
    image_format: str = "jpg",
    font_path: Path | None = None,
) -> list[Path]:
    image_api, image_draw, image_font, _ = pillow_modules()
    if min(per_sheet, columns, thumb_width, thumb_height) <= 0:
        raise ValueError("Sheet counts and thumbnail dimensions must be positive")
    if image_format not in {"jpg", "png"}:
        raise ValueError("Format must be jpg or png")
    dataset, output = dataset.expanduser().resolve(), output.expanduser().resolve()
    if not dataset.is_dir():
        raise ValueError(f"Dataset directory does not exist: {dataset}")
    if output == dataset or dataset in output.parents:
        raise ValueError("Output must be outside the dataset directory")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError(
            "Output must be a new or empty directory; choose a new review version"
        )
    files = sorted(
        (
            p
            for p in dataset.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ),
        key=natural_key,
    )
    if not files:
        raise ValueError(f"No supported images found directly in {dataset}")
    if any(
        p.parent != dataset
        for p in dataset.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ):
        raise ValueError("Nested images found; pass one flat image folder per review")

    font = select_font(image_font, font_path)
    draw = image_draw.Draw(image_api.new("RGB", (1, 1)))
    labels = {
        p: wrap_label(draw, p.name, font, max(1, thumb_width - 14)) for p in files
    }
    bbox = font.getbbox("Ag中文")
    line_height = max(24, bbox[3] - bbox[1] + 6)
    label_height = max(len(label) for label in labels.values()) * line_height + 16
    thumb = (thumb_width, thumb_height)
    # Validate all files before creating any output. Keep only one thumbnail in
    # memory during preflight; large datasets must not retain all decoded sources.
    for path in files:
        read_thumbnail(path, thumb).close()

    output.mkdir(parents=True, exist_ok=True)
    destinations = []
    pad = 16
    for page, start in enumerate(range(0, len(files), per_sheet), 1):
        batch = files[start : start + per_sheet]
        used_columns = min(columns, len(batch))
        rows = math.ceil(len(batch) / columns)
        sheet = image_api.new(
            "RGB",
            (
                used_columns * (thumb_width + pad) + pad,
                rows * (thumb_height + label_height + pad) + pad,
            ),
            BACKGROUND,
        )
        draw = image_draw.Draw(sheet)
        for index, path in enumerate(batch):
            x = pad + (index % columns) * (thumb_width + pad)
            y = pad + (index // columns) * (thumb_height + label_height + pad)
            tile = read_thumbnail(path, thumb)
            sheet.paste(tile, (x, y))
            tile.close()
            for line_index, label in enumerate(labels[path]):
                draw.text(
                    (x + 7, y + thumb_height + 5 + line_index * line_height),
                    label,
                    font=font,
                    fill=(245, 245, 245),
                )
        destination = output / f"contact_sheet_{page:02d}.{image_format}"
        # Even a concurrently created file must not be overwritten.
        with destination.open("xb") as handle:
            sheet.save(
                handle,
                format="JPEG" if image_format == "jpg" else "PNG",
                **({"quality": 92} if image_format == "jpg" else {}),
            )
        sheet.close()
        destinations.append(destination)
    return destinations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--per-sheet", type=positive_int, default=15)
    parser.add_argument("--columns", type=positive_int, default=5)
    parser.add_argument("--thumb-width", type=positive_int, default=320)
    parser.add_argument("--thumb-height", type=positive_int, default=480)
    parser.add_argument("--format", choices=("jpg", "png"), default="jpg")
    parser.add_argument(
        "--font", type=Path, help="TTF/TTC/OTF font for filename labels"
    )
    args = parser.parse_args(argv)
    try:
        outputs = make_contact_sheets(
            args.dataset,
            args.output,
            args.per_sheet,
            args.columns,
            args.thumb_width,
            args.thumb_height,
            args.format,
            args.font,
        )
    except (ValueError, ImportError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
