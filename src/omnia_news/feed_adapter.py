# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Project existing OMNIA feed records without reading collectors or following URLs."""

from urllib.parse import urlsplit


def adapt_feed(payload):
    platform = payload["platform"]
    social = payload.get("socialMetadata") or {}
    content = social.get("content") or {}
    account = social.get("account") or {}
    text = content.get("text") if platform == "x" else payload.get("body")
    text = text if isinstance(text, str) else payload.get("title") or ""
    if platform in {"news", "website"} and payload.get("title") and payload["title"] not in text:
        text = payload["title"] + "\n\n" + text
    url = content.get("canonicalUrl") or payload["url"]
    metadata = {"source_kind": "commit" if platform == "github" else "article" if platform in {"news", "website"} else "post"}
    event_type = payload.get("eventType")
    if isinstance(event_type, str) and event_type.strip() and len(event_type) <= 100:
        metadata["source_event_type"] = event_type
    metadata["author_identity_kind"] = "platform_account" if account.get("nativeId") or account.get("handle") else "source_label"
    actor = payload.get("actor")
    if isinstance(actor, str) and actor.strip() and len(actor) <= 256:
        metadata["source_actor"] = actor
    if platform == "github" and "/releases/tag/" in url:
        metadata["source_kind"] = "release"
    if platform == "github" and any(p in url for p in ("/issues/", "/pull/")):
        metadata["source_kind"] = "comment"
    if platform == "github" and payload.get("eventType") == "commit_push" and len(text) >= 4000:
        metadata["source_text_at_limit"] = True
    # A news-feed excerpt is assessed as an excerpt, not as a downloaded article.
    if platform in {"news", "website"}:
        metadata["is_truncated"] = True
    contexts, seen = [], set()
    relations = {"reply_to": "reply_to", "quotes": "quote", "quote": "quote", "reposts": "repost", "repost": "repost"}
    for row in social.get("contexts") or []:
        record = row.get("record") or {}
        body = record.get("content") or {}
        author = record.get("account") or {}
        relation = relations.get(row.get("relation"))
        cid = record.get("dedupKey") or body.get("nativeId")
        if relation and cid and cid not in seen and body.get("text") and body.get("canonicalUrl"):
            contexts.append(
                {
                    "id": cid,
                    "relation": relation,
                    "author": author.get("nativeId") or author.get("handle") or "unknown",
                    "text": body["text"],
                    "url": body["canonicalUrl"],
                }
            )
            seen.add(cid)
    expected = [r for r in social.get("relationships") or [] if r.get("relation") in relations]
    if any(r.get("to") not in seen for r in expected):
        metadata["context_missing"] = True
    followers = account.get("followers")
    handle = account.get("handle")
    if isinstance(handle, str) and handle.strip() and len(handle) <= 100:
        metadata["author_handle"] = handle
    if type(followers) is int and 0 <= followers <= 1000000000000:
        metadata["author_followers"] = followers
    return {
        "id": payload["id"],
        "platform": platform,
        "url": url,
        "author": account.get("nativeId") or account.get("handle") or payload.get("sourceLabel") or urlsplit(url).hostname,
        "text": text,
        "observed_at": payload.get("observedAt") or payload["publishedAt"],
        "published_at": payload.get("publishedAt"),
        "context": contexts,
        "metadata": metadata,
    }
