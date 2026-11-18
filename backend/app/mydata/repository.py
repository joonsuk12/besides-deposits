"""Repository. Spring의 @Repository(JPA Repository)에 해당한다."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.mydata.models import MyRecord


def save(db: Session, row: MyRecord) -> MyRecord:
    db.add(row)
    db.flush()  # id를 받으려고 (JPA save 후 id가 채워지는 것과 같다)
    return row


def find(db: Session, kind: str | None = None, stock_code: str | None = None, limit: int | None = None) -> list[MyRecord]:
    q = select(MyRecord).order_by(MyRecord.created_at.desc(), MyRecord.id.desc())
    if kind:
        q = q.where(MyRecord.kind == kind)
    if stock_code:
        q = q.where(MyRecord.stock_code == stock_code)
    if limit:
        q = q.limit(limit)
    return list(db.scalars(q))
