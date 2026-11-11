"""DTO. Spring의 Request/Response DTO에 해당한다.

Pydantic 모델은 타입만 적어 두면 검증과 JSON 변환을 알아서 해 준다.
from_attributes=True 는 Entity 객체를 그대로 DTO로 바꿀 수 있게 하는 설정이다 (MapStruct 역할).
"""
import datetime

from pydantic import BaseModel, ConfigDict


class StockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    market: str
    is_watched: bool


class PriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: datetime.date
    open: int
    high: int
    low: int
    close: int
    volume: int


class WatchlistItem(BaseModel):
    """관심 종목 한 줄: 종목 + 최근 종가와 전날 대비 변화."""

    code: str
    name: str
    market: str
    date: datetime.date | None  # 최근 종가 날짜 (주가가 아직 없으면 None)
    close: int | None
    change: int | None  # 전날 종가 대비 (원)
    change_pct: float | None  # 전날 종가 대비 (%)


class CollectResult(BaseModel):
    code: str
    name: str
    saved: int  # 새로 저장한 일봉 개수
