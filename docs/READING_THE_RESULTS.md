# Reading the news records

The September 28 casebook preserves every outcome in the selected source window.
Each publication has a source reference, content hash, native response, probability
distribution and an application-level acceptance result.

## Three separate questions

1. **What did the source contain?** Inspect its URL, event type, author basis,
   available context and completeness flags.
2. **What did LAYA answer?** Inspect the exact task, selected label and native
   distribution. A probability belongs to that classification task.
3. **What may a consumer use?** Inspect `tasks.*.status`, source issues, freshness
   and the relationship to the asset. A stored answer does not authorize an order.

## Source inspection notes

These notes compare captured source content with stored answers. They are qualitative
checks, not a labeled accuracy benchmark.

| Record | Native observation | Interpretation |
| --- | --- | --- |
| [Technical commit](../examples/news-window-2026-09-28/records/1d95a206b51fd1ab2221aeee.md) | `technical` at 0.9975; relevance selects `insufficient` at 0.4105 | The event category and feed relevance are separate judgments. Recognizing technical content does not establish market significance. |
| [Addressed token request](../examples/news-window-2026-09-28/records/0994402fd914acc1a8c6840b.md) | `launch` at 0.9959; `announcement` at 0.9968 | The primary text asks another account to launch an asset. These labels must not be interpreted as proof that deployment occurred. Request-versus-completion needs explicit review before automatic downstream use. |
| [Reported deployment](../examples/news-window-2026-09-28/records/bedd0953049a6abb567c92dd.md) | `launch` at 0.9713; token reference selects `explicit` at 0.4029 | The source contains an address-shaped reference and reports deployment. The package extracts that reference separately; it does not verify a chain transaction or official affiliation. |
| [Repost activity](../examples/news-window-2026-09-28/records/4bb90a4ea735fc77060f6bf1.md) | The model returns an announcement label using supplied context | The primary text is only a repost status. The operational-event gate prevents the quoted claim from becoming an accepted primary-author announcement. |
| [Deleted-source activity](../examples/news-window-2026-09-28/records/06176ed40a68575df25d4314.md) | Native answers remain inspectable | The collection event marks deletion. The source gate prevents automatic consumption of those answers. |

## Confidence review

High probability can coexist with an unsuitable label. The addressed-request record
demonstrates why an acceptance threshold is not a substitute for task validation.
The complete dataset is retained, including weak answers and cases requiring review.

Before using these classifications to change publication or trading policy, label
an independent source sample, include requests and status-only events, and measure
precision and accepted coverage per task. Keep classification, source verification
and financial execution as separate decisions.

See [Confidence](CONFIDENCE.md), [Intelligence API](INTELLIGENCE.md), and the
[complete casebook](../examples/news-window-2026-09-28/README.md).
