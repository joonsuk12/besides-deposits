"""Service. Spring의 @Service에 해당한다.

업무 규칙(종목이 없으면 404, 어디서부터 수집할지 등)을 여기에 둔다.
router는 이 파일의 함수만 부르고, 이 파일은 repository와 collector만 부른다.
"""
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.stock import collector, repository
from app.stock.models import DailyPrice, Stock
from app.stock.schemas import CollectResult

# 처음 수집할 때 가져올 기간
INITIAL_YEARS = 3


def get_stocks(db: Session) -> list[Stock]:
    return repository.find_all_stocks(db)


def get_prices(db: Session, code: str, days: int) -> list[DailyPrice]:
    if repository.find_stock(db, code) is None:
        # Spring에서 커스텀 예외를 던지고 @ExceptionHandler가 404로 바꾸는 것과 같다.
        raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {code}")
    start = date.today() - timedelta(days=days)
    return repository.find_prices(db, code, start)


def collect_watchlist_prices(db: Session) -> list[CollectResult]:
    """관심 종목의 일봉을 수집한다. 이미 저장된 날짜 다음 날부터만 가져온다."""
    today = date.today()
    results = []
    for code, name in collector.WATCHLIST.items():
        repository.save_stock(db, code, name, is_watched=True)

        latest = repository.find_latest_price_date(db, code)
        start = latest + timedelta(days=1) if latest else today - timedelta(days=365 * INITIAL_YEARS)

        rows = collector.fetch_daily_prices(code, start, today) if start <= today else []
        # 거래정지일처럼 시가가 0인 날은 차트를 망가뜨려서 뺀다.
        prices = [
            DailyPrice(stock_code=code, date=r.date, open=r.open, high=r.high, low=r.low, close=r.close, volume=r.volume)
            for r in rows
            if r.open > 0 and (latest is None or r.date > latest)
        ]
        repository.save_prices(db, prices)
        db.commit()  # 종목 하나가 끝날 때마다 확정 (@Transactional의 커밋 시점)
        results.append(CollectResult(code=code, name=name, saved=len(prices)))
    return results
