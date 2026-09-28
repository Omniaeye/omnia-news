# OMNIA News

## Intelligence delivery — 28 September 2026

Version 0.3.0 adds ten independent news judgments, publication identity, a persistent
assessment index, reference lookup, pinned language routing, explicit segmentation,
43 metadata fields, frozen batches and source-indexed casebooks. The original
feed-filter API and vendored runtime snapshot remain compatible.

Native evaluation completed locally against 500 distinct source records
selected before inference: 273 X, 219 GitHub, eight news excerpts. The original
capture remains under the private ArbitrageStocks artifacts directory. There are
170 records with supplied context, 20 missing referenced parents, 270 follower
counts and 271 observed author handles.

The native batch is a coverage and response record. No independent labeled set was
supplied; task precision must not be inferred from acceptance counts. Existing feed
routing and trading execution remain unchanged. The casebook contains 5,530 native answers across 553 text/segment evaluations.
All 553 were reused during final replay, with zero new inference records. The
software suite passed 85 tests. Query p95 was 0.6182 ms across 1,000 local read-only
queries. See docs/VALIDATION.md and docs/verification-0.3.0.json.

Relevance accepted only one record at the unfitted 0.8 threshold. Automatic feed
filtering and trading consumption require task-quality validation; no activation
was performed. Source inspection notes retain concrete high-confidence mistakes.

## Product boundaries

Source content is untrusted data. No source URL is fetched during classification.
Original collection transport provenance remains in the caller archive. Public
namespaces describe the OMNIA contract, without rewriting capture history.

Trading consumption requires an explicit publication link and network-scoped
asset. The library returns cached context; it never authorizes an order.
