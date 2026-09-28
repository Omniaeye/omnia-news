# Copyright 2026 OMNIA EYE Corporation.
# SPDX-License-Identifier: Apache-2.0
"""Pinned per-language models and lossless bounded segmentation."""

from dataclasses import replace
from ._engine.runtime import LocalLaya, check_token_budget


class NewsModel(LocalLaya):
    def prepare(self, state, questions):
        # Initialize and verify the pinned checkpoint through the same runtime path.
        if self.router is None:
            import torch
            from laya import Router

            torch.set_num_threads(self.settings.threads)
            self.router = Router(
                device=self.settings.device,
                revision=self.settings.revision,
                default=self.settings.model,
                auto_task_detection=False,
                max_loaded=1,
            )
        agent = self.router.load(self.settings.model)
        if agent.revision != self.settings.revision:
            raise ValueError("checkpoint_revision_mismatch")

        def fits(value):
            try:
                check_token_budget(agent.tok, value, questions, max_len=self.settings.max_len, head_max_len=self.settings.head_max_len)
                return True
            except ValueError as error:
                if str(error) != "state exceeds the complete-input context budget":
                    raise
                return False

        if fits(state):
            return [state]
        chunks = []
        parts = [("primary", state["primary_author"], "", state["primary_text"])]
        parts += [("context", c["author"], c["relation"], c["text"]) for c in state["context"]]
        for scope, author, relation, text in parts:
            pending = [text]
            while pending:
                part = pending.pop(0)
                value = {
                    "primary_author": state["primary_author"],
                    "primary_text": part if scope == "primary" else "",
                    "context": [] if scope == "primary" else [{"author": author, "relation": relation, "text": part}],
                }
                if fits(value):
                    chunks.append(value)
                elif len(part) > 1:
                    middle = len(part) // 2
                    pending[0:0] = [part[:middle], part[middle:]]
                else:
                    raise ValueError("source_attribution_exceeds_context")
                if len(chunks) + len(pending) > 256:
                    raise ValueError("segment_budget_exceeded")
        return chunks


class RoutedNews:
    def __init__(self, settings):
        self.settings = settings
        self.models = {}

    def for_event(self, item):
        from laya.lang import analyse

        contents = [item["text"], *[c["text"] for c in item["context"]]]
        detected = analyse(contents)
        hint = (item.get("language") or "").lower().split("-")[0]
        name = "english" if detected["is_english"] and hint in {"", "en"} else "multilingual"
        if name not in self.models:
            self.models[name] = NewsModel(replace(self.settings, model=name, max_len=512 if name == "english" else 1024, head_max_len=192))
        return self.models[name]
