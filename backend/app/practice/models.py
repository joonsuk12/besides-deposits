"""Entity. Spring의 @Entity 클래스에 해당한다.

시장 지수(코스피·코스닥) 일별 종가. 타임머신 연습에서 "그 6개월 동안 시장 전체는 어땠나"와 비교하려고 둔다.
(2026-11-18 "오늘 왜 움직였지?" 때 만든 index_price 테이블을 그대로 쓴다.)
"""
import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IndexPrice(Base):
    __tablename__ = "index_price"

    index_code: Mapped[str] = mapped_column(primary_key=True)  # KS11(코스피) / KQ11(코스닥)
    date: Mapped[datetime.date] = mapped_column(primary_key=True)
    close: Mapped[float]
