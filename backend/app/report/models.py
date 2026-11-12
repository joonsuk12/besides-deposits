"""Entity. Spring의 @Entity 클래스에 해당한다."""
from datetime import date

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Report(Base):
    """증권사 종목 리포트 한 건 (네이버 증권 리서치 > 종목분석)."""

    __tablename__ = "report"

    nid: Mapped[str] = mapped_column(primary_key=True)  # 네이버 리서치 글 번호
    item_code: Mapped[str] = mapped_column(index=True)  # 종목코드
    item_name: Mapped[str]
    broker: Mapped[str]  # 증권사
    title: Mapped[str]
    write_date: Mapped[date] = mapped_column(index=True)
    goal_price: Mapped[int | None]  # 목표주가 (없으면 None)
    opinion: Mapped[str | None]  # 증권사가 쓴 투자의견 원문 (Buy, 매수, Hold …)
    opinion_type: Mapped[str | None]  # buy / neutral / sell
    content_html: Mapped[str] = mapped_column(Text)  # 증권사가 쓴 요약문 (HTML)
