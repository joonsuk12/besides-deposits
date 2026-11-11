"""외부에서 주가를 가져오는 코드. NewStocks의 파이썬 pykrx 서버가 하던 일이다.

Spring으로 치면 외부 API를 부르는 Client 클래스(RestTemplate/WebClient 래퍼)에 해당한다.
DB는 건드리지 않고, 가져온 데이터를 돌려주기만 한다.

터미널에서 직접 실행하면 관심 종목 주가를 수집한다:
    python -m app.stock.collector
"""
from dataclasses import dataclass
from datetime import date

# 관심 종목 (종목코드: 이름)
WATCHLIST: dict[str, str] = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "000150": "두산",
    "168360": "펨트론",
}


@dataclass
class PriceRow:
    date: date
    open: int
    high: int
    low: int
    close: int
    volume: int


def fetch_daily_prices(code: str, start: date, end: date) -> list[PriceRow]:
    """일봉을 가져온다. pykrx가 실패하거나 비어 있으면 FinanceDataReader로 다시 시도한다."""
    try:
        rows = _fetch_from_pykrx(code, start, end)
        if rows:
            return rows
    except Exception as e:  # KRX 사이트가 바뀌면 pykrx가 깨질 수 있다
        print(f"  pykrx 실패({code}): {e!r} → FinanceDataReader로 재시도")
    return _fetch_from_fdr(code, start, end)


def _fetch_from_pykrx(code: str, start: date, end: date) -> list[PriceRow]:
    from pykrx import stock as krx

    df = krx.get_market_ohlcv(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), code)
    return [
        PriceRow(day.date(), int(r["시가"]), int(r["고가"]), int(r["저가"]), int(r["종가"]), int(r["거래량"]))
        for day, r in df.iterrows()
    ]


def _fetch_from_fdr(code: str, start: date, end: date) -> list[PriceRow]:
    import FinanceDataReader as fdr

    df = fdr.DataReader(code, start, end)
    return [
        PriceRow(day.date(), int(r["Open"]), int(r["High"]), int(r["Low"]), int(r["Close"]), int(r["Volume"]))
        for day, r in df.iterrows()
    ]


if __name__ == "__main__":
    from app.core.database import SessionLocal, create_tables
    from app.stock import service

    create_tables()
    with SessionLocal() as db:
        for result in service.collect_watchlist_prices(db):
            print(f"{result.name}({result.code}): {result.saved}일치 저장")
