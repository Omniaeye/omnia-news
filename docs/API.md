# News API

For ten-task assessments, publication identity, cached lookup and token context,
use the [Intelligence API](INTELLIGENCE.md). The interface below is the existing
feed-filtering API and retains its original policy and input bounds.

`process(event, ledger, backend, min_probability=0.8, max_bytes=65536, policy=None)` returns
`omnia.news.decision.v1`. The backend is callable `(state, questions)` and exposes
`manifest()`; use the bundled `LocalLaya` for actual inference. `ledger` is the
bundled `DecisionLedger` and provides both `decide()` and `record_assessment()`.
`policy=None` selects `NewsPolicy()` defaults. The final three arguments are keyword-only.

The CLI exposes the same metadata catalog with `omnia-news --catalog`, without
requiring a model revision or loading weights. File batches support
`--offset-bytes` for the byte offset reported at a batch boundary; see Operations.

| Input | Contract |
| --- | --- |
| `id` | Stable nonempty source ID, up to 200 characters |
| `platform` | github, x, reddit, youtube, website or news |
| `url` | HTTPS reference, up to 2048 characters, without credentials or whitespace/control characters; never fetched |
| `author` | Primary author identifier |
| `text` | Complete supplied primary text, up to 20000 characters |
| `observed_at` | Timestamp with timezone |
| `published_at` | Optional source publication time with timezone |
| `language` | Optional source language label; does not auto-select the model |
| `context` | Up to four independently attributed records |
| `metadata` | Optional object with only the typed fields in [Parameters](PARAMETERS.md) |

Each context record has `id`, `relation`, `author`, `text`, `url`. Relations are
`reply_to`, `quote` and `repost`. IDs must be unique and cannot equal the primary ID.
GitHub records require a full 40-character commit SHA in the canonical source URL.
Context text is bounded to 10000 characters per record. Author identifiers are
bounded to 256 characters. Unknown fields are rejected. Omitted metadata means
unknown/unreported, not false or zero; metadata nulls are rejected. Normalization
copies the event and does not mutate the caller's object.

```json
{
  "id": "github:example/project:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "platform": "github",
  "url": "https://github.com/example/project/commit/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "author": "example-maintainer",
  "text": "Fix reconnect handling after a request timeout",
  "observed_at": "2026-09-25T12:00:00Z",
  "published_at": "2026-09-25T11:58:00Z",
  "language": "en",
  "context": [],
  "metadata": {
    "source_kind": "commit",
    "author_type": "person",
    "commit_parent_count": 1,
    "commit_is_merge": false,
    "commit_files_changed": 2,
    "is_truncated": false
  }
}
```

This is a contract fixture, not an observation of an existing commit. The adapter
owns source authenticity, timestamps and metadata accuracy. The byte bound and
selected model's token bound are independent; accepting a source contract does
not guarantee that its complete text fits the model context. Long inputs fail
instead of being silently truncated.

The persisted final result contains:

| Output | Meaning |
| --- | --- |
| `assessment_id` | Identity returned by persistence of this final assessment |
| `status` | `completed`, or `failed` in a recorded backend failure |
| `action`, `reason`, `notes` | Proposed disposition, stable reason code and deterministic explanation |
| `source_id`, `source_url`, `source_platform`, `source_author` | Primary source attribution |
| `context_provenance` | Context IDs, relationships, authors and URLs, without their text |
| `observed_at`, `published_at`, `evaluated_at` | Supplied source times and actual UTC evaluation time |
| `original_input_sha256` | Canonical JSON hash of the supplied event object; not the raw JSONL byte hash |
| `normalized_source_sha256` | Canonical JSON hash after contract normalization, including all metadata |
| `metadata_catalog`, `metadata_fields` | Catalog version and supplied field names, without free-form values |
| `news_policy`, `min_answer_probability`, `task_version` | Applied routing policy, threshold and relevance task version |
| `decision` | Durable inference record, or null when a metadata gate avoided inference |
| `preserve_archive` | Always true; caller must retain original source archives |

The model returns `keep` or `noise`. These labels do not have the same semantics
as the final routing action: an accepted `noise` vote on unconstrained text becomes
`review`. The default metadata gates can return review before loading a model.
Each evaluation persists its final result, including model-cache replays.

Backend or inference failures persist a `status: failed`, `action: review` final
assessment with `error_code` set to an exception type, then re-raise. Input contract
violations raise `ValueError`; the CLI owns durable malformed-input reporting.
No result invents entity extraction, a factual summary, a price target or a claim
of code correctness. See [Operations](OPERATIONS.md) for stream recovery.
