# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""A model vote cannot hide an unconstrained free-form message."""
def decide(record, *, operational=False, literal=None):
    if literal:
        return 'suppress', literal
    if record['status'] != 'accepted':
        return 'review', 'below_probability_threshold'
    answer = record['answers']['signal']['choice']
    if answer == 'keep':
        return 'keep', 'informative_text'
    if operational:
        return 'suppress', 'confirmed_operational_record'
    return 'review', 'unverified_noise'
