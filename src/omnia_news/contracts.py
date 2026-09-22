# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Bounded source records with explicit attribution."""
from copy import deepcopy
from datetime import datetime, timezone
from urllib.parse import urlsplit
import json
import re

PLATFORMS = frozenset({'github', 'x', 'reddit', 'youtube', 'website', 'news'})


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('timestamp_required')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timezone_required')
    return parsed.astimezone(timezone.utc)


def bounded(value, maximum=256, *, empty=False):
    if not isinstance(value, str) or len(value) > maximum or (not empty and not value.strip()):
        raise ValueError('invalid_text')
    return value


def source_url(value):
    parsed = urlsplit(bounded(value, 2048))
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('invalid_source_url')
    return value


def normalize(event, max_bytes=65536):
    if not isinstance(event, dict):
        raise ValueError('event_object_required')
    required = {'id', 'platform', 'url', 'author', 'text', 'observed_at'}
    optional = {'published_at', 'language', 'context'}
    if not required <= set(event) or set(event) - required - optional:
        raise ValueError('invalid_event_fields')
    if len(json.dumps(event, ensure_ascii=False, allow_nan=False).encode()) > max_bytes:
        raise ValueError('event_too_large')
    out = deepcopy(event)
    bounded(out['id'], 200)
    bounded(out['author'])
    bounded(out['text'], 20000, empty=True)
    if out['platform'] not in PLATFORMS:
        raise ValueError('unsupported_platform')
    source_url(out['url'])
    timestamp(out['observed_at'])
    if out.get('published_at') is not None:
        timestamp(out['published_at'])
    if out.get('language') is not None:
        bounded(out['language'], 32)
    context = out.setdefault('context', [])
    if not isinstance(context, list) or len(context) > 4:
        raise ValueError('invalid_context')
    seen = {out['id']}
    for item in context:
        if not isinstance(item, dict) or set(item) != {'id', 'relation', 'author', 'text', 'url'}:
            raise ValueError('invalid_context_fields')
        bounded(item['id'], 200)
        if item['id'] in seen or item['relation'] not in {'reply_to', 'quote', 'repost'}:
            raise ValueError('invalid_context_relation')
        seen.add(item['id'])
        bounded(item['author'])
        bounded(item['text'], 10000)
        source_url(item['url'])
    if out['platform'] == 'github':
        match = re.fullmatch(r'https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/commit/([a-fA-F0-9]{40})', out['url'])
        if not match:
            raise ValueError('invalid_commit_identity')
        out['repository'], out['commit_sha'] = match[1], match[2].lower()
    return out
