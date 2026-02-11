#!/usr/bin/env python3
"""Safety checks for public landing content."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = [
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgho_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\bapi[_-]?key\s*[:=]\s*[A-Za-z0-9_\-]{8,}"),
]

RESTRICTED_TERMS = [
    "internal-only",
    "confidential",
    "restricted",
    "private runbook",
    "incident response",
]


def main() -> int:
    index_html = REPO_ROOT / "index.html"
    if not index_html.exists():
        print("index.html is required")
        return 1

    text = index_html.read_text(encoding="utf-8")
    errors: list[str] = []

    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"index.html: matched secret pattern {pattern.pattern}")
            break

    for term in RESTRICTED_TERMS:
        if term in text.lower():
            errors.append(f"index.html: matched restricted term '{term}'")
            break

    if errors:
        print("Public content checks failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Public content checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
