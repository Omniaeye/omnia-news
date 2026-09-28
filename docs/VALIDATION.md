# Validation

## Relevance and feed eligibility — 0.3.1

The [complete follow-up window](../examples/news-window-2026-09-28-v2/README.md)
uses separate primary-text relevance input and preserves unchanged version 1
receipts for other tasks. All 500 sources completed. The feed policy produced
64 keep, 46 exact-format suppress and 390 review outcomes at the unchanged 0.8
threshold. The final replay reused all native receipts.

The [source review](../examples/relevance-review-2026-09-28/README.md) retains
assistant annotations and every decision. Its 11 decisive outcomes matched the
review; 35 remained review. This is diagnostic evidence, not independent human
ground truth or fitted probability calibration. Native false positives and
format-policy overrides remain visible in the source records.

Fresh evaluation and immediate cache replay were also checked on three captured
sources: an English news post, a GitHub change and a Chinese post. Each fresh
assessment executed two scoped calls; each repeated assessment reused both.
The software checks cover scope isolation, prior-record integrity, cache reuse,
exact-format boundaries and blocked trading-context export for suppressed sources.

The version 0.3.0 measurements below describe the original catalog and remain
historical records.

## Version 0.3.0

The local suite passed **85 tests**, Ruff, runtime fingerprint checks, casebook
verification, wheel/source builds and an isolated installed-wheel import check.
The staged Git tree also passed casebook verification after line-ending
normalization. [Machine-readable receipt](verification-0.3.0.json) binds the source
files, frozen input and casebook manifest. CI checks belong to their exact commit.

Software checks cover per-task acceptance, policy-only cache reuse, observation-clock
reuse, content/context invalidation, native publication aliases, missing fields,
source-quality gates, attributed references, read-only inspection, network-scoped
trading context, frozen input, source/result bindings and public casebook integrity.

Contract tests provide controlled backend responses to verify software behavior.
Native inference is recorded separately against captured source data. A successful
software check does not establish semantic precision or market performance.

The 500-publication evaluation freezes the source selection before inference and
records every task response, weak answer and failure. Per-task accuracy is left
unreported without an independently labeled reference set. Acceptance counts
report application policy coverage only.

## Native source window — 28 September 2026

[Inspect all 500 records](../examples/news-window-2026-09-28/README.md) · [Source inspection notes](READING_THE_RESULTS.md)

| Measurement | Result |
| --- | ---: |
| Distinct source records | 500 |
| X / GitHub / news excerpts | 273 / 219 / 8 |
| Completed / failed source evaluations | 500 / 0 |
| Native text/segment evaluations | 553 |
| Native typed answers | 5,530 |
| English / multilingual evaluations | 519 / 34 |
| Complete cache replay | 553 of 553 |
| New model evaluations during replay | 0 |
| Replay wall time, including preparation | 16.703 seconds |
| Read-only archive queries | 1,000 across all 500 records |
| Query p50 / p95 | 0.4306 / 0.6182 ms |
| Verified casebook files, excluding manifest | 1,004 |

The source selection used the feed sort cutoff `2026-09-28T20:48:07.787271+00:00` and removed
duplicate publication identities before inference. The read-only capture file was
written at 20:50:48 UTC. This is a sort/publication cutoff, not an assertion that
all records had been ingested by that earlier instant. The original source export
remains private; public records contain references, hashes and complete assessments.
The cohort includes posts, commits, replies, quotes, reposts and operational social
events. It contains no Reddit or YouTube input; those URL contracts have software
coverage, not native results in this source window.

The run used the pinned `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` checkpoints through
OMNIA Laya `256eaf39550291dec7378d5a20078cc0d500e852`, Python 3.11.15, Torch 2.14.0,
Transformers 5.17.0 and NumPy 2.4.6 on a Ryzen 5 9600X CPU. Each worker used four
threads. A second worker processed the tail of the same frozen cohort through the
shared cache; duplicate inference claims were coordinated by the ledger.

The complete original batch took 3063.641 seconds including
initialization and work shared with the second worker. Native receipt latency was
p50 6406.616 ms and p95 17604.873 ms
per text/segment evaluation. These are local observations under this workload,
not a production capacity or end-user latency certification. Cache-query timings
measure only read-only retrieval; they do not represent fresh inference.

### Per-task acceptance

| Task | Accepted | Review | Insufficient | Failed |
| --- | ---: | ---: | ---: | ---: |
| relevance | 1 | 204 | 295 | 0 |
| event | 244 | 256 | 0 | 0 |
| claim | 134 | 251 | 115 | 0 |
| tone | 4 | 288 | 208 | 0 |
| importance | 3 | 356 | 141 | 0 |
| urgency | 7 | 492 | 1 | 0 |
| promotion | 19 | 255 | 226 | 0 |
| token_reference | 172 | 328 | 0 | 0 |
| narrative_object | 48 | 452 | 0 | 0 |
| context_dependence | 1 | 365 | 134 | 0 |

All tasks used the initial 0.8 maximum-probability gate. Acceptance is policy
coverage, not accuracy. In particular, relevance accepted only one record and
returned insufficient on 295. These results do not establish an automatic feed
filter or a reliable trading trigger. The addressed-request example also shows
that a high-probability label can still be unsuitable for downstream conclusions.

Twenty records lack referenced parent context, 48 contain status-only primary
text, six commit descriptions reach the collector's text limit, 25 require
segmentation, five report deletion and eight are news excerpts. These categories
can overlap. Native answers are preserved alongside the applicable source gates.
No public feed policy, production database or order execution was changed.

## Historical validation records

## Version 0.2.0

Executed on Windows with Python 3.14.5. [Machine-readable receipt](verification-0.2.0.json)
binds the checks to source-file hashes and their actual verification time.

| Check | Result |
|---|---|
| Unit and integration suite | 52 tests passed |
| Input-boundary corpus | 400 cases exercised inside the suite |
| Ruff and diff whitespace checks | Passed |
| Shared product runtime fingerprints | Passed |
| Source distribution and wheel build | Passed |
| Clean-environment installed wheel imports and catalogs | Passed |
| Source distribution includes corpus, helpers and notices | Passed |

The case corpus is part of the reported suite, not 400 additional independent
model evaluations. Controlled backend responses exercise routing and failure
handling. No new model inference, throughput benchmark or accuracy measurement
was run for this release. The CI matrix additionally covers Python 3.10/3.12
on Windows and Linux; remote results belong to their exact commit.

Regression coverage includes source contract boundaries, final assessment storage,
claim recovery, cache reads during inference, durable failures and stream restart.
Product-specific assertions cover metadata policy and attribution in News, and
semantic domains, freshness rechecks, cross-field consistency and batch coverage
in Trading. Each package runs only its relevant product assertions.

## Evaluating model quality

Use separately reviewed examples and hold out time/source groups. Record the
checkpoint, task, catalog, policy and calibration versions. Report precision,
review coverage, false suppression, Brier/ECE and latency by task and language.
Neither contract-case counts nor repository history establish model quality.

## Historical 0.1.0 verification

The following receipt belongs to the previous release and is retained unchanged.
It does not validate the changed 0.2.0 pipeline.


Executed checks for the 0.1.0 product package. [Machine-readable receipt](verification.json).

| Check | Result |
| --- | --- |
| Contract and recovery tests | 35 passed |
| Ruff, compilation and shared-runtime fingerprint | Passed |
| Wheel build and isolated installed-package imports | Passed |
| Pinned Laya CPU inference | Completed on the included contract input |
| Durable replay | Cache hit for every recorded assessment |

## Inference result

The included commit description received `keep` with probability 0.7618. The configured 0.8 gate routed it to `review`. No message was published.

Cold processing, including model initialization, took 4.479 seconds.
Persistent replay took 0.004 seconds on this workstation.
These single-input measurements verify integration behavior. They are not throughput,
financial-performance, task-accuracy or production-capacity measurements.

The checkpoint reports a calibration warning for its 11-or-more-choice bucket.
These tasks use two choices; their active bucket passed the runtime check.
Answer probabilities still require task-specific calibration against independently reviewed data.

## Coverage

Tests exercise malformed input, identity, timestamps, unknown values, durable
replay, model failure, policy boundaries and recovery across records. Backend
doubles in contract tests provide controlled answers; the separate inference
receipt above uses the pinned local model.

For release decisions, measure accepted precision and review coverage on a labeled
source sample. Preserve source context and report results by platform and language.
