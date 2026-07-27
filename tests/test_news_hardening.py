# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Deterministic regressions and controlled-backend contracts, not model benchmarks."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from helpers import Backend, event
from omnia_news.catalog import FIELDS, model_metadata, parameter_catalog
from omnia_news.config import Config
from omnia_news.contracts import normalize
from omnia_news.github import message, operational_record
from omnia_news.pipeline import process
from omnia_news.policy import NewsPolicy
from omnia_news._engine.ledger import DecisionLedger, digest


class NewsHardeningTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.ledger = DecisionLedger(Path(self.folder.name) / 'decisions.db')

    def tearDown(self):
        self.ledger.close()
        self.folder.cleanup()

    def test_only_unambiguous_final_trailer_block_is_removed(self):
        title = 'Signed-off-by: reject spoofed signoffs during release validation'
        body = 'Fix attribution\n\nSigned-off-by: example syntax\nThis is an explanation.'
        mixed = 'Fix attribution\n\nSigned-off-by: Example\nUnknown: preserve me'
        for value in (title, body, mixed):
            with self.subTest(value=value):
                self.assertEqual(message(value), value)
        self.assertEqual(message('Fix attribution\n\nSigned-off-by: Example\nCo-authored-by: Other\n'), 'Fix attribution')
        backend = Backend()
        self.assertEqual(process(event(title), self.ledger, backend)['action'], 'keep')
        self.assertEqual(backend.calls, 1)

    def test_free_form_bracket_suffix_cannot_enable_suppression(self):
        text = 'Update coverage report [security fix: reject arbitrary command injection]'
        self.assertFalse(operational_record(text))
        result = process(event(text), self.ledger, Backend('noise'))
        self.assertEqual((result['action'], result['reason']), ('review', 'unverified_noise'))
        self.assertEqual(process(event('Update coverage report'), self.ledger, Backend('noise'))['action'], 'suppress')

    def test_long_source_and_context_urls_survive_full_pipeline(self):
        item = event(platform='news')
        item['url'] = 'https://example.com/' + 'a' * 1800
        item['context'] = [{'id': 'other', 'relation': 'quote', 'author': 'other-author',
                            'text': 'Separate account', 'url': 'https://example.com/' + 'b' * 1800}]
        result = process(item, self.ledger, Backend())
        self.assertEqual(result['action'], 'keep')
        self.assertEqual(result['decision']['evidence'], [item['url'], item['context'][0]['url']])
        self.assertEqual(result['context_provenance'][0]['author'], 'other-author')

    def test_catalog_and_invalid_typed_metadata(self):
        self.assertEqual(len(parameter_catalog()['fields']), 32)
        catalog = parameter_catalog()
        catalog['fields']['title']['max_length'] = 99999
        self.assertEqual(FIELDS['title']['max_length'], 300)
        cases = [{'unknown': True}, {'source_deleted': 1}, {'commit_additions': True},
                 {'commit_deletions': -1}, {'advisory_severity': 'urgent'}, {'title': None},
                 {'tags': ['a', 'a']}, {'tags': ['a'] * 9}, {'source_updated_at': '2026-01-01'},
                 {'commit_parent_count': 1, 'commit_is_merge': True}, {'translation_language': 'en'}]
        for metadata in cases:
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                normalize(dict(event(), metadata=metadata))
        with self.assertRaises(ValueError):
            normalize(dict(event(platform='news'), metadata={'commit_additions': 1}))

    def test_metadata_fingerprints_original_and_bounds_model_context(self):
        item = dict(event(), metadata={'title': 'Private source title', 'commit_paths': ['private/file.py'],
                                      'commit_is_revert': True, 'author_verified': True})
        before = copy.deepcopy(item)
        backend = Backend()
        result = process(item, self.ledger, backend)
        self.assertEqual(item, before)
        self.assertEqual(result['original_input_sha256'], digest(before))
        self.assertEqual(backend.inputs[0]['reported_metadata'], {'commit_is_revert': True})
        self.assertNotIn('Private source title', json.dumps(result))
        self.assertNotIn('private/file.py', json.dumps(result))
        self.assertEqual(model_metadata(item['metadata']), {'commit_is_revert': True})
        changed = copy.deepcopy(item)
        changed['metadata']['author_verified'] = False
        other = process(changed, self.ledger, backend)
        self.assertNotEqual(result['normalized_source_sha256'], other['normalized_source_sha256'])

    def test_metadata_gates_skip_model_and_persist_final_assessment(self):
        for metadata, reason in (({'is_truncated': True}, 'incomplete_source_text'),
                                 ({'source_deleted': True}, 'deleted_source'),
                                 ({'record_type': 'retraction'}, 'source_retraction'),
                                 ({'content_format': 'html'}, 'html_requires_text_adapter')):
            with self.subTest(metadata=metadata):
                backend = Backend()
                result = process(dict(event(), metadata=metadata), self.ledger, backend)
                self.assertEqual((result['action'], result['reason']), ('review', reason))
                self.assertIsNone(result['decision'])
                self.assertEqual(backend.calls, 0)
                self.assertTrue(result['assessment_id'])
                self.assertTrue(result['evaluated_at'].endswith('+00:00'))

    def test_policy_controls_actual_suppression_and_age_at_observation(self):
        result = process(event('a' * 40), self.ledger, Backend(), policy=NewsPolicy(allow_literal_suppression=False))
        self.assertEqual(result['reason'], 'literal_suppression_disabled')
        result = process(event('Update coverage report'), self.ledger, Backend('noise'),
                         policy=NewsPolicy(allow_operational_suppression=False))
        self.assertEqual(result['reason'], 'operational_suppression_disabled')
        item = dict(event(), observed_at='2026-09-25T12:01:01Z', published_at='2026-09-25T12:00:00Z')
        self.assertEqual(process(item, self.ledger, Backend(), policy=NewsPolicy(max_age_seconds=60))['reason'],
                         'source_outside_age_policy')
        self.assertEqual(process(item, self.ledger, Backend(), policy=NewsPolicy(max_age_seconds=61))['action'], 'keep')
        self.assertEqual(process(item, self.ledger, Backend(), policy=NewsPolicy(allowed_languages=('en',)))['reason'],
                         'language_outside_policy')

    def test_policy_environment_and_rejection(self):
        with patch.dict(os.environ, {'OMNIA_LAYA_REVISION': 'a' * 40, 'OMNIA_NEWS_ALLOW_LITERAL_SUPPRESSION': 'false',
                                    'OMNIA_NEWS_ALLOWED_LANGUAGES': 'en,pt-BR', 'OMNIA_NEWS_MAX_AGE_SECONDS': '3600'}, clear=True):
            policy = Config.from_env().policy
            self.assertFalse(policy.allow_literal_suppression)
            self.assertEqual(policy.allowed_languages, ('en', 'pt-BR'))
            self.assertEqual(policy.max_age_seconds, 3600)
        for kwargs in ({'review_deleted': 'false'}, {'max_age_seconds': True}, {'allowed_languages': ['en']}):
            with self.assertRaises(ValueError):
                NewsPolicy(**kwargs)

    def test_failure_records_final_failed_assessment_without_provider_message(self):
        class Broken(Backend):
            def manifest(self):
                raise RuntimeError('private-provider-secret')
        captured = []
        original = self.ledger.record_assessment
        def capture(result):
            captured.append(result)
            return original(result)
        with patch.object(self.ledger, 'record_assessment', side_effect=capture):
            with self.assertRaises(RuntimeError):
                process(event(), self.ledger, Broken())
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0]['status'], 'failed')
        self.assertEqual(captured[0]['error_code'], 'RuntimeError')
        self.assertNotIn('private-provider-secret', json.dumps(captured[0]))

    def test_replay_reuses_model_but_records_new_evaluation(self):
        backend = Backend()
        item = event()
        first, second = process(item, self.ledger, backend), process(item, self.ledger, backend)
        self.assertEqual(backend.calls, 1)
        self.assertEqual(first['decision']['decision_id'], second['decision']['decision_id'])
        self.assertTrue(second['decision']['cache_hit'])
        self.assertNotEqual(first['assessment_id'], second['assessment_id'])

    def test_url_controls_and_invalid_ports_are_rejected(self):
        for url in ('https://example.com/a\nb', 'https://example.com:invalid/a', 'https://example.com:0/a'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                normalize(dict(event(platform='news'), url=url))
