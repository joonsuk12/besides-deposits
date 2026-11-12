"""Repository. Spring의 @Repository(JPA Repository)에 해당한다."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.report.models import Report


def find_by_date(db: Session, day: date) -> list[Report]:
    return list(db.scalars(select(Report).where(Report.write_date == day).order_by(Report.item_name, Report.broker)))


def find_by_stock(db: Session, code: str, limit: int) -> list[Report]:
    return list(
        db.scalars(
            select(Report).where(Report.item_code == code).order_by(Report.write_date.desc(), Report.nid.desc()).limit(limit)
        )
    )


def find_previous_goal(db: Session, report: Report) -> int | None:
    """같은 종목·같은 증권사의 바로 전 리포트 목표주가."""
    return db.scalar(
        select(Report.goal_price)
        .where(
            Report.item_code == report.item_code,
            Report.broker == report.broker,
            Report.write_date < report.write_date,
            Report.goal_price.is_not(None),
        )
        .order_by(Report.write_date.desc())
        .limit(1)
    )


def save_all(db: Session, reports: list[Report]) -> int:
    """없는 것만 넣는다. 새로 넣은 개수를 돌려준다."""
    if not reports:
        return 0
    existing = set(db.scalars(select(Report.nid).where(Report.nid.in_([r.nid for r in reports]))))
    new = [r for r in reports if r.nid not in existing]
    db.add_all(new)
    return len(new)
