#!/usr/bin/env python3
"""Initialize a project or audit its inventory, without overwriting user files.

Python 3.9+; standard library only. Visual review and image decoding are separate gates.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
MANAGEMENT = "00_项目管理"
DIRECTORIES = [
    MANAGEMENT, "01_原始素材", "02_设计候选", "03_训练候选", "04_正式训练集",
    "05_淘汰区", "06_正则集", "07_导出/Anima", "07_导出/Krea2",
    "07_导出/正则复用包", "08_测试样图", "08_丹炉导入", "09_训练产物", "outputs",
]
TEMPLATES = {
    "project-state.template.md": f"{MANAGEMENT}/项目状态.md",
    "character-profile.template.yaml": f"{MANAGEMENT}/角色配置.yaml",
    "task_plan.template.md": "task_plan.md",
    "findings.template.md": "findings.md",
    "progress.template.md": "progress.md",
    "inventory.template.csv": f"{MANAGEMENT}/图片清单.csv",
    "batches.template.csv": f"{MANAGEMENT}/生成批次.csv",
    "coverage.template.csv": f"{MANAGEMENT}/覆盖矩阵.csv",
    "runs.template.csv": f"{MANAGEMENT}/训练记录.csv",
}
TRAIN_CATEGORIES = {"training_candidate", "formal", "rejected"}
STATUSES = {"candidate", "needs_review", "needs_repair", "approved", "rejected", "superseded"}
CAPTION_STATUSES = {"pending", "draft", "reviewed", "not_applicable"}
HUB_STATUSES = {"not_requested", "pending", "approved", "changes_requested"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def initialize(root: Path, character_id: str, display_name: str, trigger: str) -> list[str]:
    for value in (character_id, trigger):
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value):
            raise ValueError("Character ID and trigger must be lowercase ASCII identifiers")
    if any(c in display_name for c in "\r\n"):
        raise ValueError("Display name must be a single line")
    replacements = {
        "CHARACTER_ID": character_id, "DISPLAY_NAME": display_name, "TRIGGER": trigger,
        "ROOT": str(root), "TIMESTAMP": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    # Render everything before writing; JSON string escaping is valid in double-quoted YAML.
    rendered = {}
    for template, destination in TEMPLATES.items():
        content = (ASSETS / template).read_text(encoding="utf-8-sig")
        for key, value in replacements.items():
            if template.endswith(".yaml"):
                value = json.dumps(value, ensure_ascii=False)[1:-1]
            content = content.replace("{{" + key + "}}", value)
        rendered[destination] = content
    for directory in DIRECTORIES:
        (root / directory).mkdir(parents=True, exist_ok=True)
    actions = []
    for relative, content in rendered.items():
        path = root / relative
        try:
            with path.open("x", encoding="utf-8", newline="") as handle:
                handle.write(content)
            actions.append(f"CREATE {relative}")
        except FileExistsError:
            actions.append(f"KEEP {relative}")
    return actions


def project_file(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute() or "\\" in relative:
        raise ValueError(f"Expected project-relative POSIX path: {relative!r}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path leaves project: {relative!r}")
    if not path.is_file():
        raise ValueError(f"Missing file: {relative}")
    return path


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def audit(root: Path, families: list[str], ready: bool, trigger: str, require_hub: bool = False) -> dict:
    errors, warnings = [], []
    inventory = root / MANAGEMENT / "图片清单.csv"
    with inventory.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = set(next(csv.reader((ASSETS / "inventory.template.csv").read_text().splitlines())))
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError("Legacy/incomplete inventory; migrate a copy first. Missing: " + ", ".join(sorted(missing)))
        rows = list(reader)
    lookup = {}
    for filename, key in (("生成批次.csv", "batch_id"), ("覆盖矩阵.csv", "cell_id")):
        with (root / MANAGEMENT / filename).open(encoding="utf-8-sig", newline="") as handle:
            table = csv.DictReader(handle)
            if key not in (table.fieldnames or []) or "pack" not in (table.fieldnames or []):
                raise ValueError(f"Invalid ledger header: {filename}")
            lookup[key] = {}
            for item in table:
                if not item[key] or item[key] in lookup[key]:
                    errors.append(f"{filename}: empty/duplicate {key}")
                lookup[key][item[key]] = item["pack"]
    ids, paths, approved_hashes = set(), set(), {}
    generated_hashes = set()
    states, by_pack, coverage, captions = Counter(), {}, Counter(), Counter()
    for index, row in enumerate(rows, 2):
        image_id = row.get("image_id", "")
        label = image_id or f"row {index}"
        if None in row or any(value is None for value in row.values()):
            errors.append(f"{label}: malformed CSV row")
            continue
        if not image_id or image_id in ids:
            errors.append(f"{label}: missing/duplicate image_id")
        ids.add(image_id)
        category, status, pack = row["category"], row["status"], row["pack"]
        for dimension in ("image", "anima", "krea2"):
            hub_status = row[f"hub_{dimension}_review_status"]
            if hub_status not in HUB_STATUSES:
                errors.append(f"{label}: unknown Hub {dimension} review status")
        if row["review_source"] not in {"", "plugin", "hub", "user"}:
            errors.append(f"{label}: unknown review_source")
        for field, key in (("batch_id", "batch_id"), ("coverage_cell_id", "cell_id")):
            value = row[field]
            if value and (value not in lookup[key] or lookup[key][value] != pack):
                errors.append(f"{label}: unknown or mismatched {field}")
        if status not in STATUSES:
            errors.append(f"{label}: unknown status {status!r}")
        if category not in TRAIN_CATEGORIES | {"source", "design", "regularization", "evaluation"}:
            errors.append(f"{label}: unknown category {category!r}")
        if row["source_kind"] not in {"source", "generated", "derived"}:
            errors.append(f"{label}: unknown source_kind")
        if category in TRAIN_CATEGORIES and not pack:
            errors.append(f"{label}: missing pack")
        if category == "formal" and status != "approved":
            errors.append(f"{label}: formal image must be approved")
        if category == "rejected" and status != "rejected":
            errors.append(f"{label}: rejected category must have rejected status")
        if status == "rejected" and not row["reject_reason"]:
            errors.append(f"{label}: missing rejection reason")
        states[status] += 1
        if category in TRAIN_CATEGORIES:
            by_pack.setdefault(pack, Counter())[status] += 1
        try:
            path = project_file(root, row["file"])
            if path.suffix.lower() not in IMAGE_SUFFIXES:
                raise ValueError(f"Unsupported image extension: {row['file']}")
            if path in paths:
                errors.append(f"{label}: image file registered more than once")
            paths.add(path)
            actual_hash = digest(path)
            if row["sha256"] != actual_hash:
                errors.append(f"{label}: missing or stale SHA-256")
            if category in TRAIN_CATEGORIES and row["source_kind"] == "generated":
                generated_hashes.add(actual_hash)
            if category in TRAIN_CATEGORIES and status == "approved":
                if not row["review_source"]:
                    errors.append(f"{label}: approved image missing review_source")
                if row["hub_image_review_status"] == "changes_requested":
                    errors.append(f"{label}: approved image has unresolved Hub changes")
                if ready and require_hub and row["hub_image_review_status"] != "approved":
                    errors.append(f"{label}: Hub image review not approved")
                if actual_hash in approved_hashes:
                    errors.append(f"{label}: duplicates approved image {approved_hashes[actual_hash]}")
                approved_hashes[actual_hash] = label
                if row["coverage_cell_id"]:
                    coverage[row["coverage_cell_id"]] += 1
            if row["source_kind"] == "generated":
                if not row["batch_id"]:
                    errors.append(f"{label}: generated image missing batch_id")
                project_file(root, row["prompt_file"])
            for reference in filter(None, row["reference_files"].split(";")):
                project_file(root, reference)
            if row["source_kind"] == "derived" and not row["parent_id"]:
                errors.append(f"{label}: derived image missing parent_id")
            for family in ("anima", "krea2"):
                caption_status = row[f"{family}_caption_status"]
                if caption_status not in CAPTION_STATUSES:
                    errors.append(f"{label}: unknown {family} caption status")
                relative = row[f"{family}_caption_file"]
                text = ""
                if relative:
                    caption_path = project_file(root, relative)
                    if caption_path.suffix != ".txt" or caption_path.stem != path.stem:
                        errors.append(f"{label}: {family} caption must be a same-stem .txt")
                    text = caption_path.read_text(encoding="utf-8-sig").strip()
                    if not text:
                        errors.append(f"{label}: empty {family} caption")
                    if trigger and not re.search(r"(?<![\w-])" + re.escape(trigger) + r"(?![\w-])", text):
                        errors.append(f"{label}: missing exact trigger in {family} caption")
                if caption_status == "reviewed" and not text:
                    errors.append(f"{label}: reviewed {family} caption has no content")
                if category in TRAIN_CATEGORIES and status == "approved":
                    captions[f"{family}:{caption_status}"] += 1
                    if ready and family in families and (caption_status != "reviewed" or not text):
                        errors.append(f"{label}: {family} caption not ready for export")
                    if ready and family in families:
                        hub_status = row[f"hub_{family}_review_status"]
                        if hub_status == "changes_requested" or (require_hub and hub_status != "approved"):
                            errors.append(f"{label}: Hub {family} review not approved")
            if row["anima_caption_file"] and row["anima_caption_file"] == row["krea2_caption_file"]:
                errors.append(f"{label}: model families cannot share one caption file")
        except (ValueError, OSError, UnicodeError) as exc:
            errors.append(f"{label}: {exc}")
    for row in rows:
        if row.get("parent_id") and (row["parent_id"] not in ids or row["parent_id"] == row.get("image_id")):
            errors.append(f"{row.get('image_id')}: missing/self parent_id")
    for directory in ("03_训练候选", "04_正式训练集", "05_淘汰区"):
        for path in (root / directory).rglob("*"):
            if path.suffix.lower() in IMAGE_SUFFIXES and path.is_file() and path.resolve() not in paths:
                warnings.append(f"Unregistered image: {path.relative_to(root)}")
    if ready and not approved_hashes:
        errors.append("No approved training images")
    if ready and warnings:
        errors.append("Resolve unregistered training images before export")
    return {
        "status": "FAIL" if errors else "PASS", "inventory_rows": len(rows),
        "generated_candidate_images_unique": len(generated_hashes),
        "approved_training_images_unique": len(approved_hashes),
        "status_counts": dict(states), "pack_counts": by_pack,
        "approved_coverage_counts": dict(coverage), "caption_counts": dict(captions),
        "errors": errors, "warnings": warnings,
        "scope": "Inventory paths, hashes, provenance fields and caption readiness only; not image decoding, visual quality, near-duplicate detection, or trainer validation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("root", type=Path)
    init.add_argument("--character-id", required=True)
    init.add_argument("--display-name", required=True)
    init.add_argument("--trigger", required=True)
    check = commands.add_parser("audit")
    check.add_argument("root", type=Path)
    check.add_argument("--family", action="append", choices=["anima", "krea2"], default=[])
    check.add_argument("--ready-for-export", action="store_true")
    check.add_argument("--require-hub-review", action="store_true")
    check.add_argument("--trigger", default="")
    args = parser.parse_args()
    try:
        root = args.root.expanduser().resolve()
        if args.command == "init":
            print("\n".join(initialize(root, args.character_id, args.display_name, args.trigger)))
            return 0
        if args.ready_for_export and (not args.family or not args.trigger):
            parser.error("--ready-for-export requires --family and --trigger")
        if args.require_hub_review and not args.ready_for_export:
            parser.error("--require-hub-review requires --ready-for-export")
        report = audit(root, args.family, args.ready_for_export, args.trigger, args.require_hub_review)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return int(report["status"] != "PASS")
    except (ValueError, OSError, csv.Error) as exc:
        parser.exit(2, f"ERROR: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
