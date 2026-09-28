# Confidence and acceptance

OMNIA records a decision separately from the policy that consumes it.

| Field | Meaning |
| --- | --- |
| `probabilities` | Native distribution across the supplied labels |
| `answer_probability` | Maximum probability in that distribution |
| `model_confidence` | Provider-native confidence statistic, when returned |
| `threshold` | Product policy applied to one task |
| `status` | Accepted, review, insufficient or failed |
| `calibration` | Provenance of the acceptance configuration |

The current intelligence tasks use `choice`. The integration also validates `score` and `noul` for the legacy runtime. A noul is a yes-probability; it is not a severity score.

LAYA confidence for choice/score measures normalized entropy. TypeSafe's provider confidence is a separate statistic. OMNIA does not transfer a provider confidence threshold between backends. The native probability distribution is retained for inspection.

## Per-task gates

Each task initially uses an unfitted probability threshold of 0.8. A result above that threshold is accepted by the configured policy; it is not a guarantee of factual correctness or task accuracy. A response selecting `insufficient` remains insufficient even at high probability.

Incomplete text, deleted records, missing parent context, retractions and segmented inputs require review at the source level. Status-only social events such as a bare "Reposted" cannot inherit accepted claims from quoted context. A publication timestamp after its observation also requires review. Backend failures remain failed. Results preserve answers even when they cannot be used automatically.

Threshold changes do not repeat inference in the intelligence path. The underlying ledger is called with a structural floor of zero; consumers must use `tasks.*.status`, not `inference.*.status`, for product acceptance. Inference records retain the exact policy used when they were generated.

Feed eligibility additionally uses `feed_decision`. Exact full-message operational
formats cannot be promoted by a high model probability. Native noise votes do not
suppress free-form text. These source checks do not alter the native distribution
or manufacture a confidence value. Short social fragments below 32 characters,
without a URL, cashtag or EVM-shaped reference, require review.

The [relevance review](../examples/relevance-review-2026-09-28/README.md) preserves
the complete follow-up window and assistant-reviewed examples. Its policy checks
are not a fitted probability calibration or an independent accuracy benchmark.

## Calibration procedure

1. Freeze publication IDs before looking at answers.
2. Label the task independently, using the complete source and attributable context.
3. Separate calibration records from the held-out evaluation set. Group related publications to avoid leakage.
4. Fit a supported calibration transformation using calibration data only.
5. Measure precision and coverage at each candidate threshold on held-out records.
6. Report performance per task, label, language and source type. A small slice remains an uncertain estimate.
7. Version the model revision, numeric precision, question catalog and calibration artifact together.

Record ECE and Brier score when a labeled probability evaluation is available. Record precision/coverage for the actual acceptance policy. Missing labels never count as correct answers. The first 500-publication run reports response distributions and operational coverage; unlabeled results do not establish accuracy.

## References

- [TypeSafe confidence](https://docs.typesafe.ai/confidence)
- [TypeSafe typed primitives](https://docs.typesafe.ai/primitives)
- [LAYA evaluation harness](https://github.com/NandhaKishorM/laya/blob/main/docs/evals.md)
- [Guo et al., On Calibration of Modern Neural Networks](https://arxiv.org/abs/1706.04599)
