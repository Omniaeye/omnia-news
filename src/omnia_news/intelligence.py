# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Per-task news assessments with stable inference reuse and independent policy gates."""

from copy import deepcopy
from datetime import datetime, timezone
import json
import re
from .assessment_tasks import DEFAULT_THRESHOLDS, TASKS, VERSION
from .contracts import normalize, timestamp
from .identity import publication_identity, content_version
from .temporal import observe
from .reference_index import index as index_references
from .relevance_policy import checks as relevance_checks, decide as feed_decision
from ._engine.ledger import digest, probability


def references(item):
    result = []
    for scope, text in [("primary", item["text"]), *[(c["id"], c["text"]) for c in item["context"]]]:
        for kind, pattern in [
            ("url", r'https://[^\s<>"\]]+'),
            ("handle", r"(?<!\w)@[A-Za-z0-9_]{1,30}\b"),
            ("ticker", r"(?<!\w)\$[A-Za-z][A-Za-z0-9_]{1,14}\b"),
            ("evm_address", r"\b0x[a-fA-F0-9]{40}\b"),
            ("base58_candidate", r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"),
        ]:
            for match in re.finditer(pattern, text):
                result.append(
                    {
                        "kind": kind,
                        "value": match[0].rstrip(".,;)"),
                        "scope": scope,
                        "start": match.start(),
                        "end": match.end(),
                        "status": "observed_reference",
                    }
                )
    return result


def assess(event, ledger, backend, *, thresholds=None, max_bytes=1048576, prior_assessment=None):
    item = normalize(event, max_bytes, max_text=200000)
    if prior_assessment is not None:
        from .casebook import validate_result
        from .assessment_tasks import catalog
        validate_result(prior_assessment)
        if prior_assessment.get("schema") != "omnia.news.intelligence.v1":
            raise ValueError("legacy_assessment_required")
        if prior_assessment["source_input_sha256"] != digest(event):
            raise ValueError("prior_source_mismatch")
        if prior_assessment.get("assessment_id") != digest({k: v for k, v in prior_assessment.items() if k != "assessment_id"}):
            raise ValueError("prior_assessment_hash_mismatch")
        old_tasks = catalog(prior_assessment["schema"])
        if any(task != old_tasks[name] for name, task in TASKS.items() if name != "relevance"):
            raise ValueError("prior_task_catalog_changed")
    identity = publication_identity(item["platform"], item["url"], item["id"])
    version = content_version(item)
    limits = dict(DEFAULT_THRESHOLDS)
    if thresholds is not None and not isinstance(thresholds, dict):
        raise ValueError("threshold_object_required")
    if thresholds:
        if set(thresholds) - set(TASKS):
            raise ValueError("unknown_task_threshold")
        limits.update(thresholds)
    for value in limits.values():
        probability(value)
    state = {
        "primary_author": item["author"],
        "primary_text": item["text"],
        "context": [{"author": c["author"], "relation": c["relation"], "text": c["text"]} for c in item["context"]],
    }
    tasks = {}
    groups = []
    for scope, value, questions in (
        ("primary_text", {"text": item["text"]}, {"relevance": TASKS["relevance"]}),
        ("attributed_context", state, {name: task for name, task in TASKS.items() if name != "relevance"}),
    ):
        if scope == "attributed_context" and prior_assessment is not None:
            groups.append(("legacy_attributed_context", None, [{} for _ in prior_assessment["inference"]], questions))
            continue
        routed_item = {**item, "context": []} if scope == "primary_text" else item
        model = backend.for_event(routed_item) if hasattr(backend, "for_event") else backend
        chunks = model.prepare(value, questions) if hasattr(model, "prepare") else [value]
        if not isinstance(chunks, list) or not 1 <= len(chunks) <= 256 or any(not isinstance(c, dict) for c in chunks):
            raise ValueError("invalid_model_segments")
        groups.append((scope, model, chunks, questions))
    calls = []
    event_type = item["metadata"].get("source_event_type")
    status_labels = {"social_repost": "reposted", "social_pin": "pinned", "social_unpin": "unpinned",
                     "social_reply": "replied", "social_quote": "quoted"}
    source_issues = [
        name
        for name, active in {
            "incomplete_text": item["metadata"].get("is_truncated"),
            "source_limit_reached": item["metadata"].get("source_text_at_limit"),
            "deleted_source": item["metadata"].get("source_deleted") or event_type == "social_delete",
            "retraction": item["metadata"].get("record_type") == "retraction",
            "html_requires_adapter": item["metadata"].get("content_format") == "html",
            "empty_primary": not item["text"].strip(),
            "segmented_input": any(len(group[2]) != 1 for group in groups),
            "missing_parent_context": item["metadata"].get("context_missing"),
            "status_only_primary": event_type in status_labels and item["text"].strip().casefold() == status_labels[event_type],
            "publication_after_observation": bool(item.get("published_at"))
            and timestamp(item["published_at"]) > timestamp(item["observed_at"]),
        }.items()
        if active
    ]
    for scope, model, chunks, questions in groups:
        if scope == "legacy_attributed_context":
            calls.extend({**deepcopy(call), "scope": scope, "task_ids": list(questions),
                          "segment": index, "segment_count": len(chunks), "cache_hit": True,
                          "reuse_kind": "prior_assessment", "reused_from": prior_assessment["assessment_id"]}
                         for index, call in enumerate(prior_assessment["inference"]))
            continue
        for index, chunk in enumerate(chunks):
            request = {
                "id": "news:" + digest({"key": identity["key"],
                    "version": digest({"author": item["author"], "text": item["text"]}) if scope == "primary_text" else version,
                    "scope": scope, "segment": index}),
                "state": chunk,
                "questions": deepcopy(questions),
                "evidence": [identity["canonical_url"]] + ([] if scope == "primary_text" else [c["url"] for c in item["context"]]),
            }
            try:
                call = ledger.decide(
                    request, model, manifest={**model.manifest(), "task_version": VERSION, "input_scope": scope},
                    min_probability=0.0, max_bytes=max_bytes
                )
            except Exception as exc:
                call = {"status": "failed", "error_type": type(exc).__name__}
            calls.append({**call, "scope": scope, "task_ids": list(questions), "segment": index, "segment_count": len(chunks)})
    for name in TASKS:
        applicable = [call for call in calls if name in call["task_ids"]]
        answers = [c["answers"][name] for c in applicable if "answers" in c]
        answer = answers[0] if len(answers) == 1 and len(applicable) == 1 else None
        status = "failed" if len(answers) != len(applicable) else "needs_review"
        if answer is not None and not source_issues:
            status = (
                "insufficient"
                if answer["choice"] == "insufficient"
                else "accepted"
                if answer["answer_probability"] >= limits[name]
                else "needs_review"
            )
        tasks[name] = {
            "status": status,
            "answer": answer,
            "segment_answers": answers if answer is None else [],
            "threshold": limits[name],
            "calibration": "unfitted_policy_threshold",
        }
    inspected = relevance_checks(item, source_issues)
    relevance = tasks["relevance"]
    review_reasons = []
    if inspected["short_social_fragment"]:
        review_reasons.append("short_social_fragment")
    if inspected["format_reason"] and relevance["answer"] and relevance["answer"]["choice"] == "informative":
        review_reasons.append("source_format_conflicts_with_native_answer")
    if review_reasons and relevance["status"] != "failed":
        relevance["status"] = "needs_review"
    relevance["review_reasons"] = review_reasons
    result = {
        "schema": VERSION,
        "source": "omnia.news",
        "source_event_type": event_type,
        "identity": identity,
        "content_version": version,
        "source_input_sha256": digest(event),
        "source_url": item["url"],
        "author": item["author"],
        "attribution": {
            "author_reference": item["author"],
            "identity_kind": item["metadata"].get("author_identity_kind", "caller_supplied"),
            "source_actor": item["metadata"].get("source_actor"),
            "independently_verified": False,
        },
        "observed_at": item["observed_at"],
        "published_at": item.get("published_at"),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "language": item.get("language"),
        "measurements": {
            "characters": len(item["text"]),
            "utf8_bytes": len(item["text"].encode("utf-8")),
            "context_records": len(item["context"]),
            "segments": sum(len(group[2]) for group in groups),
            **{
                k: v
                for k, v in item["metadata"].items()
                if k in {"author_followers", "view_count", "like_count", "reply_count", "repost_count"}
            },
        },
        "references": references(item),
        "source_issues": source_issues,
        "tasks": tasks,
        "relevance_checks": inspected,
        "feed_decision": feed_decision(relevance, inspected),
        "recurrence": observe(ledger, identity["key"], item),
        "inference": calls,
        "execution_authorized": False,
        "status": "failed" if any(c.get("status") == "failed" for c in calls) else "completed",
    }
    result = ledger.record_assessment(result)
    ledger.db.execute(
        "CREATE TABLE IF NOT EXISTS news_index (identity TEXT, version TEXT, observed TEXT, assessment TEXT, PRIMARY KEY(identity,version))"
    )
    ledger.db.execute(
        "INSERT INTO news_index VALUES (?,?,?,?) ON CONFLICT(identity,version) DO UPDATE SET observed=excluded.observed,assessment=excluded.assessment WHERE excluded.observed>=news_index.observed",
        (
            identity["key"],
            version,
            timestamp(item["observed_at"]).isoformat(timespec="microseconds"),
            json.dumps(result, ensure_ascii=False, allow_nan=False),
        ),
    )
    ledger.db.commit()
    index_references(ledger, result, item)
    return result


def lookup(ledger, identity, version=None):
    """Return stored evaluations without invoking inference or requesting external URLs."""
    exists = ledger.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='news_index'").fetchone()
    if not exists:
        return None
    query = "SELECT assessment FROM news_index WHERE identity=?"
    args = [identity]
    if version:
        query += " AND version=?"
        args.append(version)
    query += " ORDER BY observed DESC LIMIT 1"
    row = ledger.db.execute(query, args).fetchone()
    return json.loads(row[0]) if row else None
