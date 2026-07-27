# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Versioned feed policy; adapter metadata is never proof of factual correctness."""
from dataclasses import asdict, dataclass
import os
from .contracts import timestamp

POLICY_VERSION = 'omnia.news.policy.v1'


@dataclass(frozen=True)
class NewsPolicy:
    allow_literal_suppression: bool = True
    allow_operational_suppression: bool = True
    review_incomplete: bool = True
    review_deleted: bool = True
    review_retractions: bool = True
    review_html: bool = True
    allowed_languages: tuple = ()
    max_age_seconds: int | None = None

    def __post_init__(self):
        for name in ('allow_literal_suppression', 'allow_operational_suppression', 'review_incomplete',
                     'review_deleted', 'review_retractions', 'review_html'):
            if type(getattr(self, name)) is not bool:
                raise ValueError('invalid_news_policy_boolean')
        if (not isinstance(self.allowed_languages, tuple)
                or any(not isinstance(v, str) or not v.strip() or len(v) > 32 for v in self.allowed_languages)):
            raise ValueError('invalid_allowed_languages')
        if self.max_age_seconds is not None and (type(self.max_age_seconds) is not int or not 0 <= self.max_age_seconds <= 315360000):
            raise ValueError('invalid_max_age_seconds')

    def manifest(self):
        values = asdict(self)
        values['allowed_languages'] = list(self.allowed_languages)
        return {'version': POLICY_VERSION, **values}

    @classmethod
    def from_env(cls):
        values = {}
        for name in ('allow_literal_suppression', 'allow_operational_suppression', 'review_incomplete',
                     'review_deleted', 'review_retractions', 'review_html'):
            raw = os.environ.get('OMNIA_NEWS_' + name.upper())
            if raw is not None:
                if raw.strip().lower() not in {'true', 'false', '1', '0'}:
                    raise ValueError('invalid_news_policy_boolean')
                values[name] = raw.strip().lower() in {'true', '1'}
        raw = os.environ.get('OMNIA_NEWS_ALLOWED_LANGUAGES', '')
        values['allowed_languages'] = tuple(value.strip() for value in raw.split(',') if value.strip())
        age = os.environ.get('OMNIA_NEWS_MAX_AGE_SECONDS', '')
        values['max_age_seconds'] = int(age) if age.strip() else None
        return cls(**values)

    def review_reason(self, item):
        metadata = item['metadata']
        if self.review_incomplete and metadata.get('is_truncated') is True:
            return 'incomplete_source_text'
        if self.review_deleted and metadata.get('source_deleted') is True:
            return 'deleted_source'
        if self.review_retractions and metadata.get('record_type') == 'retraction':
            return 'source_retraction'
        if self.review_html and metadata.get('content_format') == 'html':
            return 'html_requires_text_adapter'
        language = metadata.get('translation_language') or item.get('language')
        if self.allowed_languages and (not language or language.casefold() not in {v.casefold() for v in self.allowed_languages}):
            return 'language_outside_policy'
        if self.max_age_seconds is not None:
            if item.get('published_at') is None:
                return 'publication_time_required'
            age = (timestamp(item['observed_at']) - timestamp(item['published_at'])).total_seconds()
            if age < 0:
                return 'publication_after_observation'
            if age > self.max_age_seconds:
                return 'source_outside_age_policy'
        return None


def decide(record, *, operational=False, literal=None, policy=None):
    policy = policy or NewsPolicy()
    if literal:
        return ('suppress', literal) if policy.allow_literal_suppression else ('review', 'literal_suppression_disabled')
    if record['status'] != 'accepted':
        return 'review', 'below_probability_threshold'
    answer = record['answers']['signal']['choice']
    if answer == 'keep':
        return 'keep', 'informative_text'
    if operational and policy.allow_operational_suppression:
        return 'suppress', 'confirmed_operational_record'
    if operational:
        return 'review', 'operational_suppression_disabled'
    return 'review', 'unverified_noise'
