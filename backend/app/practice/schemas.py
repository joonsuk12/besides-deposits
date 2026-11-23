"""DTO. Spring의 Request/Response DTO에 해당한다."""
import datetime

from pydantic import BaseModel, Field

from app.stock.schemas import PriceResponse


class Option(BaseModel):
    key: str
    label: str


class Fact(BaseModel):
    """그 시점에 알 수 있었던 사실 한 줄."""

    label: str  # 예: "최근 3개월"
    value: str  # 예: "+12.3%"
    tone: str = ""  # up / down / "" (화면 색)
    hint: str | None = None  # 초보용 읽는 법


class YearRow(BaseModel):
    year: int
    revenue: float | None  # 억원
    operating_profit: float | None  # 억원
    net_income: float | None  # 억원


class QuestionResponse(BaseModel):
    available: bool
    message: str | None = None
    code: str | None = None
    name: str | None = None  # 정답을 보기 전에는 화면이 가린다 (기억에 기대지 않게)
    market: str | None = None
    industry: str | None = None
    as_of: datetime.date | None = None  # 이날까지의 정보만 보여준다
    horizon_label: str = "6개월"
    prices: list[PriceResponse] = []  # as_of까지 (최근 2년)
    price_facts: list[Fact] = []
    value_facts: list[Fact] = []  # 그 시점 PER·PBR (그때 나와 있던 사업보고서 기준)
    years: list[YearRow] = []  # 그때 나와 있던 연간 실적 (최근 3년)
    guesses: list[Option] = []
    reasons: list[Option] = []


class AnswerRequest(BaseModel):
    code: str = Field(max_length=12)
    as_of: datetime.date
    guess: str = Field(max_length=10)  # up / flat / down
    reasons: list[str] = Field(default=[], max_length=8)
    memo: str = Field(default="", max_length=500)


class AnswerResponse(BaseModel):
    name: str
    as_of: datetime.date
    end_date: datetime.date
    guess_label: str
    outcome: str  # up / flat / down
    outcome_label: str
    correct: bool
    return_pct: float
    index_name: str
    index_return_pct: float | None
    max_up_pct: float  # 그 기간 중 가장 많이 올랐을 때 (as_of 종가 대비)
    max_down_pct: float  # 그 기간 중 가장 많이 내렸을 때
    comment: str  # 결과 한두 문장 (권유 없이)
    prices: list[PriceResponse]  # as_of 2년 전 ~ end_date (결과까지 이어서)


class ReasonStat(BaseModel):
    key: str
    label: str
    total: int
    correct: int


class HistoryItem(BaseModel):
    created_at: datetime.datetime
    code: str | None
    name: str
    as_of: str
    guess_label: str
    outcome_label: str
    correct: bool
    return_pct: float


class HistoryResponse(BaseModel):
    total: int
    correct: int
    by_reason: list[ReasonStat]  # 이유를 골랐을 때 얼마나 맞았나 (내 판단 습관)
    items: list[HistoryItem]  # 최신순
