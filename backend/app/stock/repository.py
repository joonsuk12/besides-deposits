"""Repository. Spring의 @Repository(JPA Repository)에 해당한다.

DB를 직접 건드리는 코드는 이 파일에만 둔다.
"""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.stock.models import DailyPrice, Stock


def find_all_stocks(db: Session) -> list[Stock]:
    return list(db.scalars(select(Stock).order_by(Stock.name)))


def find_stock(db: Session, code: str) -> Stock | None:
    return db.get(Stock, code)


def save_stock(db: Session, code: str, name: str, is_watched: bool) -> Stock:
    """있으면 고치고 없으면 만든다 (JPA의 save와 같다)."""
    stock = db.get(Stock, code)
    if stock is None:
        stock = Stock(code=code)
        db.add(stock)
    stock.name = name
    stock.is_watched = is_watched
    return stock


def find_prices(db: Session, code: str, start: date) -> list[DailyPrice]:
    return list(
        db.scalars(
            select(DailyPrice)
            .where(DailyPrice.stock_code == code, DailyPrice.date >= start)
            .order_by(DailyPrice.date)
        )
    )


def find_latest_price_date(db: Session, code: str) -> date | None:
    return db.scalar(select(func.max(DailyPrice.date)).where(DailyPrice.stock_code == code))


def save_prices(db: Session, prices: list[DailyPrice]) -> None:
    db.add_all(prices)
