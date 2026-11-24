"""Repository. Spring의 @Repository(JPA Repository)에 해당한다."""
import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.practice.models import BondYield, IndexPrice, IndexValuation, SectorMember


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


def find_sector(db: Session, stock_code: str) -> SectorMember | None:
    """가장 좁은(종목 수가 적은) 업종."""
    return db.scalars(
        select(SectorMember).where(SectorMember.stock_code == stock_code).order_by(SectorMember.size)
    ).first()


def replace_sector_members(db: Session, rows: list[SectorMember]) -> None:
    db.query(SectorMember).delete()
    db.add_all(rows)


def find_index_valuation(db: Session, index_code: str, start: datetime.date, end: datetime.date) -> list[IndexValuation]:
    return list(
        db.scalars(
            select(IndexValuation)
            .where(IndexValuation.index_code == index_code, IndexValuation.date >= start, IndexValuation.date <= end)
            .order_by(IndexValuation.date)
        )
    )


def save_index_valuation(db: Session, rows: list[IndexValuation]) -> None:
    for r in rows:
        db.merge(r)


def find_bond_yields(db: Session, kind: str, start: datetime.date, end: datetime.date) -> list[BondYield]:
    return list(
        db.scalars(
            select(BondYield)
            .where(BondYield.kind == kind, BondYield.date >= start, BondYield.date <= end)
            .order_by(BondYield.date)
        )
    )


def save_bond_yields(db: Session, rows: list[BondYield]) -> None:
    for r in rows:
        db.merge(r)
