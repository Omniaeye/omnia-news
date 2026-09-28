# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
import unittest

from helpers import event
from omnia_news.relevance_policy import checks, decide


class RelevancePolicyTests(unittest.TestCase):
    def task(self, choice='informative', status='accepted'):
        return {'status': status, 'answer': {'choice': choice, 'answer_probability': .99}}

    def test_generated_benchmark_receipt_cannot_be_published_by_a_confident_model(self):
        item = event('add Operations.ScriptOperations (ubuntu-latest net10.0 Release) (benchmarkdotnet) benchmark result for ' + 'a' * 40)
        result = decide(self.task(), checks(item, []))
        self.assertEqual(result['action'], 'suppress')
        self.assertEqual(result['basis'], 'exact_source_format')
        self.assertTrue(result['preserve_archive'])

    def test_actual_changes_containing_hashes_or_benchmark_words_are_preserved(self):
        for body in ['Fix benchmark result display for slow requests',
                     'Fix retry handling for ' + 'a' * 40,
                     "Merge branch 'main' into feature\n\nFix a timeout in the retry handler.",
                     'Deploy Storybook preview for PR #5\n\nFix missing previews after deploy.']:
            with self.subTest(body=body):
                self.assertEqual(decide(self.task(), checks(event(body), []))['action'], 'keep')

    def test_native_noise_cannot_suppress_free_form_text_with_asset_mentions(self):
        item = event('2027 will be a busy year for $COIN and $META', 'x')
        result = decide(self.task('noise'), checks(item, []))
        self.assertEqual(result['action'], 'review')
        self.assertEqual(result['reason'], 'unverified_noise')

    def test_incomplete_source_is_not_suppressed_as_an_exact_format(self):
        result = decide(self.task(), checks(event('a' * 40), ['incomplete_text']))
        self.assertEqual(result['action'], 'review')

    def test_short_reaction_does_not_inherit_quoted_news(self):
        result = decide(self.task(), checks(event('Interesting', 'x'), []))
        self.assertEqual(result['action'], 'review')
        self.assertFalse(result['publication_authorized'])
