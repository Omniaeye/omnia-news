# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Executable catalog of adapter-supplied metadata; values are not verified claims."""
from copy import deepcopy

CATALOG_VERSION = 'omnia.news.metadata.v1'


def _field(kind, description, use='provenance', **bounds):
    return {'type': kind, 'description': description, 'use': use, **bounds}


FIELDS = {
    'source_kind': _field('enum', 'Kind reported by the source adapter.', 'model_context',
                          values=['article', 'post', 'commit', 'release', 'advisory', 'comment']),
    'record_type': _field('enum', 'Relationship to previously published content.', 'deterministic_gate',
                         values=['original', 'correction', 'update', 'retraction']),
    'source_updated_at': _field('timestamp', 'Last source edit time, with timezone.'),
    'source_deleted': _field('boolean', 'Adapter reports that the source was deleted.', 'deterministic_gate'),
    'author_type': _field('enum', 'Reported primary author category.', 'model_context',
                         values=['person', 'organization', 'bot', 'unknown']),
    'author_verified': _field('boolean', 'Platform account badge, not factual verification.'),
    'publisher': _field('string', 'Publisher identity supplied by the adapter.', max_length=200),
    'canonical_url': _field('url', 'Canonical HTTPS reference; never fetched.'),
    'title': _field('string', 'Original source title, retained only in the caller archive.', max_length=300),
    'section': _field('string', 'Source section or channel.', max_length=100),
    'tags': _field('strings', 'Source labels, not inferred entities.', max_items=8, max_length=64),
    'content_format': _field('enum', 'Format of the supplied primary text.', 'deterministic_gate',
                            values=['plain_text', 'markdown', 'html']),
    'is_truncated': _field('boolean', 'Adapter reports incomplete primary text.', 'deterministic_gate'),
    'is_machine_translated': _field('boolean', 'Supplied text was machine translated.', 'model_context'),
    'translation_language': _field('string', 'Language of the translated text, if supplied.', 'deterministic_gate', max_length=32),
    'source_revision': _field('string', 'Source-side revision or edit identifier.', max_length=200),
    'origin_id': _field('string', 'Original record identifier for syndicated content.', max_length=200),
    'origin_url': _field('url', 'Original source HTTPS reference; not proof of authorship.'),
    'is_sponsored': _field('boolean', 'Adapter reports sponsored content.', 'model_context'),
    'is_bot_generated': _field('boolean', 'Adapter reports generated content; never sufficient to suppress.', 'model_context'),
    'commit_parent_count': _field('integer', 'Number of commit parents.', 'model_context', maximum=100, platform='github'),
    'commit_files_changed': _field('integer', 'Reported changed-file count.', maximum=1000000, platform='github'),
    'commit_additions': _field('integer', 'Reported added-line count.', maximum=1000000000, platform='github'),
    'commit_deletions': _field('integer', 'Reported deleted-line count.', maximum=1000000000, platform='github'),
    'commit_branch': _field('string', 'Observed branch; not a claim that the commit is deployed.', max_length=256, platform='github'),
    'commit_is_merge': _field('boolean', 'Adapter identifies a merge commit.', 'model_context', platform='github'),
    'commit_is_revert': _field('boolean', 'Adapter identifies a revert commit.', 'model_context', platform='github'),
    'commit_signature_verified': _field('boolean', 'Adapter signature result; this package does not verify signatures.', platform='github'),
    'commit_paths': _field('strings', 'Bounded source-reported paths; never opened.', max_items=16, max_length=256, platform='github'),
    'release_tag': _field('string', 'Source release identifier.', max_length=128),
    'advisory_id': _field('string', 'Source advisory identifier; not a validated vulnerability.', max_length=128),
    'advisory_severity': _field('enum', 'Source severity label; not independently assessed.',
                               values=['unknown', 'low', 'moderate', 'high', 'critical']),
}


def parameter_catalog():
    """Return a detached, JSON-serializable catalog used by validation and docs."""
    return {'schema': CATALOG_VERSION, 'fields': deepcopy(FIELDS)}


def normalize_metadata(value, *, platform, url_validator, timestamp_validator):
    if not isinstance(value, dict) or set(value) - set(FIELDS):
        raise ValueError('invalid_metadata_fields')
    for name, item in value.items():
        spec = FIELDS[name]
        if spec.get('platform', platform) != platform:
            raise ValueError('metadata_platform_mismatch')
        kind = spec['type']
        if kind == 'boolean':
            valid = type(item) is bool
        elif kind == 'integer':
            valid = type(item) is int and 0 <= item <= spec['maximum']
        elif kind == 'enum':
            valid = isinstance(item, str) and item in spec['values']
        elif kind == 'string':
            valid = isinstance(item, str) and bool(item.strip()) and len(item) <= spec['max_length']
        elif kind == 'strings':
            valid = (isinstance(item, list) and len(item) <= spec['max_items']
                     and all(isinstance(v, str) and v.strip() and len(v) <= spec['max_length'] for v in item))
            if valid:
                valid = len(item) == len(set(item))
        elif kind == 'url':
            url_validator(item)
            valid = True
        elif kind == 'timestamp':
            timestamp_validator(item)
            valid = True
        else:
            raise RuntimeError('unsupported_catalog_type')
        if not valid:
            raise ValueError('invalid_metadata_value:' + name)
    if 'commit_parent_count' in value and 'commit_is_merge' in value:
        if value['commit_is_merge'] != (value['commit_parent_count'] > 1):
            raise ValueError('inconsistent_commit_parent_count')
    if 'translation_language' in value and value.get('is_machine_translated') is not True:
        raise ValueError('translation_requires_translated_text')
    return deepcopy(value)


def model_metadata(value):
    """Only bounded flags, enums and a small count enter the model context."""
    return {name: item for name, item in value.items() if FIELDS[name]['use'] == 'model_context'}
