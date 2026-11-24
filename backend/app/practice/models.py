"""Entity. Spring의 @Entity 클래스에 해당한다.

타임머신 연습에서 "그때 시장·업종·금리는 어땠나"를 보여주려고 모아 두는 시장 데이터.
- IndexPrice: 코스피·코스닥 일별 종가 (2026-11-18 만든 index_price 테이블을 그대로 쓴다)
- SectorMember: 종목 → KRX 업종 지수 (예: 삼성전자 → 전기전자). 한 달에 한 번 새로 만든다
- IndexValuation: KRX 지수(코스피·업종)의 일별 PER·PBR·배당수익률
- BondYield: 국고채 3년·10년 일별 금리
"""
import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IndexPrice(Base):
    __tablename__ = "index_price"

    index_code: Mapped[str] = mapped_column(primary_key=True)  # KS11(코스피) / KQ11(코스닥)
    date: Mapped[datetime.date] = mapped_column(primary_key=True)
    close: Mapped[float]


class SectorMember(Base):
    """종목이 속한 KRX 업종 지수. 여러 지수에 속하면 종목 수가 가장 적은(가장 좁은) 업종을 쓴다."""

    __tablename__ = "krx_sector_member"

    index_code: Mapped[str] = mapped_column(primary_key=True)  # 1013 (코스피 전기전자) 등
    stock_code: Mapped[str] = mapped_column(primary_key=True, index=True)
    index_name: Mapped[str]
    size: Mapped[int]  # 그 지수에 든 종목 수


class IndexValuation(Base):
    __tablename__ = "index_valuation"

    index_code: Mapped[str] = mapped_column(primary_key=True)  # 1001 코스피, 2001 코스닥, 업종 지수
    date: Mapped[datetime.date] = mapped_column(primary_key=True)
    per: Mapped[float | None]
    pbr: Mapped[float | None]
    dividend_yield: Mapped[float | None]


class BondYield(Base):
    __tablename__ = "bond_yield"

    kind: Mapped[str] = mapped_column(primary_key=True)  # 국고채3년 / 국고채10년
    date: Mapped[datetime.date] = mapped_column(primary_key=True)
    value: Mapped[float]  # %
