# Operations

OMNIA News is a bounded processing library and JSONL command. Your
application owns source collection, scheduling, authentication and delivery.

## Installation and configuration

Use the [README](../README.md) to install the package. Export environment variables
from [.env.example](../.env.example); the command does not load dotenv files.
Pin `OMNIA_LAYA_REVISION` to the selected model family's immutable Hub commit.
An English checkpoint revision must not be reused for a different model family.

| Setting | Meaning | Default |
|---|---|---|
| `OMNIA_LAYA_MODEL` | english, typed-decisions or multilingual | english |
| `OMNIA_LAYA_DEVICE` | cpu, cuda or mps | cpu |
| `OMNIA_LAYA_THREADS` | Integer CPU thread budget | 2 |
| `OMNIA_LAYA_MAX_LEN` | Full tokenizer context limit for selected checkpoint | 512 |
| `OMNIA_LAYA_HEAD_MAX_LEN` | Instructions and answer-options budget | 192 |
| `OMNIA_LAYA_MAX_INPUT_BYTES` | Bounded UTF-8 record size | 65536 |
| `OMNIA_LAYA_MIN_PROBABILITY` | Maximum-answer-probability gate | 0.8 |
| `OMNIA_NEWS_DATABASE` | Private SQLite storage | var/news/decisions.sqlite3 |
| `OMNIA_NEWS_MAX_RECORDS` | Physical input lines per batch | 1000 |

Probability thresholds belong to the task and reviewed dataset. They are not
universal accuracy scores. Oversized model context is refused, not silently
truncated. Inspect the parameter catalog without installing or loading a model:

```bash
omnia-news --catalog
```

## Stream processing and restart

Each nonempty input line produces an outcome or a typed failure. Invalid UTF-8,
JSON, contracts and oversized records are recorded with input fingerprints;
raw provider exception messages and input bodies are not emitted in errors.
Blank lines count toward the physical line budget.

At the batch boundary the command emits `status: paused`, `reason: record_limit`,
`next_line` and, for seekable inputs, `next_offset_bytes`. It does not read the
next record to detect EOF. Therefore a pause can also occur exactly at EOF;
resuming there completes immediately. An open stream remains positioned at its
first unread record.

```bash
omnia-news --input observations.jsonl --offset-bytes 12345
```

Use only an offset previously returned for the same immutable input file. The
offset counts bytes, not characters. A file path is required for this CLI option;
stream consumers retain the existing handle. The command does not validate an
external file fingerprint. Store that fingerprint with the consumer checkpoint.

Exit codes: `0` means no record errors, including a clean batch pause; `1` means
one or more record errors; `2` means startup or fatal storage failure. A completed
`review` outcome is not a command failure. Inspect outcomes, not just exit status.

## Durable storage

| Table | Records |
|---|---|
| decisions | Successful typed model answers and their input/model fingerprints |
| assessments | Final product outcomes, policy, timing and evidence references |
| failures | Model/runtime failure type, key and time |
| claims | Expiring ownership of an in-progress inference |

Each worker owns its SQLite connection. Cache reads do not acquire a write
transaction. Inference occurs outside transactions; short claims coordinate
identical requests. Defaults: SQLite/claim wait 30 seconds; inference lease
300 seconds. Library callers can set `busy_timeout` and `lease_seconds` on
`DecisionLedger`. These values are not unconsumed environment settings.

After process death, another worker can reclaim an expired request. A late owner
cannot commit over a replacement owner. Inference exceeding the lease fails and
requires replay; choose lease duration from measured workloads. A process can
repeat model work after a crash, while successful decisions retain a unique key.

There is no background retry queue or hard cancellation of a stuck model call in
this library. A supervising worker enforces its process deadline, retains input,
and schedules retry with bounded backoff. If failure storage is unavailable, the
command fails explicitly: the caller must retain that input for recovery.

Use SQLite's backup API for live backups. Copying only the main file can omit WAL
data. Retention belongs to the operator; the package never silently deletes source
data. Model cache and final assessments are separate: a reused model answer can
participate in a new policy evaluation.

## Deployment boundaries

Protect input archives, model cache and the ledger with filesystem access controls.
Input text remains in the caller archive; these records retain hashes/references.
Evidence URLs may contain sensitive information and require application-level
access controls. Source URLs are not fetched and source strings cannot invoke tools.

After downloading and verifying the checkpoint, `HF_HUB_OFFLINE=1` prevents further
Hub downloads. The library has no public listener or embedded credentials.
An API wrapper must add identity, per-user budgets, concurrency limits and
request timeouts. Measure queue age, latency, review rate and storage growth in
that application before increasing worker count.

## Runtime provenance

The [runtime manifest](runtime-snapshot.json) preserves original OMNIA Laya hashes
and the product patch hashes separately. The two product packages carry identical
engine files. `python tools/verify_snapshot.py` checks the packaged integration;
it does not verify model weights or claim a byte-identical upstream snapshot.
The running adapter caches its code fingerprint at first use. Restart workers
after changing dependencies, runtime files or precision settings.

## News policy

All suppression/review switches accept true/false or 1/0. Defaults enable literal
and operational suppression and review incomplete, deleted, retracted or HTML
sources. `OMNIA_NEWS_ALLOWED_LANGUAGES` is an optional comma-separated allowlist.
`OMNIA_NEWS_MAX_AGE_SECONDS` is optional; it compares publication to observation,
not to the wall clock. See [parameter contracts](PARAMETERS.md) for all metadata.


## Intelligence batches

Use a dedicated `OMNIA_NEWS_DATABASE`. Collection databases remain read-only sources.
The batch command accepts normalized JSONL, or an existing feed export with
`--capture`. It makes no collector request and submits no order.

```bash
omnia-news-batch --input sources.jsonl --output var/news/window
omnia-news-batch --input sources.jsonl --output var/news/window --thresholds thresholds.json
```

The second invocation reuses the same frozen source batch. A different input hash
is rejected. Successful inference is reused; failed inference remains retryable.
Keep `results.partial.jsonl` after interruption. Rerunning the command reconstructs
the complete results file while retaining the inference cache.

The intelligence router chooses English or multilingual based on supplied language
and text/script analysis. Both models are pinned to `OMNIA_LAYA_REVISION`. They may
remain resident together; provision memory for both checkpoints. An unavailable
checkpoint produces an explicit error rather than an English-only fallback.

`OMNIA_LAYA_THREADS`, `OMNIA_LAYA_DEVICE` and `OMNIA_NEWS_MAX_RECORDS` apply to batches.
The legacy `OMNIA_LAYA_MIN_PROBABILITY` configures the legacy filter. Intelligence
thresholds come from its task catalog or `--thresholds`, independently.

Do not treat a high cache-hit rate as model accuracy. Use the native batch summary
for inference/coverage and an independently labeled evaluation for precision.
Public source namespaces are OMNIA; raw transport provenance stays in the source
archive and is never rewritten by the public exporter.
