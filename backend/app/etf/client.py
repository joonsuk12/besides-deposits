"""외부 API Client. Spring으로 치면 RestTemplate으로 외부 API를 부르는 @Component다.

네이버 증권 모바일 내부 API: /api/stock/{code}/etfAnalysis
따라가는 지수·운용사·보수·괴리율·추적오차·기간 수익률·담긴 종목 TOP10·업종/자산 비중·분배금·자금 유입이 한 번에 온다.
ETF가 아닌 종목이면 빈 응답이나 오류가 온다.
"""
from app.core import naver


def fetch_etf(code: str) -> dict | None:
    d = naver.get_json(f"/api/stock/{code}/etfAnalysis", base_url=naver.MOBILE_BASE_URL)
    return d if isinstance(d, dict) and d.get("itemCode") else None
