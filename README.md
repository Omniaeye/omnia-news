<p align="center"><img src="assets/eye.png" width="112" alt="OMNIA EYE" /></p>
<h1 align="center">OMNIA NEWS</h1>
<p align="center"><strong>Control what reaches your feed. Keep the evidence behind the decision.</strong></p>
<p align="center">Local typed assessments · Explicit publication policy · Durable decision records</p>
<p align="center"><a href="#quickstart">Quickstart</a> · <a href="docs/API.md">API</a> · <a href="docs/PARAMETERS.md">Parameters</a> · <a href="docs/ARCHITECTURE.md">Architecture</a> · <a href="docs/OPERATIONS.md">Operations</a></p>
<p align="center"><a href=".github/workflows/checks.yml"><img alt="Product checks" src="https://github.com/Omniaeye/omnia-news/actions/workflows/checks.yml/badge.svg" /></a> <a href="LICENSE"><img alt="Apache-2.0" src="https://img.shields.io/badge/license-Apache_2.0-63d6bc" /></a></p>

---

OMNIA NEWS turns supplied source records into **keep**, **suppress** or **review** decisions. It preserves source attribution, evaluates the information in the primary text, and records the final disposition with its policy, evidence references and timestamps.

The local inference engine is [OMNIA Laya](https://github.com/Omniaeye/omnia-laya). Closed answer types follow the decision-oriented approach discussed in [Research](docs/RESEARCH.md); this package does not call a hosted JEV service. Source collection, source archives and actual publication belong to the consuming application.

| Capability | What it delivers |
| --- | --- |
| Source contracts | Six platform labels, source ID, author, HTTPS reference and timezone-aware timestamps |
| Independent attribution | Replies, quotes and reposts retain their own authors and references |
| Commit handling | Full commit SHA, conservative trailer removal and exact bookkeeping formats |
| Optional metadata | 32 validated fields for source context, provenance and commit observations |
| Configurable policy | Probability gate, suppression controls, language allowlist and age-at-observation limit |
| Durable assessments | Final action, reason, policy, UTC evaluation time, source fingerprints and inference record |


## Decision path

```text
Source record --> Contract + attribution --> Metadata gates --> Typed informativity --> Feed policy --> Persisted assessment
```

## A message is more than a hash

`Fix retry after timeout abc1234` describes a change. Its identifier is useful
provenance. A bare hash carries no explanation. OMNIA keeps that distinction
explicit instead of treating every technical commit as noise.

Only an unambiguous final block of known attribution trailers is removed from model text. A matching phrase in the subject or body remains intact, and the complete supplied event remains fingerprinted. Empty or hash-only GitHub messages without context can receive a deterministic format decision. Bookkeeping suppression requires both an exact format and an accepted model answer. Arbitrary bracketed explanations remain free-form text and cannot enable automatic suppression.

| Action | Meaning |
| --- | --- |
| `keep` | The accepted answer supports an informative primary text |
| `suppress` | An enabled literal-format or confirmed bookkeeping rule proposes exclusion |
| `review` | A source gate, policy control or model assessment requires human/application review |

Incomplete text, deleted sources, retractions and unconverted HTML go to review by default, without inference. Policy can also require a supplied language or publication timestamp. An account badge, bot flag, signature claim or advisory severity never proves that a report is true or that code is safe.

This release evaluates **informativity**. It does not implement factual verification, entity extraction, narrative clustering, a news crawler or a publishing service. `preserve_archive: true` tells the caller to retain the original source; it is not an archive implementation.


## Quickstart

Python 3.10 or newer. Install the product and its pinned local inference dependency:

```bash
git clone https://github.com/Omniaeye/omnia-news.git
cd omnia-news
python -m pip install '.[local]'
export OMNIA_LAYA_REVISION=55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851
omnia-news --input examples/input.jsonl
```

PowerShell:

```powershell
python -m pip install '.[local]'
$env:OMNIA_LAYA_REVISION = '55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851'
omnia-news --input examples/input.jsonl
```

Install with `python -m pip install .` when consuming contracts without local
inference. The optional runtime loads only when an item needs model evaluation.
Repeated identical requests reuse recorded inference while each evaluation records its final disposition. The included input is a small contract example; replace it with source observations from your adapter.

Run `omnia-news --catalog` to inspect the metadata schema without configuring or loading a model. For large input files, the CLI reports a resumable byte offset at its batch boundary; see [Operations](docs/OPERATIONS.md) for `--offset-bytes` and recovery behavior.

## Choose your policy

```python
from omnia_news.pipeline import process
from omnia_news.policy import NewsPolicy

result = process(
    event, ledger, backend,
    min_probability=0.90,
    policy=NewsPolicy(
        allow_operational_suppression=False,
        allowed_languages=("en", "pt-BR"),
        max_age_seconds=86400,
    ),
)
```

Age is measured between the supplied `published_at` and `observed_at`, so replay is stable. The language allowlist checks supplied labels; it does not detect language or switch models. These settings are also available to the CLI through environment variables. See [Parameters](docs/PARAMETERS.md) for exact names, defaults and metadata effects.


## Inspect every decision

Every completed result includes an `assessment_id`, UTC `evaluated_at`, final `action` and `reason`, readable decision notes, the applied policy and fingerprints of the supplied and normalized event. Model-backed results additionally include answers, probability gates, checkpoint provenance, runtime hashes, timing and cache status. Metadata gates can complete with `decision: null` because no model assessment was requested.

Backend failures record a failed final assessment with the exception type before propagating the error. Primary text, context text and free-form metadata values are not copied into the ledger. Identifiers, authors and evidence URLs remain application data: store the ledger privately and retain source archives separately.

| Read next | Purpose |
| --- | --- |
| [API](docs/API.md) | Input fields, output semantics and callable interface |
| [Parameters](docs/PARAMETERS.md) | Executable metadata catalog and policy configuration |
| [Architecture](docs/ARCHITECTURE.md) | Deterministic checks, model boundary and replay |
| [Operations](docs/OPERATIONS.md) | Environment, limits, failures and recovery |
| [Validation](docs/VALIDATION.md) | Validation scope and historical inference evidence |
| [Research](docs/RESEARCH.md) | Primary sources behind the design |

## Build and verify

```bash
python -m pip install -e . ruff==0.16.8
python -m unittest discover -s tests -v
ruff check src tests tools
python tools/verify_snapshot.py
```

The tests cover contracts, deterministic policy, controlled backend responses, persistence and recovery. Regression fixtures are **not model-quality benchmarks**. The earlier `docs/verification.json` receipt describes its recorded version and input; it does not validate later code or prove task accuracy. Calibrate automatic routing against reviewed source samples before deployment.

The product shares its local integration with [OMNIA Trading](https://github.com/Omniaeye/omnia-trading). [Data Stream Multichain](https://github.com/Omniaeye/data-stream-multichain) is a related evidence project; an adapter must supply its observations to this package. No connector is bundled here.

Original OMNIA product code. Laya remains the attributed local decision engine. [Apache-2.0](LICENSE) · [Notices](THIRD_PARTY_NOTICES.md) · [Security](SECURITY.md)
