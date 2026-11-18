"""외부 API Client. Spring으로 치면 외부 데이터를 가져오는 @Component다.

FinanceDataReader로 시장 지수 일별 종가를 받는다 (무료, 로그인 필요 없음).
KS11 = 코스피, KQ11 = 코스닥.
"""
import datetime


def fetch_index(index_code: str, start: datetime.date) -> list[tuple[datetime.date, float]]:
    import FinanceDataReader as fdr

    df = fdr.DataReader(index_code, start.isoformat())
    return [(ts.date(), float(close)) for ts, close in zip(df.index, df["Close"]) if close == close]  # NaN 제외
