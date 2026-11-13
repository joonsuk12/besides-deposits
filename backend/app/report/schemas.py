"""DTO. Spring의 Response DTO에 해당한다."""
import datetime

from pydantic import BaseModel, Field


class Term(BaseModel):
    term: str
    meaning: str


class EasySummary(BaseModel):
    """'쉽게 말하면' 요약. 저장할 때(요청)와 보여줄 때(응답) 같이 쓴다."""

    one_liner: str = Field(min_length=5, max_length=120)
    story: str = Field(min_length=10, max_length=600)
    watch_out: str | None = Field(default=None, max_length=300)


class EasySaveRequest(EasySummary):
    nid: str
    written_by: str = "claude-code"


class EasyPending(BaseModel):
    """아직 쉬운 요약이 없는 리포트. 요약을 쓰는 쪽(Claude)에게 넘기는 재료."""

    nid: str
    item_name: str
    broker: str
    write_date: datetime.date
    title: str
    opinion: str | None
    goal_price: int | None
    goal_change: str | None
    text: str  # 증권사 요약문 평문


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

    # Claude가 쓴 쉬운 말 요약 (아직 없으면 None)
    easy: EasySummary | None = None


class ReportFeedResponse(BaseModel):
    date: datetime.date
    total: int
    reports: list[ReportResponse]
