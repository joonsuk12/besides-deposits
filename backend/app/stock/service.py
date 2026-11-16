"""Service. Spring의 @Service에 해당한다.

업무 규칙(종목이 없으면 404, 어디서부터 수집할지 등)을 여기에 둔다.
router는 이 파일의 함수만 부르고, 이 파일은 repository와 collector만 부른다.
"""
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import fetch_log
from app.stock import collector, repository
from app.stock.models import DailyPrice, Stock
from app.stock.schemas import CollectResult, WatchlistItem

# 처음 수집할 때 가져올 기간. 차트를 줌 아웃하면 주봉·월봉·연봉으로 바뀌어서 긴 기간이 필요하다 (2026-11-16, 3년 → 10년)
INITIAL_YEARS = 10


def init_stock_data(db: Session) -> None:
    """서버가 처음 뜰 때 한 번: 종목 목록이 비어 있으면 받아 오고 기본 관심 종목을 표시한다."""
    if repository.count_stocks(db) > 0:
        return
    sync_stock_list(db)
    for code in collector.DEFAULT_WATCHLIST:
        stock = repository.find_stock(db, code)
        if stock:
            stock.is_watched = True
    db.commit()


def sync_stock_list(db: Session) -> int:
    """국내 상장 종목·ETF 목록을 새로 받아 DB에 반영한다. 반영한 종목 수를 돌려준다."""
    rows = collector.fetch_stock_list()
    repository.save_stock_names(db, rows)
    db.commit()
    return len(rows)


def get_stocks(db: Session) -> list[Stock]:
    return repository.find_all_stocks(db)


def get_stock(db: Session, code: str) -> Stock:
    stock = repository.find_stock(db, code)
    if stock is None:
        # Spring에서 커스텀 예외를 던지고 @ExceptionHandler가 404로 바꾸는 것과 같다.
        raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {code}")
    return stock


def set_watched(db: Session, code: str, watched: bool) -> Stock:
    """관심 종목에 넣거나 뺀다."""
    stock = get_stock(db, code)
    stock.is_watched = watched
    db.commit()
    return stock


def get_watchlist(db: Session) -> list[WatchlistItem]:
    items = []
    for stock in repository.find_watched_stocks(db):
        _collect_prices(db, stock)
        recent = repository.find_recent_prices(db, stock.code, limit=2)
        last = recent[0] if recent else None
        prev = recent[1] if len(recent) > 1 else None
        change = last.close - prev.close if last and prev else None
        items.append(
            WatchlistItem(
                code=stock.code,
                name=stock.name,
                market=stock.market,
                date=last.date if last else None,
                close=last.close if last else None,
                change=change,
                change_pct=round(change / prev.close * 100, 2) if change is not None else None,
            )
        )
    return items


def get_prices(db: Session, code: str, days: int) -> list[DailyPrice]:
    stock = get_stock(db, code)
    # 검색해서 처음 들어온 종목은 주가가 없으므로, 조회할 때 가져와 저장한다.
    _collect_prices(db, stock)
    start = date.today() - timedelta(days=days)
    return repository.find_prices(db, code, start)


def collect_watchlist_prices(db: Session) -> list[CollectResult]:
    """관심 종목의 일봉을 지금 수집한다."""
    return [
        CollectResult(code=stock.code, name=stock.name, saved=_collect_prices(db, stock, force=True))
        for stock in repository.find_watched_stocks(db)
    ]


def _collect_prices(db: Session, stock: Stock, force: bool = False) -> int:
    """종목 하나의 일봉을 마지막 저장일 다음 날부터 오늘까지 가져와 저장한다. 저장한 개수를 돌려준다.

    오늘 이미 확인한 종목은 다시 요청하지 않는다 (force=True면 무조건 요청).
    """
    today = date.today()
    if stock.prices_checked_on == today and not force:
        return _backfill_prices(db, stock)  # 오늘 확인했어도 과거 채우기는 아직일 수 있다

    latest = repository.find_latest_price_date(db, stock.code)
    start = latest + timedelta(days=1) if latest else today - timedelta(days=365 * INITIAL_YEARS)
    try:
        rows = collector.fetch_daily_prices(stock.code, start, today) if start <= today else []
    except Exception as e:
        # 외부 사이트 장애로 화면 전체가 죽지 않게, 저장된 데이터로 계속 간다.
        print(f"  주가 수집 실패({stock.code}): {e!r}")
        return 0

    # 거래정지일처럼 시가가 0인 날은 차트를 망가뜨려서 뺀다.
    prices = [
        DailyPrice(stock_code=stock.code, date=r.date, open=r.open, high=r.high, low=r.low, close=r.close, volume=r.volume)
        for r in rows
        if r.open > 0 and (latest is None or r.date > latest)
    ]
    repository.save_prices(db, prices)
    stock.prices_checked_on = today
    db.commit()  # 종목 하나가 끝날 때마다 확정 (@Transactional의 커밋 시점)
    return len(prices) + _backfill_prices(db, stock)


def _backfill_prices(db: Session, stock: Stock) -> int:
    """예전에 3년치만 받아 둔 종목은 10년치가 되도록 앞쪽을 한 번만 채운다.

    상장한 지 10년이 안 된 종목은 앞쪽 데이터가 원래 없으므로, 한 번 시도한 뒤에는 fetch_log로 다시 부르지 않는다.
    """
    key = f"prices-backfill:{stock.code}"
    if fetch_log.is_fresh(db, key, minutes=60 * 24 * 365 * 100):  # 한 번 하면 끝
        return 0
    earliest = repository.find_earliest_price_date(db, stock.code)
    target = date.today() - timedelta(days=365 * INITIAL_YEARS)
    saved = 0
    if earliest and earliest > target + timedelta(days=30):
        try:
            rows = collector.fetch_daily_prices(stock.code, target, earliest - timedelta(days=1))
        except Exception as e:
            print(f"  과거 주가 수집 실패({stock.code}): {e!r}")
            return 0
        prices = [
            DailyPrice(stock_code=stock.code, date=r.date, open=r.open, high=r.high, low=r.low, close=r.close, volume=r.volume)
            for r in rows
            if r.open > 0 and r.date < earliest
        ]
        repository.save_prices(db, prices)
        saved = len(prices)
    fetch_log.mark_fetched(db, key)
    db.commit()
    return saved
