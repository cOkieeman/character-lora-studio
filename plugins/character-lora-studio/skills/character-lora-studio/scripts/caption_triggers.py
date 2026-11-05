"""Validate cast manifests and check exact caption triggers (Python 3.9+, stdlib)."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath


def has_token(text: str, trigger: str) -> bool:
    """Match an exact, case-sensitive trigger outside word/underscore/hyphen tokens."""
    return re.search(r"(?<![\w-])" + re.escape(trigger) + r"(?![\w-])", text) is not None


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def validate_cast_manifest(data: dict) -> dict:
    """Validate a relative image path -> visible character IDs manifest.

    Character IDs identify entries; their values are exact, case-sensitive triggers.
    Paths are relative to the caller's audit root, not to the JSON file's directory.
    This validates the declaration only, not files or visually present identities.
    """
    if not isinstance(data, dict) or set(data) != {"characters", "images"}:
        raise ValueError("Cast manifest must contain exactly 'characters' and 'images' objects")
    characters, images = data["characters"], data["images"]
    if not isinstance(characters, dict) or len(characters) < 2:
        raise ValueError("Cast manifest requires at least two characters")
    if not isinstance(images, dict) or not images:
        raise ValueError("Cast manifest images must be a nonempty object")
    triggers = []
    for identity, trigger in characters.items():
        if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", identity):
            raise ValueError(f"Invalid cast character ID: {identity!r}")
        if (not isinstance(trigger, str) or not trigger.strip() or trigger != trigger.strip()
                or any(ord(char) < 32 or ord(char) == 127 for char in trigger)):
            raise ValueError(f"Invalid trigger for cast character {identity!r}")
        for other in triggers:
            if has_token(trigger, other) or has_token(other, trigger):
                raise ValueError(f"Duplicate or overlapping cast triggers: {other!r}, {trigger!r}")
        triggers.append(trigger)
    seen_paths = set()
    for relative, identities in images.items():
        if (not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative
                or PurePosixPath(relative).is_absolute() or PureWindowsPath(relative).drive
                or any(part in {"", ".", ".."} for part in relative.split("/"))
                or any(ord(char) < 32 or ord(char) == 127 for char in relative)):
            raise ValueError(f"Cast image path must be a relative POSIX path without traversal: {relative!r}")
        if relative.casefold() in seen_paths:
            raise ValueError(f"Duplicate case-insensitive cast image path: {relative!r}")
        seen_paths.add(relative.casefold())
        if not isinstance(identities, list) or not identities:
            raise ValueError(f"Cast image {relative!r} needs a nonempty character ID list")
        if any(not isinstance(identity, str) or identity not in characters for identity in identities):
            raise ValueError(f"Cast image {relative!r} has an unknown character ID")
        if len(identities) != len(set(identities)):
            raise ValueError(f"Cast image {relative!r} has duplicate character IDs")
    return data


def load_cast_manifest(path: Path) -> dict:
    """Load UTF-8 JSON without allowing duplicate object keys, then validate it."""
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=_unique_object)
    return validate_cast_manifest(data)


def check_caption_triggers(text: str, expected: list[str], forbidden: list[str]) -> list[str]:
    """Return missing expected and unexpected forbidden trigger errors.

    A trigger does not match inside a longer word, underscore token, or hyphen token.
    Repetition is allowed: a multi-character sentence can refer to one identity twice.
    """
    if any(not isinstance(trigger, str) or not trigger.strip() for trigger in expected + forbidden):
        raise ValueError("Caption triggers must be nonempty strings")
    errors = [f"missing exact trigger: {trigger!r}" for trigger in expected if not has_token(text, trigger)]
    errors.extend(f"unexpected cast trigger: {trigger!r}" for trigger in forbidden if has_token(text, trigger))
    return errors
