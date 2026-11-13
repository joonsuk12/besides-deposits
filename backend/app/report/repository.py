"""Repository. Spring의 @Repository(JPA Repository)에 해당한다."""
from datetime import date

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.report.models import Report, ReportEasy


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


def find_easy(db: Session, nid: str) -> ReportEasy | None:
    return db.get(ReportEasy, nid)


def find_without_easy(db: Session, item_codes: list[str], since: date, limit: int) -> list[Report]:
    """쉬운 요약이 아직 없는 리포트. 관심 종목을 먼저, 그다음 최신순."""
    watched_first = case((Report.item_code.in_(item_codes), 0), else_=1)
    return list(
        db.scalars(
            select(Report)
            .outerjoin(ReportEasy, ReportEasy.nid == Report.nid)
            .where(ReportEasy.nid.is_(None), Report.write_date >= since)
            .order_by(watched_first, Report.write_date.desc(), Report.nid)
            .limit(limit)
        )
    )


def save_easy(db: Session, easy: ReportEasy) -> None:
    """있으면 덮어쓴다 (JPA의 merge)."""
    db.merge(easy)


def find_by_nid(db: Session, nid: str) -> Report | None:
    return db.get(Report, nid)
