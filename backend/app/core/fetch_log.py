"""외부 데이터를 언제 마지막으로 가져왔는지 기록한다. 같은 데이터를 너무 자주 요청하지 않으려는 용도.

Spring으로 치면 작은 Entity + Repository 한 벌이다. 여러 도메인(report, news)이 같이 쓴다.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base


class FetchLog(Base):
    __tablename__ = "fetch_log"

    key: Mapped[str] = mapped_column(primary_key=True)  # 예: "news:005930", "reports:2026-11-12"
    fetched_at: Mapped[datetime]


def is_fresh(db: Session, key: str, minutes: int) -> bool:
    """minutes분 안에 가져온 적이 있으면 True."""
    log = db.get(FetchLog, key)
    return log is not None and datetime.now() - log.fetched_at < timedelta(minutes=minutes)


def mark_fetched(db: Session, key: str) -> None:
    log = db.get(FetchLog, key)
    if log is None:
        db.add(FetchLog(key=key, fetched_at=datetime.now()))
    else:
        log.fetched_at = datetime.now()
