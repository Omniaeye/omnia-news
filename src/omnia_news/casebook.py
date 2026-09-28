# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Source-indexed outcome records with native probabilities and file integrity checks."""

import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
from .assessment_tasks import TASKS
from .batch import summarize, write_json
from ._engine.ledger import digest, probability, validate_answers


def validate_result(result):
    if result.get("schema") == "omnia.news.batch-failure.v1" and result["status"] == "failed":
        return
    if set(result["tasks"]) != set(TASKS):
        raise ValueError("task_coverage_mismatch")
    order = [(key, list(task["criteria"])) for key, task in TASKS.items()]
    question_hash = digest({"questions": TASKS, "order": order})
    for call in result["inference"]:
        if "answers" not in call:
            if call.get("status") != "failed":
                raise ValueError("missing_native_answers")
            continue
        if call["questions_sha256"] != question_hash:
            raise ValueError("native_question_catalog_mismatch")
        checked = validate_answers(call, TASKS)
        for key, answer in call["answers"].items():
            if answer.get("answer_probability") != checked[key]["answer_probability"]:
                raise ValueError("native_probability_mismatch")
            if "model_confidence" in answer:
                probability(answer["model_confidence"])
    for name, task in result["tasks"].items():
        probability(task["threshold"])
        answer = task["answer"]
        native = [c["answers"][name] for c in result["inference"] if "answers" in c]
        if answer is None:
            if task["status"] == "accepted":
                raise ValueError("missing_accepted_answer")
            if task["segment_answers"] != native:
                raise ValueError("native_segment_answer_mismatch")
            continue
        values = answer["probabilities"]
        if set(values) != set(TASKS[name]["criteria"]):
            raise ValueError("answer_labels_mismatch")
        for value in values.values():
            probability(value)
        if abs(sum(values.values()) - 1) > len(values) * 0.000051:
            raise ValueError("invalid_distribution")
        if abs(values[answer["choice"]] - max(values.values())) > 0.00011:
            raise ValueError("invalid_answer_choice")
        if abs(answer["answer_probability"] - max(values.values())) > 0.00011:
            raise ValueError("invalid_answer_probability")
        if task["status"] == "accepted" and (
            result["source_issues"] or answer["choice"] == "insufficient" or answer["answer_probability"] < task["threshold"]
        ):
            raise ValueError("invalid_accepted_answer")
        if len(native) != 1 or native[0] != answer:
            raise ValueError("native_answer_mismatch")


def verify(directory):
    root = Path(directory).resolve()
    manifest = json.loads((root / "manifest.json").read_bytes())
    if manifest.get("schema") != "omnia.news.casebook.v1":
        raise ValueError("unsupported_casebook_schema")
    actual_files = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p != root / "manifest.json"}
    if actual_files != set(manifest["files"]):
        raise ValueError("casebook_file_set_mismatch")
    for name, expected in manifest["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("invalid_casebook_path")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("casebook_hash_mismatch")
    summary = json.loads((root / "summary.json").read_bytes())
    records = [json.loads(path.read_bytes())["assessment"] for path in sorted((root / "records").glob("*.json"))]
    for result in records:
        validate_result(result)
    if summarize(records) != summary:
        raise ValueError("summary_record_mismatch")
    if json.loads((root / "tasks.json").read_bytes()) != TASKS:
        raise ValueError("question_catalog_mismatch")
    return {"files_verified": len(manifest["files"]), "records": summary["records"]}


def publish(events, results, output):
    root = Path(output)
    if root.exists():
        raise FileExistsError(root)
    if len(events) != len(results):
        raise ValueError("batch_coverage_mismatch")
    root.mkdir(parents=True)
    (root / "records").mkdir()
    rows = []
    table = [
        "# OMNIA News assessments",
        "",
        "Each record links the publication to its evaluation, per-task probabilities and acceptance policy.",
        "",
        "| Publication | Platform | Evaluation | Record |",
        "| --- | --- | --- | --- |",
    ]
    seen = set()
    for event, result in zip(events, results):
        validate_result(result)
        if result["source_input_sha256"] != digest(event):
            raise ValueError("source_assessment_mismatch")
        identifier = digest(event["id"])[:24]
        if identifier in seen:
            raise ValueError("duplicate_publication")
        seen.add(identifier)
        # Original full text remains in the caller's source archive. No credential-bearing payloads are exported.
        packet = {
            "publication": {k: event.get(k) for k in ("id", "platform", "url", "author", "observed_at", "published_at")},
            "assessment": result,
        }
        write_json(root / "records" / (identifier + ".json"), packet)
        safe_url = html.escape(event["url"], quote=True)
        table.append(
            f'| <a href="{safe_url}">Open source</a> | {event["platform"]} | {result["status"]} | [Inspect](records/{identifier}.md) |'
        )
        detail = [
            f"# {event['platform'].upper()} publication",
            "",
            f'<a href="{safe_url}">Original publication</a> · [Complete assessment]({identifier}.json) · [Batch index](../README.md)',
            "",
            f"Observed: {html.escape(str(event['observed_at']))}",
            "",
            "| Dimension | Answer | Probability | Acceptance threshold | Status |",
            "| --- | --- | ---: | ---: | --- |",
        ]
        for task, value in result.get("tasks", {}).items():
            answer = value["answer"] or {}
            chance = f"{answer['answer_probability']:.4f}" if answer else "See segments"
            detail.append(f"| {task} | {answer.get('choice', 'Segmented')} | {chance} | {value['threshold']:.2f} | {value['status']} |")
            rows.append(
                {
                    "publication": identifier,
                    "task": task,
                    "answer": answer.get("choice"),
                    "probability": answer.get("answer_probability"),
                    "model_confidence": answer.get("model_confidence"),
                    "threshold": value["threshold"],
                    "status": value["status"],
                    "source_url": event["url"],
                }
            )
        detail += ["", "## Source measurements", "", "| Measurement | Value |", "| --- | ---: |"]
        for name, value in result.get("measurements", {}).items():
            detail.append(f"| {name} | {value} |")
        detail += [
            "",
            "## Evidence and context",
            "",
            "Source issues: " + (", ".join(result.get("source_issues", [])) or "None recorded."),
            "",
            "The JSON record preserves reference scope, native distributions, model revision, input hashes and cached-inference receipts.",
            "",
            "A configured acceptance threshold is distinct from measured accuracy.",
        ]
        (root / "records" / (identifier + ".md")).write_text("\n".join(detail) + "\n", encoding="utf-8", newline="\n")
    summary = summarize(results)
    write_json(root / "summary.json", summary)
    write_json(root / "tasks.json", TASKS)
    with (root / "assessments.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["publication", "task", "answer", "probability", "model_confidence", "threshold", "status", "source_url"],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {k: "'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v for k, v in row.items()}
            )
    overview = [
        "## Batch results",
        "",
        f"{summary['records']} publications. {summary['native_answers']} native answers including attributed text segments.",
        "",
        "| Dimension | Accepted | Review | Insufficient | Failed |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for task, metric in summary["tasks"].items():
        counts = metric["statuses"]
        overview.append(
            "| " + task + " | " + " | ".join(str(counts.get(k, 0)) for k in ("accepted", "needs_review", "insufficient", "failed")) + " |"
        )
    overview += [
        "",
        "Acceptance is a configured probability gate. Task accuracy requires an independent labeled reference set.",
        "",
        "News excerpts retain their incomplete-source marker. Long inputs retain segment answers; they are not silently merged.",
        "",
        "[Assessment table](assessments.csv) · [Question catalog](tasks.json) · [Summary](summary.json)",
        "",
    ]
    (root / "README.md").write_text("\n".join(table[:3] + [""] + overview + table[3:]) + "\n", encoding="utf-8", newline="\n")
    write_json(
        root / "manifest.json",
        {
            "schema": "omnia.news.casebook.v1",
            "input_sha256": digest(events),
            "files": {
                p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()
            },
        },
    )
    return verify(root)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    args = parser.parse_args()
    print(json.dumps(verify(args.directory)))


if __name__ == "__main__":
    main()
