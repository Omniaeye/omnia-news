# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Frozen source batches, native assessment receipts and complete outcome reports."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import time
from .config import Config
from .contracts import timestamp
from .feed_adapter import adapt_feed
from .intelligence import assess
from .news_runtime import RoutedNews
from ._engine.ledger import DecisionLedger, digest


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def summarize(results):
    counts = Counter(row["status"] for row in results)
    tasks = {}
    for row in results:
        for name, result in row.get("tasks", {}).items():
            entry = tasks.setdefault(name, {"statuses": Counter(), "answers": Counter()})
            entry["statuses"][result["status"]] += 1
            if result["answer"]:
                entry["answers"][result["answer"]["choice"]] += 1
                chance = result["answer"]["answer_probability"]
                band = "<0.5" if chance < 0.5 else "0.5-0.8" if chance < 0.8 else "0.8-0.95" if chance < 0.95 else ">=0.95"
                entry.setdefault("probability_bands", Counter())[band] += 1
    calls = [c for row in results for c in row.get("inference", []) if "answers" in c]
    latencies = sorted(c["inference_ms"] for c in calls if not c.get("cache_hit"))
    recorded_latencies = sorted(c["inference_ms"] for c in calls)
    return {
        "records": len(results),
        "statuses": dict(counts),
        "tasks": tasks,
        "source_issues": dict(Counter(issue for row in results for issue in row.get("source_issues", []))),
        "inference_records": len(calls),
        "native_answers": sum(len(c["answers"]) for c in calls),
        "cache_hits": sum(bool(c.get("cache_hit")) for c in calls),
        **({"feed_decisions": dict(Counter(row["feed_decision"]["action"] for row in results if "feed_decision" in row)),
            "retained_prior_calls": sum(c.get("reuse_kind") == "prior_assessment" for c in calls),
            "active_native_answers": sum(len(c.get("task_ids", c["answers"])) for c in calls)}
           if any("feed_decision" in row for row in results) else {}),
        "models": dict(
            Counter(c["engine"].get("configuration", {}).get("model", c["engine"].get("backend", "unspecified")) for c in calls)
        ),
        "recorded_p50_inference_ms": statistics.median(recorded_latencies) if recorded_latencies else None,
        "recorded_p95_inference_ms": recorded_latencies[min(len(recorded_latencies) - 1, int(len(recorded_latencies) * 0.95))]
        if recorded_latencies
        else None,
        "p50_inference_ms": statistics.median(latencies) if latencies else None,
        "p95_inference_ms": latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else None,
        "quality_accuracy": None,
        "quality_basis": "No independent labeled reference set supplied.",
        "execution_authorized": False,
    }


def run(events, output, ledger, backend, *, thresholds=None, prior_assessments=None):
    if prior_assessments is not None and len(prior_assessments) != len(events):
        raise ValueError("prior_batch_coverage_mismatch")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    freeze = {
        "schema": "omnia.news.batch.v1",
        "input_sha256": digest(events),
        "records": len(events),
        "source_ids": [event["id"] for event in events],
    }
    frozen = output / "freeze.json"
    if frozen.exists() and json.loads(frozen.read_bytes()) != freeze:
        raise ValueError("frozen_batch_mismatch")
    write_json(frozen, freeze)
    results = [None] * len(events)
    # Recurrence follows observation time; exported records retain the caller's input order.
    def chronology(entry):
        try:
            return timestamp(entry[1]["observed_at"]).timestamp(), entry[0]
        except (KeyError, TypeError, ValueError, OverflowError):
            return float("inf"), entry[0]

    started = time.monotonic()
    with (output / "results.partial.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for processed, (index, event) in enumerate(sorted(enumerate(events), key=chronology), 1):
            try:
                result = assess(event, ledger, backend, thresholds=thresholds,
                                prior_assessment=None if prior_assessments is None else prior_assessments[index])
            except Exception as exc:
                result = {
                    "schema": "omnia.news.batch-failure.v1",
                    "source_id": event["id"],
                    "source_input_sha256": digest(event),
                    "status": "failed",
                    "error_type": type(exc).__name__,
                }
            results[index] = result
            stream.write(json.dumps(result, ensure_ascii=True, allow_nan=False) + "\n")
            stream.flush()
            if processed % 25 == 0:
                print(
                    json.dumps({"processed": processed, "total": len(events), "elapsed_seconds": round(time.monotonic() - started)}),
                    flush=True,
                )
    with (output / "results.partial.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for result in results:
            stream.write(json.dumps(result, ensure_ascii=True, allow_nan=False) + "\n")
    (output / "results.partial.jsonl").replace(output / "results.jsonl")
    summary = summarize(results)
    summary["wall_seconds"] = round(time.monotonic() - started, 3)
    write_json(output / "summary.json", summary)
    files = ["freeze.json", "results.jsonl", "summary.json"]
    write_json(
        output / "manifest.json",
        {"schema": "omnia.news.batch.v1", "files": {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in files}},
    )
    return summary


def load_events(path, *, capture=False, max_records=1000):
    path = Path(path)
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("batch_file_exceeds_64_mib")
    if capture:
        rows = json.loads(path.read_bytes())["rows"]
        if not isinstance(rows, list) or len(rows) > max_records:
            raise ValueError("batch_record_limit")
        return [adapt_feed(row["payload"]) for row in rows]
    events = []
    with path.open("rb") as stream:
        while True:
            line = stream.readline(1048577)
            if not line:
                break
            if len(line) > 1048576:
                raise ValueError("input_line_exceeds_one_mib")
            if not line.strip():
                continue
            if len(events) >= max_records:
                raise ValueError("batch_record_limit")
            events.append(json.loads(line))
    return events


def main():
    parser = argparse.ArgumentParser(description="OMNIA News attributed intelligence batch")
    parser.add_argument("--input", required=True, help="Normalized source events, one JSON object per line")
    parser.add_argument("--capture", action="store_true", help="Input is an OMNIA feed capture with rows[].payload")
    parser.add_argument("--output", required=True)
    parser.add_argument("--thresholds", help="JSON object mapping task IDs to probability thresholds")
    parser.add_argument("--prior-assessments", help="Version 1 results.jsonl for the identical ordered input; reuse unchanged native tasks")
    args = parser.parse_args()
    path = Path(args.input)
    config = Config.from_env()
    events = load_events(path, capture=args.capture, max_records=config.max_records)
    ledger = DecisionLedger(config.runtime.database)
    try:
        thresholds = json.loads(Path(args.thresholds).read_bytes()) if args.thresholds else None
        prior = load_events(args.prior_assessments, max_records=config.max_records) if args.prior_assessments else None
        result = run(events, args.output, ledger, RoutedNews(config.runtime), thresholds=thresholds, prior_assessments=prior)
        print(json.dumps(result, ensure_ascii=True))
        return 1 if result["statuses"].get("failed") else 0
    finally:
        ledger.close()


if __name__ == "__main__":
    raise SystemExit(main())
