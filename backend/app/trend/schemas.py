"""DTO. Spring의 Response DTO에 해당한다."""
import datetime

from pydantic import BaseModel


class TrendDay(BaseModel):
    date: datetime.date
    foreign: int
    organ: int
    individual: int
    foreign_ratio: float | None


class TrendSummary(BaseModel):
    days: int  # 합계를 낸 거래일 수
    foreign: int
    organ: int
    individual: int


class TrendResponse(BaseModel):
    available: bool
    message: str | None = None
    items: list[TrendDay] = []  # 날짜 오름차순
    summary: list[TrendSummary] = []  # 최근 5·20·60거래일 합계
    comment: str | None = None  # 최근 흐름 한 줄
