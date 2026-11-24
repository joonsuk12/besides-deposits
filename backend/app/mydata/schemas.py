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


class RiskReactionItem(BaseModel):
    """위험 신호를 보고 남긴 생각 하나 + 그 뒤 주가."""

    id: int
    created_at: datetime
    stock_code: str
    name: str
    answer: str
    answer_label: str
    memo: str
    flagged: list[str]  # 그때 🔴·🟡였던 항목 이름
    close_then: int | None
    close_then_date: str | None
    close_now: int | None
    close_now_date: str | None
    change_pct: float | None  # 답한 날 종가 → 최근 종가
    days: int | None  # 답한 날부터 지난 날 수


class AnswerGroup(BaseModel):
    answer: str
    label: str
    count: int
    avg_change_pct: float | None  # 7일 넘게 지난 답만으로 계산
    counted: int  # 평균에 들어간 답 개수


class InsightsResponse(BaseModel):
    lines: list[str]  # "한 줄 돌아보기" (권유 없이 사실만)
    risk_items: list[RiskReactionItem]
    risk_groups: list[AnswerGroup]
    total_records: int
