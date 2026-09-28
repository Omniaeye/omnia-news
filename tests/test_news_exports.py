# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from helpers import event, TypedBackend
from omnia_news._engine.ledger import DecisionLedger
from omnia_news.casebook import publish, verify, validate_result
from omnia_news.contracts import normalize
from omnia_news.feed_adapter import adapt_feed
from omnia_news.intelligence import assess
from omnia_news.reference_index import find
from omnia_news.query import query


class NewsExportTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.ledger = DecisionLedger(self.root / "news.db")
        self.backend = TypedBackend()

    def tearDown(self):
        self.ledger.close()
        self.folder.cleanup()

    def test_public_casebook_preserves_all_answers_without_copying_primary_text(self):
        item = event("Private caller source archive body")
        result = assess(item, self.ledger, self.backend)
        receipt = publish([item], [result], self.root / "public")
        self.assertEqual(receipt["records"], 1)
        text = "".join(p.read_text(encoding="utf-8") for p in (self.root / "public").rglob("*") if p.is_file())
        self.assertNotIn(item["text"], text)
        packet = json.loads(next((self.root / "public/records").glob("*.json")).read_bytes())
        self.assertEqual(len(packet["assessment"]["tasks"]), 10)
        for path in (self.root / "public").rglob("*"):
            if path.is_file():
                self.assertNotIn(b"\r\n", path.read_bytes(), str(path))
        self.assertEqual(verify(self.root / "public"), receipt)

    def test_casebook_rejects_source_change_and_answer_tampering(self):
        item = event()
        result = assess(item, self.ledger, self.backend)
        altered = deepcopy(result)
        altered["tasks"]["tone"]["status"] = "accepted"
        with self.assertRaisesRegex(ValueError, "invalid_accepted_answer"):
            validate_result(altered)
        item["text"] += " changed"
        with self.assertRaisesRegex(ValueError, "source_assessment_mismatch"):
            publish([item], [result], self.root / "altered")

    def test_casebook_detects_modified_files(self):
        item = event()
        publish([item], [assess(item, self.ledger, self.backend)], self.root / "public")
        (self.root / "public/assessments.csv").write_text("modified")
        with self.assertRaisesRegex(ValueError, "casebook_hash_mismatch"):
            verify(self.root / "public")

    def test_casebook_binds_segment_answers_and_question_catalog(self):
        self.backend.prepare = lambda state, _: [state, deepcopy(state)]
        result = assess(event(), self.ledger, self.backend)
        validate_result(result)
        changed = deepcopy(result)
        changed["tasks"]["tone"]["segment_answers"] = []
        with self.assertRaisesRegex(ValueError, "native_segment_answer_mismatch"):
            validate_result(changed)
        changed = deepcopy(result)
        changed["inference"][0]["questions_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "native_question_catalog_mismatch"):
            validate_result(changed)

    def test_feed_adapter_does_not_claim_a_feed_excerpt_is_a_full_article(self):
        item = adapt_feed(
            {
                "id": "one",
                "platform": "news",
                "title": "Release announced",
                "body": "A short summary.",
                "url": "https://example.com/story",
                "observedAt": "2026-09-28T00:00:00Z",
            }
        )
        self.assertTrue(item["metadata"]["is_truncated"])
        self.assertIn("Release announced", item["text"])

    def test_missing_parent_is_explicit_and_counts_remain_optional(self):
        item = adapt_feed(
            {
                "id": "one",
                "platform": "x",
                "body": "Agreed",
                "url": "https://x.com/i/status/123",
                "observedAt": "2026-09-28T00:00:00Z",
                "socialMetadata": {
                    "account": {"nativeId": "456", "followers": 1234},
                    "relationships": [{"relation": "reply_to", "to": "missing"}],
                },
            }
        )
        self.assertTrue(item["metadata"]["context_missing"])
        result = assess(item, self.ledger, self.backend)
        self.assertIn("missing_parent_context", result["source_issues"])
        self.assertEqual(result["measurements"]["author_followers"], 1234)
        self.assertNotIn("view_count", result["measurements"])

    def test_engagement_changes_preserve_inference(self):
        item = event()
        item["metadata"] = {"author_followers": 100}
        first = assess(item, self.ledger, self.backend)
        item["metadata"]["author_followers"] = 200
        second = assess(item, self.ledger, self.backend)
        self.assertEqual(self.backend.calls, 2)
        self.assertEqual(first["content_version"], second["content_version"])
        self.assertNotEqual(first["source_input_sha256"], second["source_input_sha256"])
        self.assertEqual(second["measurements"]["author_followers"], 200)

    def test_github_release_requires_explicit_source_kind(self):
        item = event()
        item["url"] = "https://github.com/example/project/releases/tag/v1"
        with self.assertRaisesRegex(ValueError, "invalid_commit_identity"):
            normalize(item)
        item["metadata"] = {"source_kind": "release"}
        self.assertEqual(normalize(item)["repository"], "example/project")

    def test_recurrence_deduplicates_same_publication(self):
        item = event("A new API was released")
        item["observed_at"] = "2026-09-28T00:00:00Z"
        first = assess(item, self.ledger, self.backend)
        repeated = assess(item, self.ledger, self.backend)
        self.assertEqual(repeated["recurrence"]["distinct_publications"], 1)
        self.assertEqual(repeated["recurrence"]["novelty"], "previously_observed")
        item["id"] = "second"
        item["url"] = item["url"].replace("a" * 40, "b" * 40)
        item["author"] = "second-author"
        second = assess(item, self.ledger, self.backend)
        self.assertEqual(second["recurrence"]["distinct_publications"], 2)
        self.assertEqual(second["recurrence"]["distinct_author_references"], 2)
        self.assertEqual(first["recurrence"]["novelty"], "first_in_archive")

    def test_replaying_a_source_does_not_refresh_its_first_occurrence(self):
        item = event("Same announcement")
        item["observed_at"] = "2026-09-28T01:00:00Z"
        assess(item, self.ledger, self.backend)
        item["observed_at"] = "2026-09-28T10:00:00Z"
        assess(item, self.ledger, self.backend)
        item["id"] = "later"
        item["url"] = item["url"].replace("a" * 40, "b" * 40)
        item["observed_at"] = "2026-09-28T11:00:00Z"
        result = assess(item, self.ledger, self.backend)
        self.assertEqual(result["recurrence"]["distinct_publications"], 1)

    def test_author_alias_and_primary_mentions_have_separate_indexes(self):
        item = event("A report from @OtherAccount")
        item["metadata"] = {"author_handle": "AuthorAccount"}
        result = assess(item, self.ledger, self.backend)
        authored = find(self.ledger, "author_handle", "@authoraccount")
        mentioned = find(self.ledger, "handle", "@otheraccount", scope="primary")
        self.assertEqual(authored[0]["scope"], "author")
        self.assertEqual(mentioned[0]["scope"], "primary")
        self.assertEqual(authored[0]["assessment"]["assessment_id"], result["assessment_id"])
        self.assertEqual(find(self.ledger, "author_handle", "@OtherAccount"), [])

    def test_query_reads_existing_cache_without_model_or_database_creation(self):
        item = event()
        result = assess(item, self.ledger, self.backend)
        found = query(self.root / "news.db", url=item["url"], platform=item["platform"])
        self.assertEqual(found["assessment_id"], result["assessment_id"])
        self.assertEqual(self.backend.calls, 2)
        with self.assertRaises(FileNotFoundError):
            query(self.root / "absent.db", identity=result["identity"]["key"])
        self.assertFalse((self.root / "absent.db").exists())

    def test_repository_source_is_not_mislabeled_as_commit_author(self):
        item = adapt_feed({
            "id": "commit", "platform": "github", "title": "Add a new API", "sourceLabel": "example/project",
            "actor": "push-account", "url": "https://github.com/example/project/commit/" + "a" * 40,
            "observedAt": "2026-09-28T00:00:00Z",
        })
        result = assess(item, self.ledger, self.backend)
        self.assertEqual(result["attribution"]["identity_kind"], "source_label")
        self.assertEqual(result["attribution"]["source_actor"], "push-account")
        self.assertFalse(result["attribution"]["independently_verified"])

    def test_repost_label_cannot_inherit_an_announcement_from_context(self):
        item = event("Reposted", "x")
        item["url"] = "https://x.com/i/status/123"
        item["metadata"] = {"source_event_type": "social_repost"}
        item["context"] = [{"id": "quote", "relation": "repost", "author": "another",
                            "text": "New product launches today", "url": "https://x.com/i/status/124"}]
        result = assess(item, self.ledger, self.backend)
        self.assertIn("status_only_primary", result["source_issues"])
        self.assertTrue(all(t["status"] == "needs_review" for t in result["tasks"].values()))

    def test_source_delete_event_invalidates_accepted_tasks_without_repeating_inference(self):
        item = event("Deleted", "x")
        item["url"] = "https://x.com/i/status/123"
        assess(item, self.ledger, self.backend)
        item["metadata"] = {"source_event_type": "social_delete"}
        result = assess(item, self.ledger, self.backend)
        self.assertIn("deleted_source", result["source_issues"])
        self.assertTrue(all(t["status"] == "needs_review" for t in result["tasks"].values()))
        self.assertEqual(self.backend.calls, 2)

    def test_commit_at_collection_text_limit_retains_a_completeness_gate(self):
        item = adapt_feed({
            "id": "commit", "platform": "github", "eventType": "commit_push", "body": "a" * 4000,
            "url": "https://github.com/example/project/commit/" + "a" * 40,
            "observedAt": "2026-09-28T00:00:00Z",
        })
        result = assess(item, self.ledger, self.backend)
        self.assertIn("source_limit_reached", result["source_issues"])
        self.assertEqual(result["tasks"]["relevance"]["status"], "needs_review")
