# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
import unittest
from helpers import event
from omnia_news.contracts import normalize
from omnia_news.github import message, operational_record


class ContractTests(unittest.TestCase):
    def test_identity_and_case(self):
        item = event()
        result = normalize(item)
        self.assertEqual(result['commit_sha'], 'a' * 40)
        self.assertNotIn('commit_sha', item)

    def test_unknown_keys_and_missing_identity(self):
        for key, value in (('url', 'https://github.com/p/r/commit/abcdef'), ('platform', 'unknown'), ('extra', True)):
            item = event()
            item[key] = value
            with self.assertRaises(ValueError):
                normalize(item)

    def test_private_credentials_in_url_are_rejected(self):
        item = event(platform='news')
        item['url'] = 'https://user:secret@example.com/story'
        with self.assertRaises(ValueError):
            normalize(item)

    def test_naive_time_and_byte_limit(self):
        item = event()
        item['observed_at'] = '2026-09-25T12:00:00'
        with self.assertRaises(ValueError):
            normalize(item)
        with self.assertRaises(ValueError):
            normalize(event(), 10)

    def test_context_keeps_separate_author(self):
        item = event(platform='x')
        item['context'] = [{'id': 'parent', 'relation': 'quote', 'author': 'another-author',
                            'text': 'Original claim', 'url': 'https://example.com/post'}]
        self.assertEqual(normalize(item)['context'][0]['author'], 'another-author')
        item['context'][0]['id'] = item['id']
        with self.assertRaises(ValueError):
            normalize(item)

    def test_multilingual_and_hash_in_useful_description(self):
        self.assertEqual(normalize(event('修复重试逻辑 abcdef1'))['text'], '修复重试逻辑 abcdef1')
        self.assertFalse(operational_record('Fix regression abcdef1'))

    def test_trailers_are_removed_without_truncation(self):
        value = 'Fix timeout\n\n' + 'details ' * 500 + '\n\nSigned-off-by: Example'
        self.assertIn('details ' * 400, message(value))
        self.assertNotIn('Signed-off-by:', message(value))

    def test_bookkeeping_match_is_narrow(self):
        self.assertTrue(operational_record('Update coverage report'))
        self.assertFalse(operational_record('Update coverage report to fix incorrect branch attribution'))
