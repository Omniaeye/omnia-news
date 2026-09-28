# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Exact-content recurrence over the retained assessment archive."""

from datetime import timedelta
from .contracts import timestamp
from ._engine.ledger import digest


def observe(ledger, identity, item):
    ledger.db.execute(
        "CREATE TABLE IF NOT EXISTS news_occurrence_history (identity TEXT,content TEXT,author TEXT,platform TEXT,observed TEXT,PRIMARY KEY(identity,content))"
    )
    ledger.db.execute("CREATE INDEX IF NOT EXISTS news_occurrence_history_content ON news_occurrence_history(content,observed)")
    content = digest(" ".join(item["text"].split()).casefold())
    observed = timestamp(item["observed_at"])
    known = ledger.db.execute("SELECT observed FROM news_occurrence_history WHERE identity=? AND content=?", (identity, content)).fetchone()
    prior = ledger.db.execute(
        "SELECT identity,author,platform,observed FROM news_occurrence_history WHERE content=? AND identity<>?", (content, identity)
    ).fetchall()
    bounded = [r for r in prior if observed - timedelta(hours=6) <= timestamp(r[3]) <= observed]
    ledger.db.execute(
        "INSERT INTO news_occurrence_history VALUES (?,?,?,?,?) ON CONFLICT(identity,content) DO UPDATE SET author=excluded.author,platform=excluded.platform,observed=excluded.observed WHERE excluded.observed<news_occurrence_history.observed",
        (identity, content, item["author"], item["platform"], observed.isoformat(timespec="microseconds")),
    )
    ledger.db.commit()
    return {
        "method": "normalized_exact_text",
        "text_sha256": content,
        "window_seconds": 21600,
        "distinct_publications": len(bounded) + 1,
        "distinct_author_references": len({(r[2], r[1]) for r in bounded} | {(item["platform"], item["author"])}),
        "author_basis": "source_supplied_identity_not_verified_people",
        "platforms": sorted({r[2] for r in bounded} | {item["platform"]}),
        "novelty": "previously_observed" if known else "repeated_in_archive" if bounded else "first_in_archive",
        "baseline": "local_assessment_archive_only",
    }
