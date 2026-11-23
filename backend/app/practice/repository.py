"""Repository. Spring의 @Repository(JPA Repository)에 해당한다."""
import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.practice.models import IndexPrice


def find_index_since(db: Session, index_code: str, since: datetime.date) -> list[IndexPrice]:
    return list(
        db.scalars(
            select(IndexPrice).where(IndexPrice.index_code == index_code, IndexPrice.date >= since).order_by(IndexPrice.date)
        )
    )


def find_index_latest_date(db: Session, index_code: str) -> datetime.date | None:
    return db.scalar(select(func.max(IndexPrice.date)).where(IndexPrice.index_code == index_code))


def save_index(db: Session, rows: list[IndexPrice]) -> None:
    for r in rows:
        db.merge(r)
