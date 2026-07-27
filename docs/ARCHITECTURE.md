# Architecture

Source record --> Contract and attribution --> Metadata gates --> Typed informativity --> Feed policy --> Final assessment

## Product and runtime

`contracts.py` validates bounded source input. `catalog.py` declares and executes
the 32 optional metadata contracts. `pipeline.py` prepares versioned questions,
applies `NewsPolicy`, and persists the final assessment. `_engine` supplies the local ledger
and Laya adapter; its [snapshot manifest](runtime-snapshot.json) pins exact bytes.
The snapshot is bundled for independent installation, rather than importing an
uninstalled example directory from another checkout.

Laya returns closed typed answers. Deterministic code owns identities, arithmetic,
timestamps, units, thresholds and disposition. Every source string is untrusted
data. A constrained result schema and conservative policy contain what model
output can do; neither source text nor model output can invoke tools.

## Replay and evidence

Identity covers the normalized source packet, question and option order, model
revision, runtime hashes and probability policy. Changes cannot reuse an old
decision under a new identity. Provider errors are recorded by exception type and
remain retryable. Successful records retain their original processing timestamps.

The final assessment is separate from the reusable inference decision. It stores
the routing action, reason, deterministic notes, policy configuration, actual UTC
evaluation time and inference reference. A cache hit reuses the inference record
but produces a new final assessment. Backend errors also persist a failed final
assessment before propagating; no raw provider message is copied into it.

`original_input_sha256` hashes the supplied event object as canonical JSON;
`normalized_source_sha256` hashes the validated source including all metadata.
Neither is a byte-for-byte hash of the JSONL serialization. Raw primary/context
text and free-form metadata are not copied into the ledger. The caller owns the
source archive and joins it to fingerprints and source identifiers.

The SQLite WAL ledger uses short transactions to claim a decision identity and
commit its result. Inference runs outside a database transaction, so independent
identities and cached reads need not wait for another model call. Each worker owns
its connection. Claims expire to permit recovery after process failure; ownership
is rechecked before commit so an expired worker cannot publish a late result.
Computation may repeat after a crash or lease expiry. There is no background queue:
the caller retains input and schedules retries with backoff. Separate database
files do not provide distributed deduplication.

## Product boundary

Context records keep their own author and relationship. Only the primary text receives the relevance verdict. Suppression changes a proposed feed disposition; it never deletes archive data or publishes directly.

Metadata is adapter-reported data, not verification. Eight compact flags/enums/counts
may enter model context; deterministic gates can route incomplete, deleted,
retracted or HTML source records directly to review. Other metadata is validated
and fingerprinted for provenance, with its exact role documented in [Parameters](PARAMETERS.md).

GitHub trailer removal only recognizes a final paragraph entirely made of known
trailers, with a preceding nonempty message and paragraph separator. Subject/body
examples and mixed or ambiguous blocks remain intact. Bookkeeping recognition
uses exact formats; arbitrary bracket suffixes are not whitelisted.

Source URLs are references only and are never fetched. The package does not prove
source authenticity, verify facts, validate commit signatures, extract entities,
cluster narratives or implement a connection to external collectors. These require
separate, explicitly tested application components.

Probability is evaluated per task and must be calibrated against reviewed data.
The runtime keeps upstream entropy-based confidence separate from maximum answer
probability. Token budgets are checked with the selected tokenizer before inference.
