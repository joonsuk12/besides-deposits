"""Entity. Spring의 @Entity 클래스에 해당한다.

종목 하나의 '가치 지표 재료'를 저장한다. PER·PBR 자체보다 EPS·BPS를 저장해 두면
주가가 바뀌어도 그날 종가로 다시 계산할 수 있다.
"""
from datetime import datetime

from sqlalchemy import Text
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


class CompanyOverview(Base):
    """회사 소개 글과 연도별 실적·지표. 네이버에서 받은 것을 그대로 보관한다 (반나절에 한 번 갱신)."""

    __tablename__ = "company_overview"

    stock_code: Mapped[str] = mapped_column(primary_key=True)
    summary: Mapped[str] = mapped_column(Text, default="")  # 회사 소개 문장들 (줄바꿈 구분)
    annual_json: Mapped[str] = mapped_column(Text, default="[]")  # 연도별 숫자 (JSON 문자열)
    fetched_at: Mapped[datetime]


class AnnualFinancial(Base):
    """OpenDART 사업보고서의 연간 주요계정 (원 단위). 지난 해 숫자는 바뀌지 않아 한 번 받으면 계속 쓴다."""

    __tablename__ = "annual_financial"

    stock_code: Mapped[str] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    revenue: Mapped[float | None]
    operating_profit: Mapped[float | None]
    net_income: Mapped[float | None]  # 당기순이익 (비지배주주 몫 포함)
    equity: Mapped[float | None]  # 자본총계


class AnnualShares(Base):
    """그해 말 유통 주식 수 (OpenDART 사업보고서, 보통주+우선주). 연간 PER·PBR을 해마다의 주식 수로 계산하려고 둔다."""

    __tablename__ = "annual_shares"

    stock_code: Mapped[str] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    shares: Mapped[int]
