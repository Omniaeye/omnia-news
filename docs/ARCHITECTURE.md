# Architecture

OMNIA News separates source identity, model inference, acceptance policy and consumption.

```text
Feed adapter / source record
        |
Source contract + publication identity
        |
Language routing + attributed input segments
        |
Versioned task catalog -> native LAYA -> inference cache
        |
Independent task thresholds + source-quality checks
        |
Assessment index + recurrence archive
        |
Feed policy / explicit token references / trading context
```

## Modules

| Module | Responsibility |
| --- | --- |
| `contracts` | Bounded records, source URLs, attribution and timestamps |
| `catalog` | 43 optional metadata definitions and validation |
| `identity` | Native publication keys and content versions |
| `feed_adapter` | Projection of existing feed payloads without network I/O |
| `assessment_tasks` | Ten atomic questions and default acceptance policy |
| `news_runtime` | Pinned English/multilingual models and complete input segmentation |
| `intelligence` | Per-task outcomes, evidence references and persisted lookup |
| `temporal` | Exact-text recurrence within the local archive |
| `reference_index`, `query` | Scoped reference search and read-only cached inspection |
| `trading_context` | Fresh cached assessments for caller-supplied publication links |
| `batch` | Frozen input, complete outcome accounting and replay |
| `casebook` | Per-publication exports, CSV tables and integrity verification |
| `pipeline`, `policy` | Existing informativity filter and feed disposition |
| `_engine` | Hash-verified shared local inference and ledger snapshot |

## Cache and persistence

The shared runtime caches question inputs, question/option order, pinned model
revision and runtime configuration. Intelligence uses a structural inference
floor of zero, then applies independent thresholds outside that cache. Consumers
read `tasks.*.status` for acceptance.

The SQLite ledger stores inference records and immutable final assessments.
`news_index` supports publication/version lookup. `news_occurrences` supports
exact-text recurrence. These are local application tables created only in the
configured News database, never in the production source database.

Model execution happens outside the shared ledger's transaction. Expiring claims
allow retries after a process failure. A crashed computation may repeat; only a
valid claim owner commits its result. Independent database files do not provide
distributed deduplication. Each worker owns its connection.

Original text belongs to the caller's source archive. The assessment records its
hash, identity, references, task answers and model provenance. Casebook exports
preserve those references without copying complete source articles.

## Attribution and identity

Primary text and quoted/replied-to text remain separate. A regex match includes
its source scope and character offsets. Token names, cashtags and address-shaped
strings remain observed references until another component establishes identity.
The trading context API labels a URL association as caller-supplied, not official
affiliation or author endorsement.

The News package supports explicit Robinhood, BSC and Solana context identities.
News evaluation itself remains chain-independent. A contract on one network is
not merged with the same address on another network.

## Two consumer paths

The original `process` API proposes `keep`, `suppress` or `review` based on a narrow
informativity policy. Its source and model contracts remain compatible.

The `assess` API produces ten independent intelligence dimensions. It does not
publish a post, replace the feed's existing rules or authorize a trading order.
The consuming application selects the dimensions and freshness policy it needs.

## Model boundary

JEV/LAYA answers closed typed questions. Code controls identity, timestamps,
counting, cache keys, limits, thresholds and evidence references. Source strings
are untrusted input. Neither source text nor model output invokes tools or URLs.

Classification is not factual verification. The package extracts explicit textual
references and exact-text recurrence; open-ended named-entity extraction and
semantic narrative clustering are not inferred from those features.
