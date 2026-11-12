"""DTO. Spring의 Response DTO에 해당한다."""
import datetime

from pydantic import BaseModel


class NewsResponse(BaseModel):
    id: str
    stock_code: str
    office: str
    title: str
    url: str
    published_at: datetime.datetime
    date: datetime.date  # 차트에 표시할 날짜

    # 키포인트
    summary: str  # 한 줄 요약
    cluster_size: int  # 같은 내용을 다룬 기사 수 (중요도)
    related_titles: list[str]
    tone: str  # good / bad / neutral (단어로 추정)
    topics: list[str]
