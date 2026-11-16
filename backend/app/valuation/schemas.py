"""DTO. Spring의 Request/Response DTO에 해당한다."""
from datetime import date

from pydantic import BaseModel


class PeerValuation(BaseModel):
    code: str
    name: str
    per: float | None
    pbr: float | None


class ValuationResponse(BaseModel):
    available: bool
    message: str | None = None  # ETF처럼 지표가 없을 때 안내
    price: int | None = None  # 계산에 쓴 주가 (우리 DB의 최근 종가)
    price_date: date | None = None
    eps: float | None = None
    bps: float | None = None
    per: float | None = None  # = price ÷ eps (적자면 None)
    pbr: float | None = None  # = price ÷ bps
    cns_per: float | None = None  # 증권사 예상 이익 기준 PER
    industry_name: str | None = None
    industry_per: float | None = None  # 같은 업종 주요 회사들의 중간값
    industry_pbr: float | None = None
    per_gap_pct: float | None = None  # (내 PER ÷ 업종 PER - 1) × 100
    pbr_gap_pct: float | None = None
    per_comment: str | None = None
    pbr_comment: str | None = None
    focus: str | None = None  # per / pbr / both / none: 이 업종에서 더 보는 지표
    focus_title: str | None = None
    focus_reason: str | None = None
    focus_also: list[str] = []  # PER·PBR과 함께 볼 것
    focus_caution: str | None = None  # 이 업종에서 흔한 착각
    peers: list[PeerValuation] = []


class YearValuation(BaseModel):
    label: str  # "2025.12"
    is_estimate: bool  # 증권사 예상치인지
    per: float | None  # 적자인 해는 None
    pbr: float | None
    eps: float | None
    bps: float | None
    revenue: float | None  # 매출액 (억원)
    operating_profit: float | None  # 영업이익 (억원)
    roe: float | None  # %
    dividend: float | None  # 주당배당금 (원)


class OverviewResponse(BaseModel):
    available: bool
    message: str | None = None
    summary: list[str] = []  # 회사 소개 문장들
    industry_name: str | None = None
    years: list[YearValuation] = []
    trend_comment: str | None = None  # 연도별 흐름을 한두 문장으로
