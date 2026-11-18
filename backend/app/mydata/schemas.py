"""DTO. Spring의 Request/Response DTO에 해당한다."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MyRecordCreate(BaseModel):
    kind: str = Field(max_length=40)
    stock_code: str | None = Field(default=None, max_length=12)
    question: str = Field(max_length=200)
    answer: str = Field(max_length=40)
    answer_label: str = Field(max_length=60)
    memo: str = Field(default="", max_length=500)
    context: dict[str, Any] = {}  # 화면이 아는 상황 (예: 위험 신호 개수). 주가는 서버가 채운다


class MyRecordResponse(BaseModel):
    id: int
    kind: str
    stock_code: str | None
    question: str
    answer: str
    answer_label: str
    memo: str
    context: dict[str, Any]
    created_at: datetime
