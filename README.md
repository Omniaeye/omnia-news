<p align="center"><img src="assets/eye.png" width="112" alt="OMNIA EYE" /></p>
<h1 align="center">OMNIA NEWS</h1>
<p align="center"><strong>News in. Decisions with evidence out.</strong></p>
<p align="center">JEV decision integration · Evidence-first infrastructure</p>
<p align="center"><a href="#quickstart">Quickstart</a> · <a href="docs/API.md">API</a> · <a href="docs/ARCHITECTURE.md">Architecture</a> · <a href="docs/OPERATIONS.md">Operations</a> · <a href="docs/RESEARCH.md">Research</a></p>
<p align="center"><a href=".github/workflows/checks.yml"><img alt="Product checks" src="https://github.com/Omniaeye/omnia-news/actions/workflows/checks.yml/badge.svg" /></a> <a href="LICENSE"><img alt="Apache-2.0" src="https://img.shields.io/badge/license-Apache_2.0-63d6bc" /></a></p>

---

Turn source records into explainable feed decisions. Keep the event, its author, its context and its evidence together. JEV supplies a typed assessment; OMNIA applies a versioned publication policy.

| Capability | What it delivers |
| --- | --- |
| Source identity | Platform, native event ID, author, URL and observation time |
| Context | Separately attributed replies, quotes and reposts |
| GitHub filtering | Commit identity, useful descriptions and narrow bookkeeping suppression |
| Typed assessment | Two explicit labels, probability distributions and review boundaries |
| Durable replay | Evidence references, fingerprints and checkpoint provenance |
| Archive preservation | Feed disposition never deletes the source record |


## Decision path

```text
Source record --> Identity and attribution --> Typed relevance --> Probability gate --> Feed policy --> Evidence record
```

## A message is more than a hash

`Fix retry after timeout abc1234` describes a change. Its identifier is useful
provenance. A bare hash carries no explanation. OMNIA keeps that distinction
explicit instead of treating every technical commit as noise.

The GitHub route removes attribution trailers from the model text while retaining
the complete source fingerprint. Empty or hash-only messages receive a deterministic
format decision. Generated bookkeeping requires both a narrow format match and
an accepted model answer. Free-form text that the model calls noise goes to review.

| Action | Meaning |
| --- | --- |
| `keep` | The accepted assessment supports an informative primary text |
| `suppress` | A literal format or confirmed bookkeeping rule excludes it from the feed |
| `review` | Probability or evidence does not support automatic routing |

This evaluates message information. It does not certify the quality, correctness
or security of the code in a commit. Source fetching and feed publication remain
owned by the application consuming these records.


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
Repeated identical requests reuse recorded decisions. The included input is a
small contract example; replace it with source observations from your adapter.


## Inspect every decision

Each model record includes source and evidence IDs, input and question fingerprints,
the pinned checkpoint, runtime source hashes, model answers, probability gates,
processing time and cache status. Raw input text is not persisted in that ledger.
Keep source archives separately and protect the ledger as application data.

| Read next | Purpose |
| --- | --- |
| [API](docs/API.md) | Input fields, output semantics and callable interface |
| [Architecture](docs/ARCHITECTURE.md) | Deterministic checks, model boundary and replay |
| [Operations](docs/OPERATIONS.md) | Environment, limits, failures and recovery |
| [Validation](docs/VALIDATION.md) | Executed checks and inference evidence |
| [Research](docs/RESEARCH.md) | Primary sources behind the design |

## Build and verify

```bash
python -m pip install -e . ruff==0.16.8
python -m unittest discover -s tests -v
ruff check src tests tools
python tools/verify_snapshot.py
```

Both products share the reviewed [OMNIA Laya](https://github.com/Omniaeye/omnia-laya)
integration and connect to the [multichain evidence field](https://github.com/Omniaeye/data-stream-multichain).
The product code is original OMNIA work. Laya remains the attributed local decision
engine. [Apache-2.0](LICENSE) · [Notices](THIRD_PARTY_NOTICES.md) · [Security](SECURITY.md)
