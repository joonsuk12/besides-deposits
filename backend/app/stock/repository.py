"""Repository. Spring의 @Repository(JPA Repository)에 해당한다.

DB를 직접 건드리는 코드는 이 파일에만 둔다.
"""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.stock.models import DailyPrice, Stock


def count_stocks(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Stock)) or 0


def find_all_stocks(db: Session) -> list[Stock]:
    return list(db.scalars(select(Stock).order_by(Stock.name)))


def find_watched_stocks(db: Session) -> list[Stock]:
    return list(db.scalars(select(Stock).where(Stock.is_watched).order_by(Stock.name)))


def find_stock(db: Session, code: str) -> Stock | None:
    return db.get(Stock, code)


def save_stock_names(db: Session, rows: list[tuple[str, str, str]]) -> None:
    """(코드, 이름, 시장) 목록을 한꺼번에 넣는다. 있으면 이름·시장만 고치고 없으면 만든다."""
    existing = {s.code: s for s in db.scalars(select(Stock))}
    for code, name, market in rows:
        stock = existing.get(code)
        if stock is None:
            db.add(Stock(code=code, name=name, market=market))
        else:
            stock.name = name
            stock.market = market


def find_prices(db: Session, code: str, start: date) -> list[DailyPrice]:
    return list(
        db.scalars(
            select(DailyPrice)
            .where(DailyPrice.stock_code == code, DailyPrice.date >= start)
            .order_by(DailyPrice.date)
        )
    )


def find_recent_prices(db: Session, code: str, limit: int) -> list[DailyPrice]:
    """최근 limit일치 일봉. 최신 날짜가 먼저 온다."""
    return list(
        db.scalars(
            select(DailyPrice)
            .where(DailyPrice.stock_code == code)
            .order_by(DailyPrice.date.desc())
            .limit(limit)
        )
    )


def find_earliest_price_date(db: Session, code: str) -> date | None:
    return db.scalar(select(func.min(DailyPrice.date)).where(DailyPrice.stock_code == code))


def find_latest_price_date(db: Session, code: str) -> date | None:
    return db.scalar(select(func.max(DailyPrice.date)).where(DailyPrice.stock_code == code))


def save_prices(db: Session, prices: list[DailyPrice]) -> None:
    db.add_all(prices)
