# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Read-only inspection of cached publication assessments; no model configuration required."""

import argparse
import json
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from .identity import publication_identity
from .intelligence import lookup
from .reference_index import KINDS, find


def query(database, *, identity=None, url=None, platform=None, reference_kind=None, value=None, limit=50):
    path = Path(database).resolve()
    if not path.is_file():
        raise FileNotFoundError("news_database_not_found")
    if sum(v is not None for v in (identity, url, reference_kind)) != 1:
        raise ValueError("select_one_lookup_method")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        ledger = SimpleNamespace(db=connection)
        if reference_kind:
            return find(ledger, reference_kind, value, limit=limit)
        if url:
            if platform not in {"x", "github", "reddit", "youtube", "website", "news"}:
                raise ValueError("platform_required_for_url")
            identity = publication_identity(platform, url, "")["key"]
        return lookup(ledger, identity)
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description="Read OMNIA News assessments without inference")
    parser.add_argument("--database", default=os.environ.get("OMNIA_NEWS_DATABASE", "var/news/decisions.sqlite3"))
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--identity")
    selection.add_argument("--url")
    selection.add_argument("--reference-kind", choices=sorted(KINDS))
    parser.add_argument("--platform")
    parser.add_argument("--value")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    result = query(
        args.database,
        identity=args.identity,
        url=args.url,
        platform=args.platform,
        reference_kind=args.reference_kind,
        value=args.value,
        limit=args.limit,
    )
    print(json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2))


if __name__ == "__main__":
    main()
