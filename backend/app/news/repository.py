"""Repository. Spring의 @Repository(JPA Repository)에 해당한다."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.news.models import News


def find_by_stock(db: Session, code: str, since: datetime, limit: int) -> list[News]:
    return list(
        db.scalars(
            select(News)
            .where(News.stock_code == code, News.published_at >= since)
            .order_by(News.published_at.desc())
            .limit(limit)
        )
    )


def save_all(db: Session, items: list[News]) -> None:
    """있으면 묶음 크기만 갱신하고(기사가 늘어날 수 있다), 없으면 넣는다."""
    for item in items:
        existing = db.get(News, (item.id, item.stock_code))
        if existing is None:
            db.add(item)
        else:
            existing.cluster_size = max(existing.cluster_size, item.cluster_size)
            existing.related_titles = item.related_titles or existing.related_titles
