# Persistent news assessments

Status: accepted for the library implementation.

## Decision

Keep the compatible feed filter and add a separate intelligence path. Store native
inference independently of per-task acceptance policy. Index assessments by stable
publication identity and content version. Use explicit references to supply cached
news context to a trading consumer.

## Reasons

The original filter answers one narrow informativity question. Expanding that
question into a combined importance/trading judgment would change its behavior
and make failures difficult to isolate. Independent tasks permit separate review,
thresholds and future calibration without repeating unchanged model inference.

A source reference cannot prove affiliation. Quoted authors, mentions and caller
supplied token links therefore retain different relationship scopes. Changing an
engagement count does not invalidate the content assessment.

## Consequences

The ledger and indexes are local SQLite application state. Each worker owns a
connection. Caller-side orchestration retains source archives, schedules retries
and decides whether to publish or act. Long documents retain attributed segment
answers and require document-level review. No confidence score is treated as a
probability of investment return.
