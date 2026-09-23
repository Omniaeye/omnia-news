# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""News evidence -> typed assessment -> conservative feed disposition."""
from copy import deepcopy
from .contracts import normalize
from .github import message, literal_reason, operational_record
from .questions import QUESTIONS, TASK_VERSION
from .policy import decide


def process(event, ledger, backend, *, min_probability=.8, max_bytes=65536):
    item = normalize(event, max_bytes)
    primary = message(item['text']) if item['platform'] == 'github' else item['text'].strip()
    literal = literal_reason(primary) if item['platform'] == 'github' and not item['context'] else None
    state = {'primary_author': item['author'], 'primary_text': primary, 'context': item['context']}
    request = {'id': item['id'], 'state': state, 'questions': deepcopy(QUESTIONS),
               'evidence': [item['url'], *[c['url'] for c in item['context']]]}
    # The task manifest binds all source metadata, even values omitted from model input.
    from ._engine.ledger import digest
    if literal:
        predictor = lambda *_: {'answers': {'signal': {'type': 'choice', 'choice': 'noise',
                               'probabilities': {'keep': 0., 'noise': 1.}}}}
        manifest = {'backend': 'literal_format', 'task': TASK_VERSION, 'source_hash': digest(item)}
    else:
        predictor = backend
        manifest = {**backend.manifest(), 'task': TASK_VERSION, 'source_hash': digest(item)}
    record = ledger.decide(request, predictor, manifest=manifest,
                           min_probability=min_probability, max_bytes=max_bytes)
    action, reason = decide(record, operational=item['platform'] == 'github' and operational_record(primary), literal=literal)
    return {'schema': 'omnia.news.decision.v1', 'source_id': item['id'], 'source_url': item['url'],
            'action': action, 'reason': reason, 'preserve_archive': True,
            'decision': record, 'task_version': TASK_VERSION}
