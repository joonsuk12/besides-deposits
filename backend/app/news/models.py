"""Entity. Spring의 @Entity 클래스에 해당한다."""
from datetime import datetime

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class News(Base):
    """종목 뉴스 묶음의 대표 기사.

    네이버는 같은 사건을 다룬 기사들을 하나로 묶어서 준다. 대표 기사 하나만 저장하고,
    묶음에 든 기사 수(cluster_size)를 함께 저장한다. 여러 언론사가 다룰수록 중요한 뉴스로 본다.
    """

    __tablename__ = "news"

    id: Mapped[str] = mapped_column(primary_key=True)  # 언론사ID + 기사ID
    stock_code: Mapped[str] = mapped_column(primary_key=True, index=True)  # 같은 기사가 여러 종목에 걸릴 수 있다
    office: Mapped[str]  # 언론사
    title: Mapped[str]
    body: Mapped[str] = mapped_column(Text)  # 앞부분 요약 (네이버가 주는 미리보기)
    published_at: Mapped[datetime] = mapped_column(index=True)
    url: Mapped[str]
    cluster_size: Mapped[int] = mapped_column(default=1)  # 같은 내용을 다룬 기사 수
    related_titles: Mapped[str] = mapped_column(Text, default="")  # 묶인 다른 기사 제목들 (줄바꿈 구분)
