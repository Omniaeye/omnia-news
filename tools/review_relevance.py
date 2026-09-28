# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Recompute a source-bound relevance review without model or network calls."""
import argparse
from collections import Counter
import json
from pathlib import Path

from omnia_news.casebook import verify


def review(casebook, labels):
    verify(casebook)
    records = {}
    for path in (casebook / 'records').glob('*.json'):
        packet = json.loads(path.read_bytes())
        records[packet['publication']['id']] = packet['assessment']
    outcomes = []
    seen = set()
    for label in labels['records']:
        if label['source_id'] in seen:
            raise ValueError('duplicate_review_source')
        seen.add(label['source_id'])
        result = records[label['source_id']]
        if result['source_input_sha256'] != label['source_input_sha256']:
            raise ValueError('review_source_mismatch')
        task = result['tasks']['relevance']
        action = result['feed_decision']['action']
        expected = {'informative': 'keep', 'noise': 'suppress', 'insufficient': 'review'}[label['expected']]
        outcomes.append({**label, 'answer': task['answer'], 'task_status': task['status'],
                         'feed_decision': result['feed_decision'], 'matches_reference': action == expected,
                         'assessment_id': result['assessment_id']})
    decisive = [row for row in outcomes if row['feed_decision']['action'] != 'review']
    return {'reviewer': labels['reviewer'], 'independent_human_gold': labels['independent_human_gold'],
            'reviewed': len(outcomes), 'actions': dict(Counter(row['feed_decision']['action'] for row in outcomes)),
            'decisive_matches': sum(row['matches_reference'] for row in decisive), 'decisive_total': len(decisive),
            'coverage': len(decisive) / len(outcomes) if outcomes else None,
            'precision': sum(row['matches_reference'] for row in decisive) / len(decisive) if decisive else None,
            'records': outcomes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('casebook', type=Path)
    parser.add_argument('labels', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = review(args.casebook, json.loads(args.labels.read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + '\n', encoding='utf-8', newline='\n')
