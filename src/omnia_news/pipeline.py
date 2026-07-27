# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Source evidence -> typed assessment -> durable, conservative feed disposition."""
from copy import deepcopy
from datetime import datetime, timezone
from .catalog import CATALOG_VERSION, model_metadata
from .contracts import normalize
from .github import message, literal_reason, operational_record
from .questions import QUESTIONS, TASK_VERSION
from .policy import NewsPolicy, decide
from ._engine.ledger import digest, probability


NOTES = {
    'empty_message': 'The complete primary message is empty after conservative normalization.',
    'hash_only': 'The complete primary message contains only hexadecimal identifiers.',
    'informative_text': 'An accepted model answer supports informativity, not factual correctness.',
    'confirmed_operational_record': 'An exact bookkeeping format and an accepted noise answer agree.',
    'below_probability_threshold': 'The answer did not reach the configured probability threshold.',
    'unverified_noise': 'A model noise vote alone cannot suppress free-form primary text.',
    'literal_suppression_disabled': 'The caller requires review instead of literal-format suppression.',
    'operational_suppression_disabled': 'The caller requires review instead of bookkeeping suppression.',
    'incomplete_source_text': 'The adapter marked the primary text as incomplete.',
    'deleted_source': 'The adapter marked the source as deleted.',
    'source_retraction': 'The adapter marked this record as a retraction; publication needs review.',
    'html_requires_text_adapter': 'Convert source HTML into complete attributed text before model assessment.',
    'language_outside_policy': 'The supplied text language is absent or outside the caller allowlist.',
    'publication_time_required': 'The age policy requires a source publication timestamp.',
    'publication_after_observation': 'The publication timestamp is later than the observation timestamp.',
    'source_outside_age_policy': 'Source age at observation exceeds the caller limit.',
    'backend_error': 'Assessment failed; retry with the retained original source record.',
}


def process(event, ledger, backend, *, min_probability=.8, max_bytes=65536, policy=None):
    item = normalize(event, max_bytes)
    policy = NewsPolicy() if policy is None else policy
    if not isinstance(policy, NewsPolicy):
        raise ValueError('invalid_news_policy')
    probability(min_probability)
    metadata = item['metadata']
    base = {
        'schema': 'omnia.news.decision.v1', 'source_id': item['id'], 'source_url': item['url'],
        'source_platform': item['platform'], 'source_author': item['author'],
        'context_provenance': [{key: context[key] for key in ('id', 'relation', 'author', 'url')}
                               for context in item['context']],
        'observed_at': item['observed_at'], 'published_at': item.get('published_at'),
        'original_input_sha256': digest(event), 'normalized_source_sha256': digest(item),
        'metadata_catalog': CATALOG_VERSION, 'metadata_fields': sorted(metadata),
        'preserve_archive': True, 'task_version': TASK_VERSION, 'news_policy': policy.manifest(),
        'min_answer_probability': min_probability,
    }

    def finish(action, reason, record=None, *, failed=False, error_code=None):
        result = {**base, 'evaluated_at': datetime.now(timezone.utc).isoformat(),
                  'status': 'failed' if failed else 'completed', 'action': action, 'reason': reason,
                  'decision': record, 'notes': [{'code': reason, 'text': NOTES[reason]}]}
        if metadata:
            result['notes'].append({'code': 'adapter_reported_metadata',
                                    'text': 'Metadata was validated and fingerprinted; its factual accuracy was not verified.'})
        if metadata.get('is_machine_translated'):
            result['notes'].append({'code': 'translated_source', 'text': 'The adapter supplied machine-translated primary text.'})
        if error_code:
            result['error_code'] = error_code
        return ledger.record_assessment(result)

    gate = policy.review_reason(item)
    if gate:
        return finish('review', gate)
    primary = message(item['text']) if item['platform'] == 'github' else item['text'].strip()
    literal = literal_reason(primary) if item['platform'] == 'github' and not item['context'] else None
    state = {'primary_author': item['author'], 'primary_text': primary, 'context': item['context']}
    selected = model_metadata(metadata)
    if selected:
        state['reported_metadata'] = selected
    request = {'id': item['id'], 'state': state, 'questions': deepcopy(QUESTIONS),
               'evidence': [item['url'], *[c['url'] for c in item['context']]]}
    try:
        if literal:
            predictor = lambda *_: {'answers': {'signal': {'type': 'choice', 'choice': 'noise',
                                   'probabilities': {'keep': 0., 'noise': 1.}}}}
            manifest = {'backend': 'literal_format', 'task': TASK_VERSION, 'source_hash': digest(item)}
        else:
            predictor = backend
            manifest = {**backend.manifest(), 'task': TASK_VERSION, 'source_hash': digest(item)}
        record = ledger.decide(request, predictor, manifest=manifest,
                               min_probability=min_probability, max_bytes=max_bytes)
    except Exception as error:
        finish('review', 'backend_error', failed=True, error_code=type(error).__name__)
        raise
    action, reason = decide(record, operational=item['platform'] == 'github' and operational_record(primary),
                            literal=literal, policy=policy)
    return finish(action, reason, record)
