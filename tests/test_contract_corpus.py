# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Versioned contract vectors verify acceptance boundaries, not model accuracy."""
import json
from pathlib import Path
import unittest
from omnia_news.contracts import normalize


class ContractCorpusTests(unittest.TestCase):
    def test_documented_input_boundaries(self):
        path = Path(__file__).with_name('cases') / 'contracts.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        self.assertTrue(rows)
        self.assertEqual(len({row['id'] for row in rows}), len(rows))
        for row in rows:
            with self.subTest(case=row['id']):
                try:
                    normalize(row['input'])
                    result = 'accept'
                except (ValueError, TypeError):
                    result = 'reject'
                self.assertEqual(result, row['expect'], row['purpose'])
