"""Entity. Spring의 @Entity 클래스에 해당한다.

ETF 정보(따라가는 지수, 보수, 담긴 종목 등). 네이버가 주는 JSON을 그대로 보관하고,
화면에 보낼 모양으로 바꾸는 일은 service가 한다 (항목이 많고 자주 바뀌지 않아 컬럼으로 나누지 않았다).
"""
from datetime import datetime

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EtfInfo(Base):
    __tablename__ = "etf_info"

    stock_code: Mapped[str] = mapped_column(primary_key=True)
    raw_json: Mapped[str] = mapped_column(Text)  # 네이버 etfAnalysis 응답 그대로
    fetched_at: Mapped[datetime]


class EtfHoldings(Base):
    """네이버가 비중을 비워 주는 ETF의 구성종목 비중 (KRX나 운용사 홈페이지에서 받은 것)."""

    __tablename__ = "etf_holdings"

    stock_code: Mapped[str] = mapped_column(primary_key=True)
    source: Mapped[str]  # "KRX" / "운용사 홈페이지"
    page_hint: Mapped[str | None]  # 운용사 홈페이지의 상품 번호 (다음에 바로 찾아가려고)
    raw_json: Mapped[str] = mapped_column(Text)  # [{code, name, weight}] 비중 큰 순
    fetched_at: Mapped[datetime]
