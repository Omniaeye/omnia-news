# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Commit identity is preserved; only known bookkeeping formats are suppressible."""
import re

TRAILER = re.compile(r'^(Signed-off-by|Co-authored-by|Copilot-Session|fbshipit-source-id|PiperOrigin-RevId|Reviewed By|Reviewed-by|Differential Revision):', re.I)
HASH_ONLY = re.compile(r'[a-fA-F0-9]{7,64}(?:[\s,;]+[a-fA-F0-9]{7,64})*')
PATTERNS = (
    r'ci: (?:acquire|claim|release) gh-pages publication turn',
    r'Deploy [a-fA-F0-9]{7,40} to GitHub Pages',
    r'(?:Update|Regenerate) (?:coverage(?: report| badge)?|generated status|build records)',
    r'add [^\n]+ \(benchmarkdotnet\) benchmark result for [a-fA-F0-9]{40}',
    r'Visual evidence: pr/\d+/visual/[a-fA-F0-9]{40}/\d+/\d+',
    r'(?:Deploy|Remove) Storybook preview for PR #\d+',
    r'Cleaning up docs preview for PR #\d+\.?',
    r"Merge (?:remote-tracking )?branch '[^'\n]+' into [^\n]+",
)


def message(value):
    # Only a final paragraph made entirely of known trailers is removable.
    # A subject, example in the body, or ambiguous/mixed block is preserved.
    lines = value.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    start = len(lines)
    while start and lines[start - 1].strip():
        start -= 1
    block = lines[start:]
    if start > 0 and any(line.strip() for line in lines[:start]) and block and all(TRAILER.match(line) for line in block):
        lines = lines[:start]
    return '\n'.join(lines).strip()


def literal_reason(value):
    if not value:
        return 'empty_message'
    return 'hash_only' if HASH_ONLY.fullmatch(value) else None


def operational_record(value):
    return '\n' not in value and any(re.fullmatch(pattern, value, re.I) for pattern in PATTERNS)
