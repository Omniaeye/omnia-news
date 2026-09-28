# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Indexed source references with explicit author, primary and quoted scopes."""

import json

KINDS = {"publication_url", "author_id", "author_handle", "url", "handle", "ticker", "evm_address", "base58_candidate"}


def normalized(kind, value):
    if kind not in KINDS or not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise ValueError("invalid_reference")
    return value.lstrip("@").casefold() if kind in {"handle", "author_handle"} else value.lower() if kind == "evm_address" else value


def index(ledger, result, item):
    ledger.db.execute(
        "CREATE TABLE IF NOT EXISTS news_references (kind TEXT,value TEXT,identity TEXT,version TEXT,scope TEXT,PRIMARY KEY(kind,value,identity,version,scope))"
    )
    entries = [("publication_url", result["identity"]["canonical_url"], "source"), ("author_id", item["author"], "author")]
    if item["metadata"].get("author_handle"):
        entries.append(("author_handle", item["metadata"]["author_handle"], "author"))
    entries += [(r["kind"], r["value"], r["scope"]) for r in result["references"]]
    for kind, value, scope in entries:
        ledger.db.execute(
            "INSERT OR IGNORE INTO news_references VALUES (?,?,?,?,?)",
            (kind, normalized(kind, value), result["identity"]["key"], result["content_version"], scope),
        )
    ledger.db.commit()


def find(ledger, kind, value, *, limit=50, scope=None):
    """Search stored publications only. A reference match is not an asset endorsement."""
    value = normalized(kind, value)
    if type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError("invalid_reference_limit")
    if not ledger.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='news_references'").fetchone():
        return []
    query = (
        "SELECT DISTINCT n.assessment,r.scope FROM news_references r JOIN news_index n "
        "ON n.identity=r.identity AND n.version=r.version WHERE r.kind=? AND r.value=?"
    )
    args = [kind, value]
    if scope is not None:
        query += " AND r.scope=?"
        args.append(scope)
    query += " ORDER BY n.observed DESC LIMIT ?"
    args.append(limit)
    return [{"scope": row[1], "assessment": json.loads(row[0])} for row in ledger.db.execute(query, args).fetchall()]
