"""DTO. Spring의 Response DTO에 해당한다."""
from pydantic import BaseModel


class Weight(BaseModel):
    name: str
    weight: float  # %
    code: str | None = None  # 담긴 종목이 상장 주식이면 종목코드 (눌러서 그 종목 차트로)


class LabeledValue(BaseModel):
    label: str  # 예: "1개월"
    value: str | float | None


class EtfResponse(BaseModel):
    available: bool
    message: str | None = None
    name: str | None = None
    base_index: str | None = None  # 따라가는 지수
    issuer: str | None = None  # 운용사
    listed_date: str | None = None  # YYYY-MM-DD
    summary: str | None = None  # 운용 목표 (한두 문장)
    total_fee: float | None = None  # 총보수 %/년
    deviation_rate: float | None = None  # 괴리율 % (+ 비싸게 / - 싸게 거래)
    tracking_error: float | None = None  # 추적오차 %
    total_nav: str | None = None  # 순자산 규모
    returns: list[LabeledValue] = []  # 기간 수익률 %
    holdings: list[Weight] = []  # 담긴 종목 TOP10
    assets: list[Weight] = []  # 자산 종류 비중 (주식·채권·현금·기타)
    sectors: list[Weight] = []  # 업종 비중
    dividend_yield: float | None = None  # 분배금 수익률 %/년
    dividend_months: str | None = None  # 분배금 주는 달
    inflows: list[LabeledValue] = []  # 기간별 자금 순유입
    notes: list[str] = []  # 초보용 한 줄 해설 (보수가 싼 편인지 등)
