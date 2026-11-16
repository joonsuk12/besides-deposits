"""Repository. Spring의 @Repository(JPA Repository)에 해당한다."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.trend.models import InvestorTrend


def find_since(db: Session, code: str, since: date) -> list[InvestorTrend]:
    return list(
        db.scalars(
            select(InvestorTrend)
            .where(InvestorTrend.stock_code == code, InvestorTrend.date >= since)
            .order_by(InvestorTrend.date)
        )
    )


def find_earliest_date(db: Session, code: str) -> date | None:
    return db.scalar(select(func.min(InvestorTrend.date)).where(InvestorTrend.stock_code == code))


def save_all(db: Session, rows: list[InvestorTrend]) -> None:
    for r in rows:
        db.merge(r)  # 같은 날이 이미 있으면 덮어쓴다 (장중에 받은 값이 마감 뒤 바뀔 수 있다)
