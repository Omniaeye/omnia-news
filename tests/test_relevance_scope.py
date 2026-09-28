# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from helpers import event, TypedBackend
from omnia_news._engine.ledger import DecisionLedger
from omnia_news.assessment_tasks import catalog
from omnia_news.casebook import validate_result
from omnia_news.intelligence import assess
from omnia_news.trading_context import for_token


class RecordingBackend(TypedBackend):
    def __init__(self):
        super().__init__()
        self.requests = []

    def __call__(self, state, questions):
        self.requests.append((deepcopy(state), deepcopy(questions)))
        return super().__call__(state, questions)


class RelevanceScopeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.ledger = DecisionLedger(Path(self.folder.name) / 'cache.db')
        self.addCleanup(self.ledger.close)
        self.backend = RecordingBackend()

    def test_quotes_never_enter_relevance_input_and_context_edits_reuse_it(self):
        item = event('Thanks', 'x')
        item['url'] = 'https://x.com/example/status/123'
        item['context'] = [{'id': 'q', 'relation': 'quote', 'author': 'other',
                            'text': 'A new product launched', 'url': 'https://x.com/other/status/124'}]
        first = assess(item, self.ledger, self.backend)
        self.assertEqual(self.backend.requests[0][0], {'text': 'Thanks'})
        self.assertEqual(list(self.backend.requests[0][1]), ['relevance'])
        self.assertIn('context', self.backend.requests[1][0])
        item['context'][0]['text'] = 'A different announcement'
        second = assess(item, self.ledger, self.backend)
        self.assertEqual(self.backend.calls, 3)
        self.assertEqual(first['inference'][0]['decision_id'], second['inference'][0]['decision_id'])
        validate_result(second)

    def legacy(self, item):
        result = assess(item, self.ledger, self.backend)
        questions = catalog('omnia.news.intelligence.v1')
        call = self.ledger.decide({'id': 'legacy', 'state': {'text': item['text']}, 'questions': questions,
                                  'evidence': [item['url']]}, self.backend,
                                 manifest={'backend': 'controlled_contract_test', 'task_version': 'omnia.news.intelligence.v1'},
                                 min_probability=0)
        result.pop('assessment_id')
        result['schema'] = 'omnia.news.intelligence.v1'
        result['inference'] = [call]
        for name, task in result['tasks'].items():
            task['answer'] = call['answers'][name]
        return self.ledger.record_assessment(result)

    def test_refresh_reuses_unchanged_tasks_and_keeps_original_receipt(self):
        item = event()
        prior = self.legacy(item)
        before = deepcopy(prior)
        result = assess(item, self.ledger, self.backend, prior_assessment=prior)
        validate_result(result)
        self.assertEqual(prior, before)
        inherited = result['inference'][1]
        self.assertEqual(inherited['answers'], prior['inference'][0]['answers'])
        self.assertEqual(inherited['decision_id'], prior['inference'][0]['decision_id'])
        self.assertEqual(inherited['reused_from'], prior['assessment_id'])
        self.assertEqual(result['tasks']['event']['answer'], prior['tasks']['event']['answer'])

    def test_refresh_rejects_edited_sources_or_receipts_before_calling_model(self):
        item = event()
        prior = self.legacy(item)
        before = self.backend.calls
        with self.assertRaisesRegex(ValueError, 'prior_source_mismatch'):
            assess({**item, 'text': 'Edited source'}, self.ledger, self.backend, prior_assessment=prior)
        prior['author'] = 'altered'
        with self.assertRaisesRegex(ValueError, 'prior_assessment_hash_mismatch'):
            assess(item, self.ledger, self.backend, prior_assessment=prior)
        self.assertEqual(self.backend.calls, before)

    def test_context_call_cannot_be_relabelled_as_primary_only(self):
        result = assess(event(), self.ledger, self.backend)
        result['inference'][1]['scope'] = 'primary_text'
        with self.assertRaisesRegex(ValueError, 'inference_scope_coverage_mismatch'):
            validate_result(result)

    def test_missing_or_duplicated_input_segments_are_rejected(self):
        result = assess(event(), self.ledger, self.backend)
        duplicated = deepcopy(result)
        duplicated['inference'].append(deepcopy(duplicated['inference'][0]))
        with self.assertRaisesRegex(ValueError, 'inference_segment_count_mismatch'):
            validate_result(duplicated)
        result['inference'][0]['segment'] = 2
        with self.assertRaisesRegex(ValueError, 'inference_segment_coverage_mismatch'):
            validate_result(result)

    def test_operational_record_does_not_export_accepted_trading_tasks(self):
        item = event('Deploy Storybook preview for PR #7')
        result = assess(item, self.ledger, self.backend)
        self.assertEqual(result['feed_decision']['action'], 'suppress')
        context = for_token(self.ledger, {'chain': 'bsc', 'network_id': '56', 'contract': '0x' + '1' * 40},
                            [{'platform': item['platform'], 'url': item['url']}])
        self.assertEqual(context['signals'][0]['tasks'], {})
        self.assertEqual(context['signals'][0]['status'], 'feed_policy_review')
