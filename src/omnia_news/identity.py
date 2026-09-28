# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Stable publication identities; handles are references, never post identities."""

import re
from urllib.parse import parse_qs, urlsplit, urlunsplit
from .contracts import source_url
from ._engine.ledger import digest


def publication_identity(platform, url, fallback_id):
    source_url(url)
    parsed = urlsplit(url)
    host = parsed.hostname.lower()
    if parsed.port not in (None, 443):
        host = ""
    path = parsed.path.rstrip("/")
    native = None
    if platform == "x" and host in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}:
        match = re.fullmatch(r"/(?:i|[A-Za-z0-9_]+)/status/(\d+)", path)
        native = match[1] if match else None
        if native:
            url = "https://x.com/i/status/" + native
    elif platform == "youtube":
        if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
            native = parse_qs(parsed.query).get("v", [None])[0]
            match = re.fullmatch(r"/(?:shorts|live)/([\w-]{11})", path)
            native = match[1] if match else native
        elif host == "youtu.be":
            native = path.lstrip("/")
        if native and re.fullmatch(r"[A-Za-z0-9_-]{11}", native):
            url = "https://www.youtube.com/watch?v=" + native
        else:
            native = None
    elif platform == "github" and host == "github.com":
        match = re.fullmatch(r"/([^/]+/[^/]+)/(commit/([a-fA-F0-9]{40})|releases/tag/([^/]+)|issues/(\d+)|pull/(\d+))", path)
        if match:
            native = path.lstrip("/")
    elif platform == "reddit" and host in {"reddit.com", "www.reddit.com", "old.reddit.com"}:
        match = re.fullmatch(r"/r/[^/]+/comments/([a-z0-9]+)(?:/[^/]+)?(?:/([a-z0-9]+))?", path)
        if match:
            native = "t1_" + match[2] if match[2] else "t3_" + match[1]
    if native is None:
        url = urlunsplit(("https", parsed.netloc.lower(), parsed.path, parsed.query, ""))
    return {
        "key": platform + ":" + (native or "url:" + digest(url)),
        "native_id": native,
        "canonical_url": url,
        "input_id": fallback_id,
        "basis": "native_url" if native else "canonical_url",
    }


def content_version(item):
    """Collection clocks do not invalidate an unchanged source evaluation."""
    metadata = {
        k: v
        for k, v in item["metadata"].items()
        if k
        not in {
            "source_updated_at",
            "author_followers",
            "view_count",
            "like_count",
            "reply_count",
            "repost_count",
            "context_missing",
            "author_handle",
            "author_identity_kind",
            "source_actor",
            "source_event_type",
            "source_text_at_limit",
        }
    }
    return digest(
        {"author": item["author"], "text": item["text"], "language": item.get("language"), "context": item["context"], "metadata": metadata}
    )
