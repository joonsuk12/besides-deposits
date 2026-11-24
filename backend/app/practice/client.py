"""외부 API Client. Spring으로 치면 외부 데이터를 가져오는 @Component다.

FinanceDataReader로 시장 지수 일별 종가를 받는다 (무료, 로그인 필요 없음). KS11 = 코스피, KQ11 = 코스닥.
pykrx(KRX 정보데이터시스템, 무료 회원 로그인)로 업종 지수 구성 종목, 지수 PER·PBR, 국고채 금리를 받는다.
"""
import datetime
from functools import wraps

from app.core import krx
from app.core.krx import use_login


def fetch_index(index_code: str, start: datetime.date) -> list[tuple[datetime.date, float]]:
    import FinanceDataReader as fdr

    df = fdr.DataReader(index_code, start.isoformat())
    return [(ts.date(), float(close)) for ts, close in zip(df.index, df["Close"]) if close == close]  # NaN 제외


def _krx():
    if not use_login():  # 계정이 없거나 KRX가 막혀 쉬는 중이면 부르지 않는다
        raise RuntimeError("KRX를 부를 수 없어요 (계정 없음 또는 잠깐 쉬는 중)")
    from pykrx import stock  # use_login() 다음에 import해야 로그인 정보를 읽는다

    return stock


def _guard(fn):
    """KRX 호출이 실패하면 이 프로세스에서 한동안 KRX를 부르지 않게 한다 (IP 차단이 길어지지 않게)."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if not krx.is_paused():
                krx.pause(repr(e)[:80])
            raise

    return wrapper


@_guard
def fetch_index_members(index_code: str) -> list[str]:
    stock = _krx()
    day = stock.get_nearest_business_day_in_a_week()
    return [str(c) for c in stock.get_index_portfolio_deposit_file(index_code, day)]


@_guard
def fetch_index_name(index_code: str) -> str:
    return _krx().get_index_ticker_name(index_code)


@_guard
def fetch_index_valuation(index_code: str, start: datetime.date, end: datetime.date) -> list[tuple]:
    """[(날짜, PER, PBR, 배당수익률)]. 값이 0이면(적자 등으로 계산 안 됨) None."""
    df = _krx().get_index_fundamental(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), index_code)
    out = []
    for ts, row in df.iterrows():
        val = [float(row.get(k) or 0) or None for k in ("PER", "PBR", "배당수익률")]
        out.append((ts.date(), *val))
    return out


@_guard
def fetch_bond_yields(kind: str, start: datetime.date, end: datetime.date) -> list[tuple[datetime.date, float]]:
    """kind: 국고채3년 / 국고채10년. [(날짜, 수익률 %)]"""
    if not use_login():
        raise RuntimeError("KRX를 부를 수 없어요 (계정 없음 또는 잠깐 쉬는 중)")
    from pykrx import bond

    df = bond.get_otc_treasury_yields(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), kind)
    return [(ts.date(), float(v)) for ts, v in zip(df.index, df["수익률"]) if v == v]
