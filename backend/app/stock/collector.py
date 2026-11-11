"""외부에서 종목 목록과 주가를 가져오는 코드. NewStocks의 파이썬 pykrx 서버가 하던 일이다.

Spring으로 치면 외부 API를 부르는 Client 클래스(RestTemplate/WebClient 래퍼)에 해당한다.
DB는 건드리지 않고, 가져온 데이터를 돌려주기만 한다.

터미널에서 직접 실행하면 종목 목록을 새로 받고 관심 종목 주가를 수집한다:
    python -m app.stock.collector
"""
from dataclasses import dataclass
from datetime import date

# 처음 실행할 때 관심 종목으로 넣어 둘 종목코드. 이후에는 화면의 ★로 넣고 뺀다.
DEFAULT_WATCHLIST = ["005930", "000660", "000150", "168360"]


@dataclass
class PriceRow:
    date: date
    open: int
    high: int
    low: int
    close: int
    volume: int


def fetch_stock_list() -> list[tuple[str, str, str]]:
    """국내 상장 종목과 ETF의 (코드, 이름, 시장) 목록."""
    import FinanceDataReader as fdr

    rows: list[tuple[str, str, str]] = []
    krx = fdr.StockListing("KRX")
    for code, name, market in zip(krx["Code"], krx["Name"], krx["Market"]):
        if market.startswith(("KOSPI", "KOSDAQ")):
            rows.append((code, name, "KOSDAQ" if market.startswith("KOSDAQ") else "KOSPI"))
    try:
        etf = fdr.StockListing("ETF/KR")
        rows += [(code, name, "ETF") for code, name in zip(etf["Symbol"], etf["Name"])]
    except Exception as e:  # ETF 목록은 없어도 서비스가 돌아가므로 넘어간다
        print(f"  ETF 목록 실패: {e!r}")
    return rows


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
        print(f"종목 목록: {service.sync_stock_list(db)}개")
        for result in service.collect_watchlist_prices(db):
            print(f"{result.name}({result.code}): {result.saved}일치 저장")
