# Validation

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
