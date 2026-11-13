"""Repository. Spring의 @Repository(JPA Repository)에 해당한다."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.disclosure.models import DartCorp, Disclosure


def count_corps(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(DartCorp)) or 0


def find_corp(db: Session, stock_code: str) -> DartCorp | None:
    return db.get(DartCorp, stock_code)


def save_corps(db: Session, rows: list[tuple[str, str, str]]) -> None:
    for stock_code, corp_code, corp_name in rows:
        db.merge(DartCorp(stock_code=stock_code, corp_code=corp_code, corp_name=corp_name))


def find_by_stock(db: Session, stock_code: str, since: date) -> list[Disclosure]:
    return list(
        db.scalars(
            select(Disclosure)
            .where(Disclosure.stock_code == stock_code, Disclosure.rcept_dt >= since)
            .order_by(Disclosure.rcept_dt.desc(), Disclosure.rcept_no.desc())
        )
    )


def save_all(db: Session, items: list[Disclosure]) -> int:
    if not items:
        return 0
    existing = set(db.scalars(select(Disclosure.rcept_no).where(Disclosure.rcept_no.in_([d.rcept_no for d in items]))))
    new = [d for d in items if d.rcept_no not in existing]
    db.add_all(new)
    return len(new)
