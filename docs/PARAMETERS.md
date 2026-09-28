# News parameters

The executable catalog is `omnia_news.catalog.parameter_catalog()`, schema
`omnia.news.metadata.v2`. It returns a detached JSON-serializable object with
43 field definitions, their types, limits and actual use. Validation executes
these definitions; this is not a list of planned model capabilities.

```python
from omnia_news.catalog import parameter_catalog
catalog = parameter_catalog()
assert len(catalog['fields']) == 43
```

## Source metadata

All fields below belong to the optional `event.metadata` object. Every value is
supplied by the adapter. None is discovered or independently verified by this
package. Absence means unknown/unreported; null and unknown keys are rejected.

In the legacy feed filter, **Model** sends only a small flag, enum or count to inference. **Gate** participates
in deterministic routing. **Provenance** is validated and included in the complete
source fingerprint, but is not sent to inference or used to select a disposition.
Free-form metadata remains in the caller's archive, not in the decision ledger.

| Field | Type / bound | Use |
| --- | --- | --- |
| `source_text_at_limit` | Boolean | Intelligence gate: collection text boundary reached |
| `source_event_type` | Nonempty string, 100 characters | Intelligence gate: operational social events |
| `author_identity_kind` | platform_account, source_label, unknown | Basis of the author reference |
| `source_actor` | Nonempty string, 256 characters | Reported activity actor, separate from content author |
| `context_missing` | Boolean | Intelligence gate: referenced parent absent |
| `author_handle` | Nonempty string, 100 characters | Observed author alias, separate from native ID |
| `author_followers` | Integer, 0 to 10^12 | Observed reach context |
| `view_count` | Integer, 0 to 10^12 | Source-reported engagement |
| `like_count` | Integer, 0 to 10^12 | Source-reported engagement |
| `reply_count` | Integer, 0 to 10^12 | Source-reported engagement |
| `repost_count` | Integer, 0 to 10^12 | Source-reported engagement |
| `source_kind` | article, post, commit, release, advisory, comment | Model |
| `record_type` | original, correction, update, retraction | Gate: retractions |
| `source_updated_at` | Timestamp with timezone | Provenance |
| `source_deleted` | Boolean | Gate: deleted source |
| `author_type` | person, organization, bot, unknown | Model |
| `author_verified` | Boolean; platform account badge only | Provenance |
| `publisher` | Nonempty string, 200 characters | Provenance |
| `canonical_url` | HTTPS URL, 2048 characters | Provenance |
| `title` | Nonempty source title, 300 characters | Provenance |
| `section` | Nonempty string, 100 characters | Provenance |
| `tags` | Up to 8 unique nonempty strings, 64 characters each | Provenance |
| `content_format` | plain_text, markdown, html | Gate: unconverted HTML |
| `is_truncated` | Boolean | Gate: incomplete text |
| `is_machine_translated` | Boolean | Model; translation note |
| `translation_language` | Nonempty string, 32 characters | Gate: language allowlist |
| `source_revision` | Nonempty source revision, 200 characters | Provenance |
| `origin_id` | Nonempty original-source ID, 200 characters | Provenance |
| `origin_url` | HTTPS URL, 2048 characters | Provenance |
| `is_sponsored` | Boolean | Model |
| `is_bot_generated` | Boolean | Model; never sufficient to suppress |
| `commit_parent_count` | Integer, 0–100 | Model |
| `commit_files_changed` | Integer, 0–1000000 | Provenance |
| `commit_additions` | Integer, 0–1000000000 | Provenance |
| `commit_deletions` | Integer, 0–1000000000 | Provenance |
| `commit_branch` | Nonempty string, 256 characters | Provenance |
| `commit_is_merge` | Boolean | Model |
| `commit_is_revert` | Boolean | Model |
| `commit_signature_verified` | Boolean; adapter claim, no signature verification here | Provenance |
| `commit_paths` | Up to 16 unique nonempty strings, 256 characters each | Provenance; paths never opened |
| `release_tag` | Nonempty string, 128 characters | Provenance |
| `advisory_id` | Nonempty string, 128 characters | Provenance |
| `advisory_severity` | unknown, low, moderate, high, critical | Provenance |

Commit fields require `platform: github`. When both fields are supplied,
`commit_is_merge` must equal `commit_parent_count > 1`. A translation language
requires `is_machine_translated: true`. Booleans do not accept integers or strings;
integer counts do not accept booleans. An empty list is valid for tags/paths.

There are eight compact model-context fields, eight deterministic-gate fields and
27 provenance-only fields. Metadata does not replace primary text and cannot
override the primary/context authorship boundary. A canonical URL or original
source reference is not proof of provenance authenticity.

## Routing policy

`NewsPolicy` is an immutable configuration object passed to `process(..., policy=)`.
The CLI reads the corresponding environment variables. Boolean environment values
accept `true`, `false`, `1` or `0` (case-insensitive); other values fail startup.

| Python field | Environment variable | Default | Behavior |
| --- | --- | --- | --- |
| `allow_literal_suppression` | `OMNIA_NEWS_ALLOW_LITERAL_SUPPRESSION` | true | Empty/hash-only GitHub primary text without context may be suppressed |
| `allow_operational_suppression` | `OMNIA_NEWS_ALLOW_OPERATIONAL_SUPPRESSION` | true | Exact bookkeeping format plus accepted noise answer may be suppressed |
| `review_incomplete` | `OMNIA_NEWS_REVIEW_INCOMPLETE` | true | Marked truncated text goes to review before inference |
| `review_deleted` | `OMNIA_NEWS_REVIEW_DELETED` | true | Marked deleted source goes to review before inference |
| `review_retractions` | `OMNIA_NEWS_REVIEW_RETRACTIONS` | true | Marked retraction goes to review before inference |
| `review_html` | `OMNIA_NEWS_REVIEW_HTML` | true | HTML input goes to review; the adapter must extract complete text |
| `allowed_languages` | `OMNIA_NEWS_ALLOWED_LANGUAGES` | Empty / unrestricted | Comma-separated exact labels, case-insensitive; absent/outside label goes to review |
| `max_age_seconds` | `OMNIA_NEWS_MAX_AGE_SECONDS` | Empty / disabled | Integer 0–315360000; requires published_at and checks age at observed_at |

`min_probability` remains the process argument controlled in the CLI by
`OMNIA_LAYA_MIN_PROBABILITY` (default 0.8). It gates maximum answer probability,
not entropy-based confidence and not estimated factual correctness.

In the legacy feed filter, language labels are compared exactly apart from case: `en` and `en-US` are distinct.
For machine-translated text, `translation_language` takes precedence over the
top-level language label. No language detection or model switching occurs.

Age is `observed_at - published_at`; this is intentionally stable on replay.
Missing publication time or a publication time after observation goes to review
when the age policy is enabled. This setting does not measure current queue age.

Disabling a review gate allows evaluation of the supplied text; it does not repair
the input or certify it. Disabling a suppression rule routes that case to review.
The full policy is persisted alongside every final assessment.

## Intelligence task parameters

The task catalog is `omnia_news.assessment_tasks.TASKS`, version `omnia.news.intelligence.v1`.
This path sends primary author reference, primary text and attributed context to the model.
Metadata supplies measurements, provenance and source gates; the legacy model-metadata
projection is not added to this intelligence state.
Ten named choice questions cover relevance, event, claim, tone, importance, urgency,
promotion, token reference, narrative subject and context dependence. The complete
criteria are executable data in that module, rather than a separate list in prose.

`DEFAULT_THRESHOLDS` declares one initial 0.8 policy value per task. Supply a partial
threshold dictionary to `assess(..., thresholds=...)`, or use the batch CLI's
`--thresholds` JSON file. Unknown task IDs, non-finite values and values outside
[0, 1] are rejected. Re-gating does not repeat inference.

The intelligence path evaluates primary text and attributed context. The eight
legacy model-context metadata flags described above remain part of the legacy
informativity path. Counts are measured context, not automatic authority weights.

| Intelligence setting | Value |
| --- | --- |
| Input budget | 1 MiB per normalized event |
| Primary text | Up to 200,000 characters |
| Context | Up to four separately attributed records |
| English model context | 512 tokens |
| Multilingual model context | 1,024 tokens |
| Question head | 192 tokens |
| Maximum segments | 256; overflow is an explicit failure |
| Default token-context freshness | 3,600 seconds; caller configurable |
| Exact-text recurrence window | Six hours within the retained local archive |

Model budgets are enforced by the pinned tokenizer. A file's byte size is not
its token count. Oversized input is segmented without dropping characters;
segment decisions do not become an automatically accepted whole-document result.
