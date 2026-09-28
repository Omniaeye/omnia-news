# News intelligence API

## Source contract

Required: `id`, `platform`, `url`, `author`, `text`, `observed_at`.
Optional: `published_at`, `language`, `context`, `metadata`.

Platforms: `x`, `github`, `reddit`, `youtube`, `website`, `news`.
URLs must be HTTPS without embedded credentials. Timestamps include a timezone.
Each context record contains its own `id`, `relation`, `author`, `text` and `url`.
Supported relations: `reply_to`, `quote`, `repost`. The source contract currently bounds context to four records; an over-budget event fails explicitly.

`assess` accepts up to 1 MiB of serialized input and 200,000 primary-text characters. The legacy filtering API retains its smaller default bounds. Model token budgets are enforced separately before inference.

## Identity and revision

`identity.publication_identity(platform, url, fallback_id)` returns a stable key, canonical reference, native identifier when recognized, and the original caller ID.

X and YouTube aliases resolve to native publication IDs. Reddit comments remain separate from posts. GitHub uses repository-scoped URLs. A website key retains its query string and removes its fragment; it does not guess which query parameters are irrelevant.

`content_version` fingerprints primary text, author, language, context and assessment-relevant metadata. Observation clocks and changing engagement counts do not invalidate an unchanged evaluation. Source input hashes still bind the complete supplied record.

## Assessment

```python
result = assess(event, ledger, backend, thresholds={"relevance": 0.9})
```

A backend exposes `manifest()` and a typed inference call. `RoutedNews` additionally chooses a pinned model per input and prepares bounded segments. The original local runtime snapshot remains byte-verified.

The result contains identity, content version, source input hash, clocks, measurements, observed references, task decisions, inference receipts, recurrence statistics and an assessment ID.

Regex extraction identifies URLs, handles, cashtags, EVM address-shaped references and Base58 candidates. Each match retains its original scope and character offsets. An address-shaped string is not proof of chain membership; a cashtag is not a verified asset. Name extraction, affiliation verification and semantic narrative clustering are separate concerns.

Long text is split by exact character boundaries until each segment fits the tokenizer. No characters are discarded. Context fragments remain context. Segment responses remain individually inspectable; a document-level answer is not fabricated from them.

## Cached retrieval

Version 2 evaluates relevance separately over `{"text": primary_text}`. The other
nine tasks receive attributed primary and context records. Each inference receipt
records its scope, task IDs and segment index. Editing a quote invalidates the
context assessment while retaining an unchanged primary-text relevance result.

`feed_decision` reports `keep`, `suppress` or `review` with its reason and basis.
Exact operational formats are evaluated independently of native probabilities.
Short social fragments and incomplete sources require review. An accepted native
noise answer cannot suppress free-form prose. `preserve_archive` remains true;
`publication_authorized` remains false until the consuming application applies its policy.

For feed eligibility, use `feed_decision`, not the maximum probability or an
individual task status. Source format can conflict with a high-confidence answer;
`tasks.relevance.review_reasons` retains that conflict without changing the answer.

```python
stored = lookup(ledger, identity_key)
historical = lookup(ledger, identity_key, content_version)
```

The index stores source versions and the latest assessment for each version. The underlying assessment ledger retains previous assessments. Retrieval never loads weights or follows external URLs.
An older observation cannot replace the indexed assessment of a newer observation.
For equal observation times, re-evaluation updates the indexed acceptance policy.

## Trading consumption

```python
from omnia_news.trading_context import for_token

packet = for_token(
    ledger,
    {"chain": "bsc", "network_id": "56", "contract": token_contract},
    [{"platform": "x", "url": original_post_url}],
    max_age_seconds=3600,
)
```

The caller supplies the asset and its source references. Output carries the relationship basis, assessment ID, content version, age and accepted task values. Missing or expired news is explicit. The news library does not assert that the author endorsed the token and does not generate or authorize an order.

Version 2 records also carry their feed decision. Review and suppressed records
return no accepted trading tasks, even if an individual native answer has high
probability. The full source assessment remains available through `lookup`.

## Batch records

```bash
omnia-news-batch --input sources.jsonl --output var/news/window
omnia-news-batch --input capture.json --capture --output var/news/feed-window
```

Refresh relevance from an existing version 1 batch while retaining unchanged tasks:

```bash
omnia-news-batch --input sources.jsonl --prior-assessments var/news/v1/results.jsonl --output var/news/v2
```

The inputs must have the same order and complete source hashes. The prior assessment
ID, original task catalog and native distributions are verified before reuse.
Inherited receipts keep their original IDs, hashes and model configuration, plus
`reuse_kind=prior_assessment` and `reused_from`. Their old relevance answer remains
in the historical receipt but does not participate in the new relevance decision.
Fresh requests execute both task groups. Old casebooks remain verifiable against
their version 1 catalog.

The feed adapter accepts an OMNIA capture containing `rows[].payload`. It projects supplied source text, native references and available reply context. Website/news feed content is marked as an excerpt. It performs no provider requests.
The existing commit collector bounds descriptions to 4,000 characters. A captured
commit at that boundary receives `source_text_at_limit`; completeness requires
confirmation even when its individual model segments fit. This adapter preserves
the captured text and does not download the rest of a commit.

`freeze.json` binds source IDs and the complete normalized input hash. `results.jsonl` has one result per input; failures include the source hash and error type. A partial JSONL remains available after interruption. Resume with the same input and output directory to reuse successful inference. Changed input is rejected.
Processing follows observation time for recurrence. Final results retain input order;
partial results follow processing order and carry their source hashes.

The casebook exporter accepts the frozen events and their results. It verifies source/result hashes, writes per-publication JSON and a CSV assessment table, and creates a file-integrity manifest. Public packets contain source references and assessments; original full text remains in the caller archive.

```python
import json
from pathlib import Path
from omnia_news.batch import load_events
from omnia_news.casebook import publish

events = load_events("sources.jsonl")
results = [json.loads(line) for line in Path("var/news/window/results.jsonl").read_text(encoding="utf-8").splitlines()]
receipt = publish(events, results, "examples/my-news-window")
```

The destination must be new; existing casebooks are never replaced implicitly.
The input must be identical to the batch's normalized source input. Use
`load_events("capture.json", capture=True)` when the batch used `--capture`.

```bash
python -m omnia_news.casebook examples/my-news-window
```

Verification checks the full file set, SHA-256 hashes, task catalog, native-answer
bindings, segmented responses, acceptance gates and recomputed batch totals.


## Reference lookup

```python
from omnia_news.reference_index import find

posts = find(ledger, "author_handle", "@account")
mentions = find(ledger, "handle", "@account", scope="primary")
links = find(ledger, "url", "https://example.com/announcement")
```

Search is bounded to 50 results by default, with a maximum of 500. Author handles
are case-insensitive observed aliases. Author IDs, publication URLs, primary-text
mentions and quoted references have separate index entries. Historical content
versions remain searchable; callers inspect the version, source issues and clock
before using an older reference. A matching handle is not evidence of token ownership.


## Read-only command line

```bash
omnia-news-query --database var/news/decisions.sqlite3 --identity x:POST_ID
omnia-news-query --database var/news/decisions.sqlite3 --platform x --url https://x.com/i/status/POST_ID
omnia-news-query --database var/news/decisions.sqlite3 --reference-kind author_handle --value @account
```

Replace `POST_ID` and `@account` with captured identifiers. The query command opens
an existing SQLite database in read-only mode. It does not create a missing
archive, load models, or require checkpoint configuration.

## Attribution basis

The feed adapter distinguishes a platform account from a repository or publisher
source label. A GitHub activity actor is retained separately; a push actor is not
automatically the commit author. `attribution.identity_kind` makes this basis
explicit. Exact-text recurrence counts author references, not verified individual
people. The original source collection determines which identity evidence exists.

Recurrence retains the first observation of each publication/content pair.
Replaying an old source does not refresh that first occurrence or create a new
publication. `previously_observed` distinguishes a retained source from a first
local observation. No first-in-archive label claims worldwide novelty.

Collection event types are retained in `source_event_type`. A delete event blocks
automatic use, and bare repost/pin/unpin/reply/quote status labels cannot inherit
an accepted announcement from their context. Native responses remain visible for
review, separately from the application gate.
