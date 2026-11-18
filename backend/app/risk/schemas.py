"""DTO. Spring의 Response DTO에 해당한다."""
import datetime

from pydantic import BaseModel


class Evidence(BaseModel):
    """신호의 근거 한 줄 (공시 한 건이나 한 해의 숫자)."""

    date: datetime.date | None = None
    text: str
    url: str | None = None  # 공시 원문


class RiskCheck(BaseModel):
    key: str  # listing, trust …
    title: str  # 예: "주식 수가 늘어날 일"
    status: str  # ok(초록) / caution(노랑) / danger(빨강)
    summary: str  # 이 종목은 어떤지 한 줄
    why: str  # 왜 초보가 봐야 하는지
    evidence: list[Evidence] = []


class RiskResponse(BaseModel):
    available: bool
    message: str | None = None
    period_days: int = 365  # 공시를 살펴본 기간
    checks: list[RiskCheck] = []
    counts: dict[str, int] = {}  # {"danger": 0, "caution": 1, "ok": 7}
