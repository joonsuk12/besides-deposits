"""Entity. Spring의 @Entity 클래스에 해당한다."""
from datetime import date, datetime

from sqlalchemy import ForeignKey, Text
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


class ReportEasy(Base):
    """리포트의 '쉽게 말하면' 요약. Claude가 초보 말투로 다시 쓴 것.

    리포트 테이블에 컬럼을 더하지 않고 따로 둔 이유: SQLite는 있는 테이블에 컬럼을 자동으로 붙여 주지 않고
    (JPA ddl-auto: update와 다름), 요약이 없는 리포트가 대부분이라 1:0..1 관계로 두는 게 자연스럽다.
    """

    __tablename__ = "report_easy"

    nid: Mapped[str] = mapped_column(ForeignKey("report.nid"), primary_key=True)
    one_liner: Mapped[str]  # 한 줄로 쉽게 (예: "메모리 값이 올라 이익이 크게 늘었다는 리포트예요")
    story: Mapped[str] = mapped_column(Text)  # 2~3문장 풀어 쓴 설명
    watch_out: Mapped[str | None] = mapped_column(Text)  # 초보가 오해하기 쉬운 점·주의할 점
    written_by: Mapped[str]  # 요약을 쓴 주체 (예: "claude-code")
    written_at: Mapped[datetime]
