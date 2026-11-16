"""Entity. Spring의 @Entity 클래스에 해당한다.

투자자별 매매동향: 하루에 외국인·기관·개인이 이 종목을 몇 주 사고(+) 팔았는지(-).
네이버가 한 번에 최근 60거래일만 주므로, 받을 때마다 DB에 쌓아 긴 기간을 만든다.
"""
import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InvestorTrend(Base):
    __tablename__ = "investor_trend"

    stock_code: Mapped[str] = mapped_column(primary_key=True)
    date: Mapped[datetime.date] = mapped_column(primary_key=True)  # 필드 이름과 타입 이름이 같아 datetime.date로 쓴다
    foreign: Mapped[int]  # 외국인 순매수 주식 수 (+ 산 쪽이 많음, - 판 쪽이 많음)
    organ: Mapped[int]  # 기관 순매수
    individual: Mapped[int]  # 개인 순매수
    foreign_ratio: Mapped[float | None]  # 외국인 보유 비율(%)
