"""Entity. Spring의 @Entity 클래스에 해당한다.

종목 하나의 '가치 지표 재료'를 저장한다. PER·PBR 자체보다 EPS·BPS를 저장해 두면
주가가 바뀌어도 그날 종가로 다시 계산할 수 있다.
"""
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Fundamental(Base):
    __tablename__ = "fundamental"

    stock_code: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[int | None]  # 네이버가 PER을 계산할 때 쓴 주가 (전일 종가)
    eps: Mapped[float | None]  # 주당순이익: 1년 순이익 ÷ 주식 수
    bps: Mapped[float | None]  # 주당순자산: 회사 순자산 ÷ 주식 수
    per: Mapped[float | None]  # 네이버가 계산한 PER (업종 비교용)
    pbr: Mapped[float | None]
    cns_per: Mapped[float | None]  # 증권사 예상 이익 기준 PER (추정PER)
    industry_code: Mapped[str | None]
    industry_name: Mapped[str | None]
    peer_codes: Mapped[str] = mapped_column(default="")  # 네이버가 고른 같은 업종 비교 회사들 (쉼표 구분)
    fetched_at: Mapped[datetime]
