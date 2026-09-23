# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Commit identity is preserved; only known bookkeeping formats are suppressible."""
import re

TRAILER = re.compile(r'^(Signed-off-by|Co-authored-by|Copilot-Session|fbshipit-source-id|PiperOrigin-RevId|Reviewed By|Differential Revision):', re.I)
HASH_ONLY = re.compile(r'[a-fA-F0-9]{7,64}(?:[\s,;]+[a-fA-F0-9]{7,64})*')
PATTERNS = (
    r'ci: (?:acquire|release) gh-pages publication turn',
    r'Deploy [a-fA-F0-9]{7,40} to GitHub Pages',
    r'(?:Update|Regenerate) (?:coverage(?: report| badge)?|generated status|build records)(?: \[[^\]]+\])?',
)


def message(value):
    return '\n'.join(line for line in value.splitlines() if not TRAILER.match(line.strip())).strip()


def literal_reason(value):
    if not value:
        return 'empty_message'
    return 'hash_only' if HASH_ONLY.fullmatch(value) else None


def operational_record(value):
    return '\n' not in value and any(re.fullmatch(pattern, value, re.I) for pattern in PATTERNS)
