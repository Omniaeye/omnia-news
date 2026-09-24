# News API

`process(event, ledger, backend, min_probability=0.8, max_bytes=65536)` returns
`omnia.news.decision.v1`. The backend is callable `(state, questions)` and exposes
`manifest()`; use the bundled `LocalLaya` for actual inference.

| Input | Contract |
| --- | --- |
| `id` | Stable nonempty source ID, up to 200 characters |
| `platform` | github, x, reddit, youtube, website or news |
| `url` | HTTPS source reference without embedded credentials; never fetched by this package |
| `author` | Primary author identifier |
| `text` | Complete supplied primary text, up to 20000 characters |
| `observed_at` | Timestamp with timezone |
| `published_at` | Optional source publication time with timezone |
| `language` | Optional source language label; does not auto-select the model |
| `context` | Up to four independently attributed records |

Each context record has `id`, `relation`, `author`, `text`, `url`. Relations are
`reply_to`, `quote` and `repost`. IDs must be unique and cannot equal the primary ID.
GitHub records require a full 40-character commit SHA in the canonical source URL.

The output contains `action`, `reason`, `source_id`, `source_url`, `task_version`,
`preserve_archive: true` and a durable `decision`. No output contains an invented
entity extraction, summary, price target or claim of code correctness.
