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
