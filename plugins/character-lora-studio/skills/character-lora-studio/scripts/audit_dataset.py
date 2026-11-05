#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pillow"]
# ///
"""Read-only audit of one flat image-caption export, including per-image cast triggers.

Run with ``uv run audit_dataset.py DATASET --trigger TOKEN``. PASS only covers
mechanical checks; anatomy, identity fidelity and caption facts need visual review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from caption_triggers import has_token
from caption_triggers import load_cast_manifest as load_shared_cast_manifest

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def pillow_modules():
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required: run this script with uv run to install its declared dependency."
        ) from exc
    return Image, ImageOps


def load_cast_manifest(path: Path) -> dict:
    data = load_shared_cast_manifest(path)
    for name in data["images"]:
        parsed = PurePosixPath(name)
        if (
            not name
            or len(parsed.parts) != 1
            or parsed.name != name
            or "\\" in name
            or ":" in name
            or parsed.suffix.lower() not in IMAGE_EXTENSIONS
        ):
            raise ValueError(
                f"Cast image key must be a flat relative image filename: {name!r}"
            )
    return data


def audit_dataset(
    dataset: Path,
    *,
    triggers=None,
    cast_manifest=None,
    outfit_tokens=None,
    outfit_regex=None,
    expected_per_outfit=None,
    min_width=512,
    min_height=512,
    strict=False,
) -> dict:
    Image, ImageOps = pillow_modules()
    dataset = Path(dataset).expanduser().resolve()
    if not dataset.is_dir():
        raise ValueError(f"Dataset directory does not exist: {dataset}")
    triggers, outfit_tokens = list(triggers or []), list(outfit_tokens or [])
    if bool(triggers) == bool(cast_manifest):
        raise ValueError("Supply either triggers or a cast manifest")
    if any(
        not value.strip() or value != value.strip()
        for value in triggers + outfit_tokens
    ):
        raise ValueError(
            "Triggers and outfit tokens must be non-empty, without surrounding whitespace"
        )
    if min_width <= 0 or min_height <= 0:
        raise ValueError("Minimum width and height must be positive")
    if expected_per_outfit is not None and (
        expected_per_outfit < 0 or not outfit_tokens
    ):
        raise ValueError(
            "Expected outfit counts require explicit --outfit-token values and a nonnegative count"
        )
    pattern = re.compile(outfit_regex) if outfit_regex else None
    cast = load_cast_manifest(Path(cast_manifest)) if cast_manifest else None
    errors, warnings = [], []
    image_groups, caption_groups = defaultdict(list), defaultdict(list)
    nested, unsupported = [], []
    for path in sorted(dataset.iterdir()):
        if path.is_dir():
            nested.append(path.name)
            continue
        if path.is_symlink():
            errors.append(f"Symbolic link is not an export file: {path.name}")
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            image_groups[path.stem.casefold()].append(path)
        elif path.suffix.lower() == ".txt":
            caption_groups[path.stem.casefold()].append(path)
        else:
            unsupported.append(path.name)
    images = [p for paths in image_groups.values() for p in paths]
    captions = [p for paths in caption_groups.values() for p in paths]
    duplicate_stems = {
        stem: [p.name for p in paths]
        for stem, paths in image_groups.items()
        if len(paths) > 1
    }
    duplicate_caption_stems = {
        stem: [p.name for p in paths]
        for stem, paths in caption_groups.items()
        if len(paths) > 1
    }
    missing_captions = [
        p.name
        for stem, paths in image_groups.items()
        if stem not in caption_groups
        for p in paths
    ]
    missing_images = [
        p.name
        for stem, paths in caption_groups.items()
        if stem not in image_groups
        for p in paths
    ]
    case_mismatches, paired_images = {}, {}
    for stem, paths in image_groups.items():
        matching_captions = caption_groups.get(stem, [])
        if len(paths) != 1 or len(matching_captions) != 1:
            continue
        image, caption = paths[0], matching_captions[0]
        if caption.stem != image.stem or caption.suffix != ".txt":
            case_mismatches[image.name] = caption.name
        else:
            paired_images[caption.name] = image
    if not images:
        errors.append("Dataset contains no supported images")
    if nested:
        errors.append("Flat export required; nested directories were not audited")
    if duplicate_stems:
        errors.append("Duplicate image stems (case-insensitive)")
    if duplicate_caption_stems:
        errors.append("Duplicate caption stems (case-insensitive)")
    if missing_captions:
        errors.append("Images without captions")
    if missing_images:
        errors.append("Captions without images")
    if case_mismatches:
        errors.append(
            "Caption filenames must match image stem case exactly and use lowercase .txt"
        )
    if unsupported:
        warnings.append("Unsupported files are not part of the image-caption audit")
    cast_missing, cast_stale = [], []
    if cast:
        actual_names = {p.name for p in images}
        cast_missing = sorted(actual_names - set(cast["images"]))
        cast_stale = sorted(set(cast["images"]) - actual_names)
        if cast_missing or cast_stale:
            errors.append(
                "Cast manifest does not exactly cover image filenames (case-sensitive)"
            )

    empty_captions, unreadable_captions = [], []
    missing_triggers, absent_character_triggers = {}, {}
    normalized = defaultdict(list)
    outfit_counts = Counter({token: 0 for token in outfit_tokens})
    token_counts = Counter(
        {token: 0 for token in (cast["characters"].values() if cast else triggers)}
    )
    paired_count = len(paired_images)
    for path in captions:
        try:
            text = path.read_text(encoding="utf-8-sig").strip()
        except (OSError, UnicodeError):
            unreadable_captions.append(path.name)
            continue
        if not text:
            empty_captions.append(path.name)
            continue
        normalized[" ".join(text.casefold().split())].append(path.name)
        for token in token_counts:
            token_counts[token] += int(has_token(text, token))
        found_outfits = {token for token in outfit_tokens if has_token(text, token)}
        if pattern:
            found_outfits.update(
                match.group(0) for match in pattern.finditer(text) if match.group(0)
            )
        outfit_counts.update(found_outfits)
        if path.name not in paired_images:
            continue
        image_name = paired_images[path.name].name
        expected = triggers
        if cast:
            identities = cast["images"].get(image_name)
            if identities is None:
                continue
            expected = [cast["characters"][identity] for identity in identities]
            absent = [
                token
                for identity, token in cast["characters"].items()
                if identity not in identities and has_token(text, token)
            ]
            if absent:
                absent_character_triggers[path.name] = absent
        missing = [token for token in expected if not has_token(text, token)]
        if missing:
            missing_triggers[path.name] = missing
    if empty_captions:
        errors.append("Empty captions")
    if unreadable_captions:
        errors.append("Unreadable or non-UTF-8 captions")
    if missing_triggers:
        errors.append("Missing exact required triggers")
    if absent_character_triggers:
        errors.append(
            "Captions mention characters absent according to the cast manifest"
        )
    duplicate_captions = [names for names in normalized.values() if len(names) > 1]
    if duplicate_captions:
        warnings.append("Duplicate normalized captions need per-image review")
    unreadable_images, undersized_images, image_hashes = [], {}, defaultdict(list)
    dimensions = {}
    for path in images:
        try:
            checksum = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    checksum.update(chunk)
            image_hashes[checksum.hexdigest()].append(path.name)
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                image.load()
                oriented = ImageOps.exif_transpose(image)
                width, height = oriented.size
            dimensions[path.name] = [width, height]
            if width < min_width or height < min_height:
                undersized_images[path.name] = [width, height]
        except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):
            unreadable_images.append(path.name)
    duplicate_images = [names for names in image_hashes.values() if len(names) > 1]
    if unreadable_images:
        errors.append("Undecodable or invalid images")
    if undersized_images:
        errors.append("Images below the configured minimum dimensions")
    if duplicate_images:
        errors.append("Duplicate image file hashes")
    count_mismatches = {
        token: outfit_counts[token]
        for token in outfit_tokens
        if expected_per_outfit is not None
        and outfit_counts[token] != expected_per_outfit
    }
    if count_mismatches:
        errors.append("Explicit outfit counts do not meet the requested target")
    if strict and warnings:
        errors.append("Strict mode treats audit warnings as failures")
    return {
        "dataset": str(dataset),
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "warnings": warnings,
        "image_count": len(images),
        "caption_count": len(captions),
        "paired_count": paired_count,
        "trigger_counts": dict(token_counts),
        "outfit_counts": dict(sorted(outfit_counts.items())),
        "duplicate_stems": duplicate_stems,
        "duplicate_caption_stems": duplicate_caption_stems,
        "missing_captions": missing_captions,
        "missing_images": missing_images,
        "case_mismatches": case_mismatches,
        "empty_captions": empty_captions,
        "unreadable_captions": unreadable_captions,
        "missing_triggers": missing_triggers,
        "absent_character_triggers": absent_character_triggers,
        "cast_missing_images": cast_missing,
        "cast_stale_images": cast_stale,
        "duplicate_captions": duplicate_captions,
        "duplicate_images": duplicate_images,
        "unreadable_images": unreadable_images,
        "undersized_images": undersized_images,
        "dimensions": dimensions,
        "dimensions_checked": True,
        "count_mismatches": count_mismatches,
        "nested_directories": nested,
        "unsupported_files": unsupported,
        "scope": "Flat export files, decodability, oriented dimensions, exact hashes and caption tokens; not visual correctness or perceptual duplicates.",
    }


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--trigger",
        action="append",
        help="Exact trigger required in every caption; repeat for combined concepts",
    )
    mode.add_argument(
        "--cast-manifest",
        type=Path,
        help="JSON characters/images mapping for per-image trigger presence",
    )
    parser.add_argument("--outfit-token", action="append", default=[])
    parser.add_argument(
        "--outfit-regex",
        help="Optional legacy outfit regex; counts full matches, no project-specific default",
    )
    parser.add_argument(
        "--expected-per-outfit",
        type=int,
        help="Target for every explicit outfit token, including currently absent tokens",
    )
    parser.add_argument("--min-width", type=positive_int, default=512)
    parser.add_argument("--min-height", type=positive_int, default=512)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail on warnings such as duplicate captions",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="New report outside the dataset; refuses existing paths",
    )
    args = parser.parse_args(argv)
    try:
        output = args.json_output.expanduser().resolve() if args.json_output else None
        dataset = args.dataset.expanduser().resolve()
        if output and (
            output == dataset or dataset in output.parents or output.exists()
        ):
            raise ValueError("JSON output must be a new file outside the dataset")
        report = audit_dataset(
            dataset,
            triggers=args.trigger,
            cast_manifest=args.cast_manifest,
            outfit_tokens=args.outfit_token,
            outfit_regex=args.outfit_regex,
            expected_per_outfit=args.expected_per_outfit,
            min_width=args.min_width,
            min_height=args.min_height,
            strict=args.strict,
        )
        rendered = json.dumps(report, ensure_ascii=False, indent=2)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8") as handle:
                handle.write(rendered + "\n")
        print(rendered)
        return 0 if report["status"] == "PASS" else 1
    except (OSError, UnicodeError, ValueError, RuntimeError, re.error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
