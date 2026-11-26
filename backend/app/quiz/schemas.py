"""DTO. Spring의 Request/Response DTO에 해당한다."""
import datetime

from pydantic import BaseModel, Field


class QuizOption(BaseModel):
    key: str
    label: str


class QuizResult(BaseModel):
    """답을 낸 뒤 보여줄 정답과 해설."""

    correct: bool
    chosen_key: str
    correct_key: str
    correct_label: str
    explanation: str  # 왜 그게 답인지
    checks: list[str] = []  # 원문·화면에서 더 확인해 볼 것
    note: str | None = None  # 흔한 착각, 참고 (그 뒤 주가 등)
    link: str | None = None  # 공시 원문 등


class QuizQuestion(BaseModel):
    qid: str  # 문제를 다시 만들 수 있는 열쇠 (유형|종목|참조)
    type: str
    type_label: str
    stock_code: str
    stock_name: str
    prompt: str
    context: list[str] = []  # 문제를 풀 때 볼 숫자·사실
    options: list[QuizOption]
    result: QuizResult | None = None  # 오늘 이미 푼 문제면 결과


class TodayResponse(BaseModel):
    day: datetime.date
    questions: list[QuizQuestion]
    done: int  # 오늘 문제 중 푼 개수


class AnswerRequest(BaseModel):
    qid: str = Field(max_length=120)
    choice: str = Field(max_length=40)


class TypeStat(BaseModel):
    type: str
    label: str
    total: int
    correct: int


class WrongItem(BaseModel):
    created_at: datetime.datetime
    type_label: str
    stock_name: str
    prompt: str
    correct_label: str


class StatsResponse(BaseModel):
    total: int
    correct: int
    streak: int  # 며칠 연속으로 풀었나 (오늘 또는 어제까지 이어진 날 수)
    days: int  # 푼 날 수
    by_type: list[TypeStat]
    recent_wrong: list[WrongItem]  # 다시 볼 것 (최근 틀린 문제)
    lines: list[str]  # 한 줄 돌아보기
