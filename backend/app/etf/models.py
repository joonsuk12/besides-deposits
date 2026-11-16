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
