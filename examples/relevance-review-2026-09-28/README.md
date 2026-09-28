# Relevance review

[Source window](../news-window-2026-09-28-v2/README.md) | [All examples](../README.md)

## Scope

Relevance evaluates whether the primary text communicates information. It does not verify a claim, predict market impact or authorize publication.

The same 500 source records were assessed with a short primary-text request. Other task answers retain their original native receipts. The acceptance threshold remains 0.8.

| Outcome | Publications |
| --- | ---: |
| Keep | 64 |
| Suppress exact operational formats | 46 |
| Review | 390 |

## What changed

- Primary-text relevance has its own request and cache key. A quote or author field cannot provide its answer.
- Source completeness remains a separate check. Long inputs preserve every segment.
- Full-message format matching identifies generated benchmark receipts, preview deployment records and merge-only bookkeeping. A substantive body prevents those matches.
- Short social reactions require context review. A model noise label alone cannot suppress free-form text.
- Native labels and probabilities are never replaced by the source-format decision.

## Reviewed records

46 source records were reviewed by the assistant against an explicit rubric. Six keep decisions and five format-based suppressions matched that review; the remaining 35 required review. Labels and every outcome are retained below.

This is a diagnostic review, not independent human ground truth. The policy was refined after error inspection. These counts do not establish calibrated probabilities or broad precision; no accuracy percentage is claimed for the full 500-source window.

| Source | Reference | Native label | Probability | Task gate | Feed action | Reason |
| --- | --- | --- | ---: | --- | --- | --- |
| [Source 40](https://x.com/i/status/2103965182942654690) | noise | noise | 0.6429 | needs_review | review | source_requires_review |
| [Source 50](https://x.com/i/status/2104673500262814176) | noise | noise | 0.7706 | needs_review | review | source_requires_review |
| [Source 60](https://x.com/i/status/2104673285216854075) | noise | noise | 0.7706 | needs_review | review | source_requires_review |
| [Source 70](https://x.com/i/status/2104673000511713642) | informative | informative | 0.5097 | needs_review | review | below_probability_threshold |
| [Source 80](https://github.com/NVIDIA/NemoClaw/commit/a36e41287ea9e93988d4b588693fefa05b01730c) | informative | informative | 0.7809 | needs_review | review | below_probability_threshold |
| [Source 90](https://github.com/aws/agentcore-cli/commit/bb2fa429725058f6b5a42fc8c5d6c4bc9f8deff4) | informative | informative | 0.8927 | accepted | keep | informative_primary_text |
| [Source 100](https://x.com/i/status/2104662434585661949) | insufficient | informative | 0.6235 | needs_review | review | below_probability_threshold |
| [Source 110](https://github.com/google/gvisor/commit/8dc6dbe24f770ff70273a8fb803acbcb3aa715a6) | informative | informative | 0.7128 | needs_review | review | below_probability_threshold |
| [Source 120](https://x.com/i/status/2104672331687940478) | informative | noise | 0.7639 | needs_review | review | unverified_noise |
| [Source 130](https://github.com/NVIDIA/Model-Optimizer/commit/e948fc5108214a2f9a0aa0d1939b47f7f26a90db) | informative | informative | 0.7142 | needs_review | review | source_requires_review |
| [Source 140](https://x.com/i/status/2104672029706453091) | insufficient | informative | 0.5971 | needs_review | review | below_probability_threshold |
| [Source 150](https://github.com/microsoft/sarif-website/commit/10af6dcc390de5b01e2b01e7b1c612450e1437a3) | noise | informative | 0.6635 | needs_review | suppress | operational_record |
| [Source 160](https://github.com/google/tpu-sync/commit/9815fb57a21a88be30cbc29e8bb1017bffec9dd5) | informative | informative | 0.5202 | needs_review | review | below_probability_threshold |
| [Source 170](https://x.com/i/status/2104671696498176408) | insufficient | informative | 0.6588 | needs_review | review | below_probability_threshold |
| [Source 180](https://x.com/i/status/2104671513412878630) | informative | informative | 0.8829 | accepted | keep | informative_primary_text |
| [Source 190](https://github.com/ROCm/TheRock/commit/ae7339c6f4ce1a00c570199af8ead62db792cb66) | noise | informative | 0.55 | needs_review | suppress | operational_record |
| [Source 200](https://x.com/i/status/2104671186563313828) | informative | informative | 0.7213 | needs_review | review | below_probability_threshold |
| [Source 210](https://x.com/i/status/2104671033873609005) | insufficient | informative | 0.8168 | needs_review | review | source_requires_review |
| [Source 220](https://github.com/NVIDIA/SkillSpector/commit/325d4de3da7bd07f2e6f831a1bc8ea2a9f2b4414) | informative | informative | 0.7776 | needs_review | review | below_probability_threshold |
| [Source 230](https://github.com/ROCm/TheRock/commit/fcbf37c6cfa38db2226fc86f3b8c083f0a9c2bb5) | informative | noise | 0.6323 | needs_review | review | unverified_noise |
| [Source 240](https://github.com/facebook/astryx/commit/1780c424935f816eae4bb933c3be4017b352d292) | noise | informative | 0.5586 | needs_review | suppress | operational_record |
| [Source 250](https://github.com/aws/agentcore-cli/commit/bb3fcd303cd05dbe9c374efa623deeedc51c6d43) | informative | informative | 0.7287 | needs_review | review | below_probability_threshold |
| [Source 260](https://www.fool.com/investing/2026/09/28/not-nvidia-not-amd-broadcoms-custom-silicon-busine/) | informative | informative | 0.8324 | needs_review | review | source_requires_review |
| [Source 270](https://github.com/facebook/astryx/commit/1bebbe2590fe810dd4dbdf2586ea3189c606fe09) | noise | informative | 0.797 | needs_review | suppress | operational_record |
| [Source 280](https://x.com/i/status/2104669979887181921) | informative | informative | 0.8664 | accepted | keep | informative_primary_text |
| [Source 290](https://x.com/i/status/2104669846181159029) | informative | informative | 0.8033 | accepted | keep | informative_primary_text |
| [Source 300](https://x.com/i/status/2104669685283520719) | noise | noise | 0.7706 | needs_review | review | source_requires_review |
| [Source 310](https://x.com/i/status/2104669481050239464) | informative | informative | 0.5787 | needs_review | review | below_probability_threshold |
| [Source 320](https://x.com/i/status/2104597137170252114) | informative | informative | 0.7076 | needs_review | review | below_probability_threshold |
| [Source 330](https://x.com/i/status/2104669240225677473) | noise | noise | 0.6632 | needs_review | review | short_social_fragment |
| [Source 340](https://x.com/i/status/2104668957521391772) | noise | noise | 0.7706 | needs_review | review | source_requires_review |
| [Source 350](https://finance.yahoo.com/markets/stocks/articles/costco-just-got-reality-check-202532104.html) | informative | informative | 0.8567 | needs_review | review | source_requires_review |
| [Source 360](https://github.com/microsoft/agent-framework-go/commit/6583e0a0145167d92ffe12780b85cd74215425bb) | informative | informative | 0.6948 | needs_review | review | below_probability_threshold |
| [Source 370](https://x.com/i/status/2104668451633512850) | informative | informative | 0.5131 | needs_review | review | below_probability_threshold |
| [Source 380](https://github.com/facebook/rebalancer/commit/0b2b5d82e85fda7db1ee0e4b358400914c0fe183) | informative | informative | 0.7324 | needs_review | review | below_probability_threshold |
| [Source 390](https://github.com/microsoft/garnet/commit/b45278cde6c1279daccc65ce523efa905b57e818) | noise | informative | 0.7898 | needs_review | suppress | operational_record |
| [Source 400](https://github.com/aws/aws-sdk-java-v2/commit/bd3cb362b8a91daf5f58e5bd766c50545313335c) | insufficient | noise | 0.5339 | needs_review | review | unverified_noise |
| [Source 410](https://x.com/i/status/2104667872484278727) | noise | noise | 0.7706 | needs_review | review | source_requires_review |
| [Source 420](https://x.com/i/status/2104648323479326755) | informative | informative | 0.8331 | accepted | keep | informative_primary_text |
| [Source 430](https://x.com/i/status/2104667495701647858) | informative | informative | 0.5754 | needs_review | review | below_probability_threshold |
| [Source 440](https://x.com/i/status/2104667472083173739) | informative | informative | 0.5153 | needs_review | review | below_probability_threshold |
| [Source 450](https://x.com/i/status/2104667354861019161) | informative | informative | 0.8273 | accepted | keep | informative_primary_text |
| [Source 460](https://x.com/i/status/2104666854794924263) | noise | noise | 0.694 | needs_review | review | source_requires_review |
| [Source 470](https://github.com/google/meridian/commit/c56865c39a48e1dbf2fc0af4b93e2780bba7bf84) | informative | informative | 0.5561 | needs_review | review | below_probability_threshold |
| [Source 480](https://github.com/facebook/idb/commit/195602fc9e8bfe92fd7d60f158870263a10032fe) | informative | informative | 0.5471 | needs_review | review | source_requires_review |
| [Source 490](https://x.com/i/status/2104666793193423017) | informative | informative | 0.6225 | needs_review | review | below_probability_threshold |

## Reproduce

```bash
python tools/review_relevance.py examples/news-window-2026-09-28-v2 examples/relevance-review-2026-09-28/labels.json --output var/relevance-review.json
```

The command verifies casebook hashes and source identity before recomputing this review. It performs no model or network calls.

[Review labels](labels.json) | [Complete outcomes](review.json) | [Acceptance policy](../../docs/CONFIDENCE.md)

## Boundaries

The other nine tasks were not recalibrated in this change. Request-versus-announcement interpretation remains separate from relevance. The 390 review decisions are not counted as approvals or silently dropped. Public feed behavior and trading execution are unchanged.
