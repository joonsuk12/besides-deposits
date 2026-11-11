"""Entity. Spring의 @Entity 클래스에 해당한다."""
from datetime import date

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Stock(Base):
    """종목."""

    __tablename__ = "stock"

    code: Mapped[str] = mapped_column(primary_key=True)  # 종목코드 6자리 (예: 005930)
    name: Mapped[str]
    is_watched: Mapped[bool] = mapped_column(default=False)  # 관심 종목 여부


class DailyPrice(Base):
    """일봉 (하루치 시가·고가·저가·종가·거래량)."""

    __tablename__ = "daily_price"
    __table_args__ = (UniqueConstraint("stock_code", "date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_code: Mapped[str] = mapped_column(ForeignKey("stock.code"), index=True)
    date: Mapped[date]
    open: Mapped[int]
    high: Mapped[int]
    low: Mapped[int]
    close: Mapped[int]
    volume: Mapped[int]
