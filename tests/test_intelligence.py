# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from helpers import event, TypedBackend
from omnia_news._engine.ledger import DecisionLedger
from omnia_news.assessment_tasks import TASKS
from omnia_news.batch import load_events, run
from omnia_news.intelligence import assess, lookup
from omnia_news.identity import publication_identity
from omnia_news.trading_context import for_token


class IntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.ledger = DecisionLedger(Path(self.directory.name) / "news.db")
        self.backend = TypedBackend()

    def tearDown(self):
        self.ledger.close()
        self.directory.cleanup()

    def test_policy_changes_reuse_inference_and_gate_each_task(self):
        item = event()
        first = assess(item, self.ledger, self.backend)
        second = assess(item, self.ledger, self.backend, thresholds={"tone": 0.55})
        self.assertEqual(self.backend.calls, 1)
        self.assertEqual(first["tasks"]["tone"]["status"], "needs_review")
        self.assertEqual(first["tasks"]["relevance"]["status"], "accepted")
        self.assertEqual(second["tasks"]["tone"]["status"], "accepted")
        self.assertEqual(lookup(self.ledger, first["identity"]["key"])["assessment_id"], second["assessment_id"])

    def test_observation_clock_does_not_recompute_content(self):
        item = event()
        assess(item, self.ledger, self.backend)
        item["observed_at"] = "2026-09-28T21:00:00Z"
        assess(item, self.ledger, self.backend)
        self.assertEqual(self.backend.calls, 1)

    def test_edit_and_context_change_invalidate_cache(self):
        item = event()
        assess(item, self.ledger, self.backend)
        item["text"] += " Changed API."
        assess(item, self.ledger, self.backend)
        item["context"] = [
            {"id": "quoted", "relation": "quote", "author": "other", "text": "Launch tomorrow", "url": "https://example.com/context"}
        ]
        assess(item, self.ledger, self.backend)
        self.assertEqual(self.backend.calls, 3)

    def test_native_ids_ignore_handle_changes_and_alias_domains(self):
        one = publication_identity("x", "https://x.com/old/status/123", "old")
        two = publication_identity("x", "https://twitter.com/new/status/123", "new")
        self.assertEqual(one["key"], two["key"])
        fake = publication_identity("x", "https://example.com/new/status/123", "new")
        self.assertNotEqual(fake["key"], one["key"])

    def test_youtube_alias_and_reddit_comment_identity(self):
        a = publication_identity("youtube", "https://youtu.be/abcdefghijk", "")
        b = publication_identity("youtube", "https://www.youtube.com/watch?v=abcdefghijk&x=1", "")
        self.assertEqual(a["key"], b["key"])
        self.assertEqual(publication_identity("reddit", "https://www.reddit.com/r/test/comments/abc/title/xyz", "")["native_id"], "t1_xyz")

    def test_optional_metadata_missing_is_not_a_global_failure(self):
        result = assess(event(), self.ledger, self.backend)
        self.assertEqual(set(result["tasks"]), set(TASKS))
        self.assertEqual(result["source_issues"], [])

    def test_quote_references_keep_their_attribution(self):
        item = event("A new release")
        item["context"] = [
            {"id": "quote", "relation": "quote", "author": "other", "text": "$COIN 0x" + "1" * 40, "url": "https://example.com/quote"}
        ]
        result = assess(item, self.ledger, self.backend)
        self.assertTrue(result["references"])
        self.assertTrue(all(r["scope"] == "quote" for r in result["references"]))

    def test_segments_are_never_presented_as_a_single_confident_answer(self):
        self.backend.prepare = lambda state, _: [state, deepcopy(state)]
        result = assess(event(), self.ledger, self.backend)
        self.assertIsNone(result["tasks"]["relevance"]["answer"])
        self.assertEqual(result["tasks"]["relevance"]["status"], "needs_review")

    def test_deleted_source_invalidates_usable_trading_context(self):
        item = event()
        item["metadata"] = {"source_deleted": True}
        result = assess(item, self.ledger, self.backend)
        token = {"chain": "bsc", "network_id": "56", "contract": "0x" + "1" * 40}
        packet = for_token(self.ledger, token, [{"platform": item["platform"], "url": item["url"]}])
        self.assertEqual(packet["signals"][0]["tasks"], {})
        self.assertFalse(packet["execution_authorized"])
        self.assertIn("deleted_source", result["source_issues"])

    def test_expired_and_missing_news_stay_explicit(self):
        item = event()
        item["observed_at"] = "2026-01-01T00:00:00Z"
        assess(item, self.ledger, self.backend)
        packet = for_token(
            self.ledger,
            {"chain": "solana", "network_id": "mainnet", "contract": "1" * 32},
            [{"platform": "github", "url": item["url"]}, {"platform": "x", "url": "https://x.com/i/status/123"}],
            now=datetime(2026, 9, 28, tzinfo=timezone.utc),
        )
        self.assertEqual([s["status"] for s in packet["signals"]], ["unavailable_or_stale", "unavailable"])

    def test_batch_refuses_replacement_of_frozen_inputs(self):
        path = Path(self.directory.name) / "batch"
        run([event("one")], path, self.ledger, self.backend)
        with self.assertRaisesRegex(ValueError, "frozen_batch_mismatch"):
            run([event("two")], path, self.ledger, self.backend)

    def test_backend_failure_is_recorded_for_every_source(self):
        class Broken(TypedBackend):
            def __call__(self, *args):
                raise TimeoutError()

        result = assess(event(), self.ledger, Broken())
        self.assertEqual(result["status"], "failed")
        self.assertTrue(all(r["status"] == "failed" for r in result["tasks"].values()))

    def test_older_replay_does_not_replace_newer_measurements(self):
        old = event()
        old["observed_at"] = "2026-09-28T10:00:00Z"
        old["metadata"] = {"author_followers": 100}
        new = deepcopy(old)
        new["observed_at"] = "2026-09-28T11:00:00Z"
        new["metadata"]["author_followers"] = 200
        result = assess(new, self.ledger, self.backend)
        assess(old, self.ledger, self.backend)
        self.assertEqual(lookup(self.ledger, result["identity"]["key"])["measurements"]["author_followers"], 200)
        self.assertEqual(self.backend.calls, 1)

    def test_batch_recurrence_is_chronological_with_input_order_preserved(self):
        older = event("Same announcement")
        older["observed_at"] = "2026-09-28T10:00:00Z"
        newer = deepcopy(older)
        newer["id"] = "newer"
        newer["url"] = newer["url"].replace("a" * 40, "b" * 40)
        newer["observed_at"] = "2026-09-28T11:00:00Z"
        output = Path(self.directory.name) / "ordered"
        run([newer, older], output, self.ledger, self.backend)
        results = [json.loads(line) for line in (output / "results.jsonl").read_text().splitlines()]
        self.assertEqual([r["recurrence"]["distinct_publications"] for r in results], [2, 1])
        self.assertEqual(results[0]["observed_at"], newer["observed_at"])

    def test_publication_after_observation_blocks_acceptance(self):
        item = event()
        item["observed_at"] = "2026-09-28T10:00:00Z"
        item["published_at"] = "2026-09-28T11:00:00Z"
        result = assess(item, self.ledger, self.backend)
        self.assertIn("publication_after_observation", result["source_issues"])
        self.assertTrue(all(t["status"] == "needs_review" for t in result["tasks"].values()))

    def test_invalid_segmentation_never_reaches_backend(self):
        self.backend.prepare = lambda *_: []
        with self.assertRaisesRegex(ValueError, "invalid_model_segments"):
            assess(event(), self.ledger, self.backend)
        self.assertEqual(self.backend.calls, 0)

    def test_batch_input_is_bounded_before_inference(self):
        path = Path(self.directory.name) / "input.jsonl"
        path.write_text(json.dumps(event()) + "\n" + json.dumps(event()) + "\n")
        with self.assertRaisesRegex(ValueError, "batch_record_limit"):
            load_events(path, max_records=1)
        path.write_bytes(b"x" * 1048577)
        with self.assertRaisesRegex(ValueError, "input_line_exceeds_one_mib"):
            load_events(path)
