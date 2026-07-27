# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Configuration contains only consumed runtime and product settings."""
from dataclasses import dataclass, field, replace
import os
from ._engine.runtime import Settings
from .policy import NewsPolicy


@dataclass(frozen=True)
class Config:
    runtime: Settings
    max_records: int = 1000
    policy: NewsPolicy = field(default_factory=NewsPolicy)

    def __post_init__(self):
        if type(self.max_records) is not int or not 1 <= self.max_records <= 100000:
            raise ValueError('invalid_record_limit')
        if not isinstance(self.policy, NewsPolicy):
            raise ValueError('invalid_news_policy')

    @classmethod
    def from_env(cls):
        settings = replace(Settings.from_env(), database=os.environ.get('OMNIA_NEWS_DATABASE', 'var/news/decisions.sqlite3'))
        return cls(settings, int(os.environ.get('OMNIA_NEWS_MAX_RECORDS', '1000')), NewsPolicy.from_env())
