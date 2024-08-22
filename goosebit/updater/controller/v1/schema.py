from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class ConfigDataUpdateMode(StrEnum):
    MERGE = "merge"
    REPLACE = "replace"
    REMOVE = "remove"


class ConfigDataSchema(BaseModel):
    data: dict[str, Any]
    mode: ConfigDataUpdateMode = ConfigDataUpdateMode.MERGE


class FeedbackStatusExecutionState(StrEnum):
    CLOSED = "closed"
    PROCEEDING = "proceeding"
    CANCELED = "canceled"
    SCHEDULED = "scheduled"
    REJECTED = "rejected"
    RESUMED = "resumed"
    DOWNLOADED = "downloaded"
    DOWNLOAD = "download"


class FeedbackStatusProgressSchema(BaseModel):
    cnt: int
    of: int | None


class FeedbackStatusResultFinished(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    NONE = "none"


class FeedbackStatusResultSchema(BaseModel):
    finished: FeedbackStatusResultFinished
    progress: FeedbackStatusProgressSchema = None


class FeedbackStatusSchema(BaseModel):
    execution: FeedbackStatusExecutionState
    result: FeedbackStatusResultSchema
    code: int = None
    details: list[str] = None


class FeedbackSchema(BaseModel):
    time: str = None
    status: FeedbackStatusSchema
