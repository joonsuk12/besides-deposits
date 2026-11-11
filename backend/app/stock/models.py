"""Entity. Spring의 @Entity 클래스에 해당한다."""
from datetime import date

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Stock(Base):
    """종목. 국내 상장 종목 전체가 들어 있고, 관심 종목은 is_watched로 표시한다."""

    __tablename__ = "stock"

    code: Mapped[str] = mapped_column(primary_key=True)  # 종목코드 6자리 (예: 005930)
    name: Mapped[str]
    market: Mapped[str] = mapped_column(default="")  # KOSPI / KOSDAQ / ETF
    is_watched: Mapped[bool] = mapped_column(default=False)  # 관심 종목 여부
    # 주가를 마지막으로 가져온 날. 같은 날 여러 번 외부에 요청하지 않으려고 둔다.
    prices_checked_on: Mapped[date | None] = mapped_column(default=None)


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
