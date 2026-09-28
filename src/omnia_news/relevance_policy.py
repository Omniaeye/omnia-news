# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Publication eligibility is distinct from the native relevance answer."""
import re

from .github import literal_reason, message, operational_record

VERSION = 'omnia.news.relevance-policy.v2'


def checks(item, source_issues):
    primary = message(item['text']) if item['platform'] == 'github' else item['text'].strip()
    format_reason = None
    if item['platform'] == 'github':
        format_reason = literal_reason(primary)
        if not format_reason and operational_record(primary):
            format_reason = 'operational_record'
    # An asset mention in a short post can be meaningful; a bare reaction needs context.
    has_reference = bool(re.search(r'https://|\$[A-Za-z][A-Za-z0-9_]{1,14}\b|0x[a-fA-F0-9]{40}', primary))
    short_social = item['platform'] in {'x', 'reddit'} and len(primary) < 32 and not has_reference
    return {'version': VERSION, 'format_reason': format_reason, 'short_social_fragment': short_social,
            'source_issues': list(source_issues), 'native_input': 'complete_primary_text'}


def decide(task, inspected):
    answer = task.get('answer')
    complete = not inspected['source_issues']
    if not complete or task['status'] == 'failed':
        action, reason, basis = 'review', 'source_requires_review', 'source_policy'
    elif inspected['format_reason']:
        action, reason, basis = 'suppress', inspected['format_reason'], 'exact_source_format'
    elif inspected['short_social_fragment']:
        action, reason, basis = 'review', 'short_social_fragment', 'source_policy'
    elif task['status'] == 'accepted' and answer and answer['choice'] == 'informative':
        action, reason, basis = 'keep', 'informative_primary_text', 'native_assessment'
    else:
        action = 'review'
        reason = 'unverified_noise' if answer and answer['choice'] == 'noise' else 'below_probability_threshold'
        basis = 'native_assessment'
    return {'action': action, 'reason': reason, 'basis': basis, 'policy_version': VERSION,
            'preserve_archive': True, 'publication_authorized': False}
