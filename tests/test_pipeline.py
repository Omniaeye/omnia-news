from pathlib import Path
import tempfile
import unittest
from helpers import Backend, event
from omnia_news.pipeline import process
from omnia_news._engine.ledger import DecisionLedger


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.ledger = DecisionLedger(Path(self.folder.name) / 'decisions.db')

    def tearDown(self):
        self.ledger.close()
        self.folder.cleanup()

    def test_informative_commit_and_replay(self):
        backend = Backend()
        item = event()
        first = process(item, self.ledger, backend)
        second = process(item, self.ledger, backend)
        self.assertEqual(first['action'], 'keep')
        self.assertTrue(first['preserve_archive'])
        self.assertTrue(second['decision']['cache_hit'])
        self.assertEqual(backend.calls, 1)

    def test_suppression_requires_literal_or_operational_evidence(self):
        backend = Backend('noise')
        self.assertEqual(process(event('Fix a small typo in documentation'), self.ledger, backend)['action'], 'review')
        self.assertEqual(process(event('Update coverage report'), self.ledger, backend)['action'], 'suppress')

    def test_literal_noise_does_not_load_model(self):
        backend = Backend()
        for value in ('', 'a' * 40):
            result = process(event(value), self.ledger, backend)
            self.assertEqual(result['action'], 'suppress')
            self.assertEqual(result['decision']['engine']['backend'], 'literal_format')
        self.assertEqual(backend.calls, 0)

    def test_low_probability_is_review(self):
        result = process(event(), self.ledger, Backend(chance=.6))
        self.assertEqual(result['action'], 'review')

    def test_quotes_stay_separate_and_cannot_trigger_literal_suppression(self):
        item = event('a' * 40)
        item['context'] = [{'id': 'other', 'relation': 'quote', 'author': 'other',
                            'text': 'A useful explanation', 'url': 'https://example.com/context'}]
        backend = Backend()
        result = process(item, self.ledger, backend)
        self.assertEqual(backend.calls, 1)
        self.assertNotIn('A useful explanation', backend.inputs[0]['primary_text'])
        self.assertEqual(result['decision']['evidence'][-1], 'https://example.com/context')

    def test_failure_is_not_a_suppression(self):
        backend = Backend()
        backend.choice = 'invalid'
        with self.assertRaises(Exception):
            process(event(), self.ledger, backend)
        self.assertEqual(self.ledger.db.execute('SELECT COUNT(*) FROM decisions').fetchone()[0], 0)
