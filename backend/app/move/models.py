"""Entity. Spring의 @Entity 클래스에 해당한다.

시장 지수(코스피·코스닥) 일별 종가. 종목이 크게 움직인 날 "시장 전체가 움직였나, 이 종목만 움직였나"를 보려고 둔다.
"""
import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IndexPrice(Base):
    __tablename__ = "index_price"

    index_code: Mapped[str] = mapped_column(primary_key=True)  # KS11(코스피) / KQ11(코스닥)
    date: Mapped[datetime.date] = mapped_column(primary_key=True)
    close: Mapped[float]
