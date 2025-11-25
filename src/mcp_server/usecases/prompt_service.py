"""
Application service for prompt lifecycle operations.
"""
from __future__ import annotations

from typing import Iterable

from mcp_server.domain import models
from mcp_server.domain.repositories import PromptRepository


class PromptService:
    def __init__(self, repository: PromptRepository):
        self.repository = repository

    def list_prompts(self) -> Iterable[models.Prompt]:
        return self.repository.list()

    def get_prompt(self, prompt_id: str) -> models.Prompt | None:
        return self.repository.get(prompt_id)

    def create_prompt(self, payload: models.PromptCreate) -> models.Prompt:
        return self.repository.create(payload)

    def update_prompt(self, prompt_id: str, payload: models.PromptUpdate) -> models.Prompt | None:
        return self.repository.update(prompt_id, payload)

    def delete_prompt(self, prompt_id: str) -> bool:
        return self.repository.delete(prompt_id)


