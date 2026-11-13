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
    """있으면 묶음 크기만 갱신하고(기사가 늘어날 수 있다), 없으면 넣는다.

    네이버는 같은 기사를 여러 묶음에 넣어 줄 때가 있다. db.get은 DB에 이미 저장된 것만 찾고
    방금 add한 것은 못 찾으므로(flush 전), 한 번에 받은 목록 안의 중복은 여기서 먼저 합친다.
    """
    unique: dict[tuple[str, str], News] = {}
    for item in items:
        key = (item.id, item.stock_code)
        if key in unique:
            unique[key].cluster_size = max(unique[key].cluster_size, item.cluster_size)
        else:
            unique[key] = item

    for item in unique.values():
        existing = db.get(News, (item.id, item.stock_code))
        if existing is None:
            db.add(item)
        else:
            existing.cluster_size = max(existing.cluster_size, item.cluster_size)
            existing.related_titles = item.related_titles or existing.related_titles
