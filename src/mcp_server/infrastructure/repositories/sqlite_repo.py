"""
SQLite-backed repository implementations.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from mcp_server.domain import models
from mcp_server.infrastructure.db import models as orm_models


def _ensure_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PromptSQLiteRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> Iterable[models.Prompt]:
        stmt = select(orm_models.PromptORM)
        return [self._to_domain(row) for row in self.session.execute(stmt).scalars().all()]

    def get(self, prompt_id: str) -> models.Prompt | None:
        row = self.session.get(orm_models.PromptORM, prompt_id)
        return self._to_domain(row) if row else None

    def create(self, data: models.PromptCreate) -> models.Prompt:
        row = orm_models.PromptORM(
            id=_ensure_id("prompt"),
            name=data.name,
            role=data.role.value,
            content=data.content,
            tags=data.tags,
            updated_at=_now(),
        )
        self.session.add(row)
        self.session.flush()
        return self._to_domain(row)

    def update(self, prompt_id: str, data: models.PromptUpdate) -> models.Prompt | None:
        row = self.session.get(orm_models.PromptORM, prompt_id)
        if not row:
            return None
        for field, value in data.model_dump(exclude_none=True).items():
            if field == "role" and value is not None:
                setattr(row, field, value.value)
            else:
                setattr(row, field, value)
        row.updated_at = _now()
        self.session.flush()
        return self._to_domain(row)

    def delete(self, prompt_id: str) -> bool:
        row = self.session.get(orm_models.PromptORM, prompt_id)
        if not row:
            return False
        self.session.delete(row)
        self.session.flush()
        return True

    @staticmethod
    def _to_domain(row: orm_models.PromptORM) -> models.Prompt:
        return models.Prompt(
            id=row.id,
            name=row.name,
            role=models.PromptRole(row.role),
            content=row.content,
            tags=row.tags or [],
            updated_at=row.updated_at,
        )


class ResourceSQLiteRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> Iterable[models.Resource]:
        stmt = select(orm_models.ResourceORM)
        return [self._to_domain(row) for row in self.session.execute(stmt).scalars().all()]

    def get(self, resource_id: str) -> models.Resource | None:
        row = self.session.get(orm_models.ResourceORM, resource_id)
        return self._to_domain(row) if row else None

    def create(self, data: models.ResourceCreate) -> models.Resource:
        row = orm_models.ResourceORM(
            id=_ensure_id("resource"),
            updated_at=_now(),
            **data.model_dump(),
        )
        self.session.add(row)
        self.session.flush()
        return self._to_domain(row)

    def update(self, resource_id: str, data: models.ResourceUpdate) -> models.Resource | None:
        row = self.session.get(orm_models.ResourceORM, resource_id)
        if not row:
            return None
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(row, field, value)
        row.updated_at = _now()
        self.session.flush()
        return self._to_domain(row)

    def delete(self, resource_id: str) -> bool:
        row = self.session.get(orm_models.ResourceORM, resource_id)
        if not row:
            return False
        self.session.delete(row)
        self.session.flush()
        return True

    @staticmethod
    def _to_domain(row: orm_models.ResourceORM) -> models.Resource:
        return models.Resource(
            id=row.id,
            name=row.name,
            description=row.description,
            content=row.content,
            category=row.category,
            tags=row.tags or [],
            updated_at=row.updated_at,
        )


class ToolSQLiteRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> Iterable[models.Tool]:
        stmt = select(orm_models.ToolORM)
        return [self._to_domain(row) for row in self.session.execute(stmt).scalars().all()]

    def get(self, tool_id: str) -> models.Tool | None:
        row = self.session.get(orm_models.ToolORM, tool_id)
        return self._to_domain(row) if row else None

    def create(self, data: models.ToolCreate) -> models.Tool:
        row = orm_models.ToolORM(
            id=_ensure_id("tool"),
            updated_at=_now(),
            **data.model_dump(),
        )
        self.session.add(row)
        self.session.flush()
        return self._to_domain(row)

    def update(self, tool_id: str, data: models.ToolUpdate) -> models.Tool | None:
        row = self.session.get(orm_models.ToolORM, tool_id)
        if not row:
            return None
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(row, field, value)
        row.updated_at = _now()
        self.session.flush()
        return self._to_domain(row)

    def delete(self, tool_id: str) -> bool:
        row = self.session.get(orm_models.ToolORM, tool_id)
        if not row:
            return False
        self.session.delete(row)
        self.session.flush()
        return True

    @staticmethod
    def _to_domain(row: orm_models.ToolORM) -> models.Tool:
        return models.Tool(
            id=row.id,
            name=row.name,
            description=row.description,
            code=row.code,
            tags=row.tags or [],
            updated_at=row.updated_at,
        )


