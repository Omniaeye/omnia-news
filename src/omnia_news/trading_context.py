# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Explicit publication references connect cached news to a network-scoped asset."""

from datetime import datetime, timezone
import re
from .contracts import timestamp, source_url
from .identity import publication_identity
from .intelligence import lookup


def for_token(ledger, token, publications, *, now=None, max_age_seconds=3600):
    if set(token) != {"chain", "network_id", "contract"} or token["chain"] not in {"robinhood", "bsc", "solana"}:
        raise ValueError("network_scoped_token_required")
    if any(not isinstance(v, str) or not v.strip() for v in token.values()):
        raise ValueError("invalid_token_identity")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,96}", token["network_id"]):
        raise ValueError("invalid_network_id")
    if token["chain"] in {"bsc", "robinhood"}:
        if not re.fullmatch(r"0x[0-9a-fA-F]{40}", token["contract"]):
            raise ValueError("invalid_evm_address")
    else:
        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        value = token["contract"]
        if not 32 <= len(value) <= 44 or any(c not in alphabet for c in value):
            raise ValueError("invalid_solana_address")
        number = 0
        for char in value:
            number = number * 58 + alphabet.index(char)
        if (number.bit_length() + 7) // 8 + len(value) - len(value.lstrip("1")) != 32:
            raise ValueError("invalid_solana_address")
    if type(max_age_seconds) is not int or not 0 < max_age_seconds <= 2592000:
        raise ValueError("invalid_news_max_age")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone_required")
    signals = []
    for ref in publications:
        source_url(ref["url"])
        key = publication_identity(ref["platform"], ref["url"], "")["key"]
        result = lookup(ledger, key)
        if not result:
            signals.append({"identity": key, "status": "unavailable"})
            continue
        age = (now - timestamp(result["published_at"] or result["observed_at"])).total_seconds()
        usable = 0 <= age <= max_age_seconds and not result["source_issues"] and result["status"] == "completed"
        feed = result.get("feed_decision")
        eligible = usable and (feed is None or feed["action"] == "keep")
        signals.append(
            {
                "identity": key,
                "assessment_id": result["assessment_id"],
                "content_version": result["content_version"],
                "status": "current" if eligible else "feed_policy_review" if usable else "unavailable_or_stale",
                "age_seconds": age,
                "relationship": "caller_supplied_publication_reference",
                "tasks": {k: v["answer"] for k, v in result["tasks"].items() if eligible and v["status"] == "accepted"},
                "feed_decision": feed,
            }
        )
    return {"schema": "omnia.news.trading-context.v1", "token": dict(token), "signals": signals, "execution_authorized": False}
