"""DTO. Spring의 Response DTO에 해당한다."""
import datetime

from pydantic import BaseModel


class Term(BaseModel):
    term: str
    meaning: str


class ReportResponse(BaseModel):
    nid: str
    item_code: str
    item_name: str
    broker: str
    title: str
    write_date: datetime.date
    url: str  # 네이버 리서치 원문 (PDF 링크가 있는 화면)

    # 숫자로 보는 핵심
    opinion: str | None  # 예: "매수 (Buy)"
    opinion_type: str | None  # buy / neutral / sell
    goal_price: int | None
    prev_goal_price: int | None  # 같은 증권사의 직전 목표주가
    goal_change: str | None  # "상향" / "하향" / "유지" / "처음" (목표주가가 없으면 None)
    close: int | None  # 우리 DB에 있는 최근 종가 (관심·조회한 종목만)
    gap_pct: float | None  # 최근 종가 대비 목표주가 차이 (%)

    # 글에서 뽑은 핵심
    headline: str | None  # 한 줄 결론
    points: list[str]  # 핵심 근거
    risks: list[str]  # 조심할 점
    terms: list[Term]  # 용어 풀이


class ReportFeedResponse(BaseModel):
    date: datetime.date
    total: int
    reports: list[ReportResponse]
