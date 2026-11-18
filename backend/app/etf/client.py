"""외부 API Client. Spring으로 치면 RestTemplate으로 외부 API를 부르는 @Component다.

1) 네이버 증권 모바일 내부 API: /api/stock/{code}/etfAnalysis
   따라가는 지수·운용사·보수·괴리율·추적오차·기간 수익률·담긴 종목 TOP10·업종/자산 비중·분배금·자금 유입이 한 번에 온다.
   ETF가 아닌 종목이면 빈 응답이나 오류가 온다.
2) KRX 구성종목(PDF): pykrx로 받는다(로그인 필요). 국내 종목은 비중이 오지만 해외 종목은 비중이 0으로 온다.
3) 운용사 홈페이지 구성종목 표: 네이버·KRX 모두 비중이 비는 해외·액티브 ETF용. 지금은 TIME(타임폴리오)만.
"""
import html
import re

import requests

from app.core import naver
from app.core.krx import use_login

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
TIME_BASE = "https://timeetf.co.kr"


def fetch_etf(code: str) -> dict | None:
    d = naver.get_json(f"/api/stock/{code}/etfAnalysis", base_url=naver.MOBILE_BASE_URL)
    return d if isinstance(d, dict) and d.get("itemCode") else None


def fetch_krx_pdf(code: str) -> list[dict]:
    """KRX 구성종목. [{code, name, weight}] (비중 큰 순). 계정이 없으면 빈 목록."""
    if not use_login():
        return []
    from pykrx import stock as krx  # use_login() 다음에 import해야 로그인 정보를 읽는다

    df = krx.get_etf_portfolio_deposit_file(code)
    rows = [
        {"code": t if re.fullmatch(r"\d{6}", t) else None, "name": r["구성종목명"], "weight": float(r["비중"] or 0)}
        for t, r in df.iterrows()
    ]
    return sorted(rows, key=lambda r: -r["weight"])


def fetch_issuer_pdf(code: str, issuer: str | None, page_hint: str | None = None) -> tuple[list[dict], str | None]:
    """운용사 홈페이지 구성종목. ([{code, name, weight}], 찾은 페이지 번호). 지원하지 않는 운용사면 ([], None)."""
    if issuer and "타임폴리오" in issuer:
        return _fetch_time(code, page_hint)
    return [], None


def _fetch_time(code: str, page_hint: str | None) -> tuple[list[dict], str | None]:
    # 상품 페이지가 종목코드가 아니라 일련번호(idx)로 되어 있어, 라인업 목록의 상품을 하나씩 열어 코드를 찾는다
    candidates = [page_hint] if page_hint else []
    lineup = requests.get(f"{TIME_BASE}/m11.php", headers=UA, timeout=15).text
    candidates += [i for i in dict.fromkeys(re.findall(r"m11_view\.php\?idx=(\d+)", lineup)) if i != page_hint]
    for idx in candidates:
        page = requests.get(f"{TIME_BASE}/m11_view.php", params={"idx": idx}, headers=UA, timeout=15).text
        if code in page:
            return _parse_time_table(page), idx
    return [], None


def _parse_time_table(page: str) -> list[dict]:
    start = page.find('id="constituentItems"')
    if start < 0:
        return []
    body = page[start : page.find("</table>", start)]
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S):
        tds = [html.unescape(re.sub(r"<[^>]+>", "", td)).strip() for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(tds) < 5:
            continue
        try:
            weight = float(tds[4].replace(",", ""))
        except ValueError:
            continue
        ticker = tds[0]
        rows.append({"code": ticker if re.fullmatch(r"\d{6}|\d{4}[0-9A-Z]\d", ticker) else None, "name": tds[1], "weight": weight})
    return sorted(rows, key=lambda r: -r["weight"])
