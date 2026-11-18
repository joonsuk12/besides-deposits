"""DTO. Spring의 Response DTO에 해당한다."""
import datetime

from pydantic import BaseModel


class MoveDisclosure(BaseModel):
    date: datetime.date
    title: str
    category: str
    level: str  # warn / good / key / info (disclosure 규칙 그대로)
    url: str
    timing: str  # "이날" / "전 거래일 장 마감 후" — 장 마감 뒤 공시는 다음 날 주가에 반영되는 경우가 많다


class MoveTrend(BaseModel):
    foreign: int
    organ: int
    individual: int


class BigMove(BaseModel):
    date: datetime.date
    change_pct: float  # 전 거래일 종가 대비 %
    volume_ratio: float | None  # 거래량 ÷ 직전 20거래일 평균
    index_name: str  # 코스피 / 코스닥
    index_change_pct: float | None  # 같은 날 시장 지수 %
    scope: str  # market(시장 전체가 같이) / both(시장도 움직였지만 이 종목이 훨씬 더) / stock(이 종목만) / unknown
    scope_text: str  # 초보용 한 줄
    disclosures: list[MoveDisclosure] = []
    trend: MoveTrend | None = None  # 그날 투자자별 순매수 (최근 것만 있음)
    trend_text: str | None = None


class MovesResponse(BaseModel):
    available: bool
    message: str | None = None
    threshold_pct: float = 0  # 이만큼 넘게 오르내린 날을 "크게 움직인 날"로 봤다
    threshold_text: str | None = None
    moves: list[BigMove] = []  # 최신순
