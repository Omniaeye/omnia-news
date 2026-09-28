<p align="center"><img src="assets/eye.png" width="112" alt="OMNIA EYE" /></p>
<h1 align="center">OMNIA NEWS</h1>
<p align="center"><strong>News intelligence. Reusable decisions.</strong></p>
<p align="center">JEV/LAYA &middot; Source context &middot; Persistent assessments</p>
<p align="center"><a href="#assessments">Assessments</a> &middot; <a href="#quickstart">Quickstart</a> &middot; <a href="docs/INTELLIGENCE.md">Intelligence API</a> &middot; <a href="docs/PARAMETERS.md">Parameters</a> &middot; <a href="docs/CONFIDENCE.md">Confidence</a></p>
<p align="center"><a href=".github/workflows/checks.yml"><img alt="Product checks" src="https://github.com/Omniaeye/omnia-news/actions/workflows/checks.yml/badge.svg" /></a></p>

---

OMNIA NEWS evaluates source content and stores the result against the original publication. A feed, token view or trading application can retrieve the same assessment without repeating inference.

The package combines ten JEV/LAYA judgments, 43 optional metadata fields, attributed reply and quote context, publication identity, and a persistent decision ledger. The local engine runs through [OMNIA Laya](https://github.com/Omniaeye/omnia-laya).

## Examples

[Browse the examples](examples/README.md) for publication records, native answers and evaluation details.

## Assessments

| Dimension | Answers | Application |
| --- | --- | --- |
| Relevance | Informative, noise | Identify readable content in the primary text |
| Event | Launch, partnership, listing, incident, regulation, technical, other | Organize the reported event |
| Claim | Announcement, opinion, question, allegation, correction, insufficient | Distinguish a report from an author's interpretation |
| Tone | Positive, negative, neutral, mixed, insufficient | Describe the primary text's overall tone |
| Importance | Routine, project, sector, insufficient | Assess the scope explicitly described |
| Urgency | Immediate, scheduled, none, insufficient | Identify time-sensitive statements |
| Promotion | Promotional, informational, mixed, insufficient | Separate reporting and solicitation |
| Token reference | Explicit, possible, absent | Identify text that needs asset resolution |
| Narrative subject | Character, person, product, cultural, absent | Identify a narrative category, including mascots and pets |
| Context dependence | Standalone, dependent, insufficient | Identify content that relies on another publication |

Each dimension has its own answer, probability distribution and acceptance threshold. A weak tone assessment does not invalidate a strong relevance assessment. `accepted`, `needs_review`, `insufficient` and `failed` describe each task independently.

Relevance reads the author's own text in a separate request. Quote context cannot turn an empty status into an informative publication. Source completeness and missing context have their own checks.

Importance describes the reported event. It is not a forecast of price movement. Narrative subject classifies a category; it does not invent a name or resolve an asset from a ticker.

## Publication to application

```text
Source + attributed context
          |
Publication identity and content version
          |
Language routing and bounded model input
          |
Ten independent JEV/LAYA assessments
          |
Persistent cache + per-task policy
          |
Feed context / token references / trading context
```

X posts use their native post ID. YouTube videos use their video ID. GitHub commits include the repository and full SHA; release, issue and pull-request URLs are supported explicitly. Reddit posts and comments have separate identities. Websites use a canonical URL and content version. Handles remain author references, not publication keys.

Replies, quotes and reposts keep their own authors. Long inputs are split without dropping text; their segment answers remain available and the aggregate requires review. News-feed excerpts retain their incomplete-source marker. The package never fetches a source URL during inference.

## Quickstart

Python 3.10 or newer:

```bash
git clone https://github.com/Omniaeye/omnia-news.git
cd omnia-news
python -m pip install '.[local]'
export OMNIA_LAYA_REVISION=55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851
export OMNIA_NEWS_DATABASE=var/news/decisions.sqlite3
omnia-news-batch --input examples/input.jsonl --output var/news/first-batch
```

PowerShell:

```powershell
python -m pip install '.[local]'
$env:OMNIA_LAYA_REVISION = '55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851'
$env:OMNIA_NEWS_DATABASE = 'var/news/decisions.sqlite3'
omnia-news-batch --input examples/input.jsonl --output var/news/first-batch
```

The revision pins model weights. Language routing selects the English or multilingual checkpoint from that revision. GPU use is configured with `OMNIA_LAYA_DEVICE=cuda`; CPU is the default. Original source collection and actual publication remain owned by the caller.

### Evaluate and retrieve

```python
from omnia_news._engine.ledger import DecisionLedger
from omnia_news.config import Config
from omnia_news.intelligence import assess, lookup
from omnia_news.news_runtime import RoutedNews

config = Config.from_env()
ledger = DecisionLedger(config.runtime.database)
try:
    result = assess(event, ledger, RoutedNews(config.runtime))
    stored = lookup(ledger, result["identity"]["key"])
    relevance = stored["tasks"]["relevance"]
finally:
    ledger.close()
```

`event` is a normalized source record. The exact contract and a complete batch workflow are in [Intelligence API](docs/INTELLIGENCE.md).

## Confidence and policy

OMNIA retains the full probability distribution, maximum answer probability and the model's original confidence statistic. These are different measurements. The initial acceptance threshold is `0.8` per task; it is a configurable policy value, not a measured accuracy claim.

A threshold change reuses stored inference. Content, context, question or model changes receive a new inference identity. [Confidence](docs/CONFIDENCE.md) defines calibration, independent review and task-level reporting.

```json
{"relevance": 0.9, "tone": 0.85, "token_reference": 0.95}
```

Save this object as a threshold file and pass `--thresholds path/to/thresholds.json`. Values are examples of policy configuration, not calibrated recommendations.

### Search the archive

```bash
omnia-news-query --database var/news/decisions.sqlite3 --reference-kind author_handle --value @account
```

Search by author ID, observed handle, publication URL, mentioned URL, cashtag or address reference. Results retain primary/quoted attribution and content version. The query command opens the database read-only and does not load a model.

## Token and trading context

A consuming application supplies a network-scoped asset and the exact publication URLs associated with it. `trading_context.for_token` retrieves cached assessments, checks age and source issues, and returns only accepted dimensions for current records.

Robinhood, BSC and Solana are explicit network families. The relationship is retained as caller-supplied evidence. A matching name or ticker never establishes official affiliation. News assessments do not authorize orders.

## Measured source context

Character count, byte size, context count and segment count are calculated directly. Source-reported followers, views, likes, replies and reposts are optional. Missing counts are not converted to zero.

Exact-text recurrence records distinct publications, author references and platforms within six hours of an observation. Its baseline is the local assessment archive. Platform accounts, publisher labels and activity actors keep separate attribution. Recurrence does not claim semantic narrative clustering or universal novelty detection.

## Feed filtering

The existing `omnia-news --input examples/input.jsonl` interface remains available. It evaluates informativity and proposes `keep`, `suppress` or `review`.

A bare commit hash can receive a deterministic format decision. A meaningful commit message containing a hash is preserved. Automatic bookkeeping suppression requires both an exact format and an accepted model answer. Archive records are retained.

## Records and operations

A batch freezes its input hash before inference and writes every outcome, including failures. The output includes `freeze.json`, `results.jsonl`, `summary.json` and a SHA-256 manifest. Repeating the same batch reuses successful inference; a different input cannot overwrite the frozen batch.

| Documentation | Contents |
| --- | --- |
| [Intelligence API](docs/INTELLIGENCE.md) | Identity, context, cached retrieval and trading integration |
| [Parameters](docs/PARAMETERS.md) | Metadata types, task criteria and configuration |
| [Confidence](docs/CONFIDENCE.md) | Probabilities, acceptance and calibration |
| [Architecture](docs/ARCHITECTURE.md) | Modules, ownership and persistence |
| [Operations](docs/OPERATIONS.md) | Environment, replay and failure recovery |
| [Validation](docs/VALIDATION.md) | Software checks and native evaluation records |
| [Reading the results](docs/READING_THE_RESULTS.md) | Source examples, model answers and application gates |
| [Research](docs/RESEARCH.md) | Technical references |

## Build and verify

```bash
python -m pip install -e . ruff==0.16.8 build
python -m unittest discover -s tests -v
ruff check src tests tools
python tools/verify_snapshot.py
python -m build
```

Contract tests use controlled responses to check software behavior. Native model evaluation is reported separately, with its input selection, revision and observed results.

Copyright 2026 OMNIA EYE Corporation. [Apache-2.0](LICENSE) &middot; [Third-party notices](THIRD_PARTY_NOTICES.md) &middot; [Security](SECURITY.md)
