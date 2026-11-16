"""외부 API Client (OpenDART 재무제표). Spring으로 치면 RestTemplate으로 외부 API를 부르는 @Component다.

연간 흐름을 네이버(최근 3년)보다 길게 보려고, 공시(사업보고서)에 나온 숫자를 OpenDART에서 받는다. 공식·무료.
- fnlttSinglAcnt   : 단일회사 주요계정 (매출액·영업이익·당기순이익·자본총계). 연결(CFS)을 먼저, 없으면 개별(OFS)
- stockTotqySttus  : 주식 총수 (유통 주식 수)
키는 공시 도메인과 같은 DART_API_KEY를 쓴다.
"""
import re
from dataclasses import dataclass

import requests

from app.disclosure.client import BASE_URL, DartError, _key

ANNUAL_REPORT = "11011"  # 사업보고서
ACCOUNTS = {"매출액": "revenue", "영업이익": "operating_profit", "당기순이익(손실)": "net_income", "당기순이익": "net_income", "자본총계": "equity"}


@dataclass
class AnnualAccounts:
    year: int
    revenue: float | None  # 원
    operating_profit: float | None
    net_income: float | None
    equity: float | None


def _num(text: str | None) -> float | None:
    if not text or text.strip() in ("", "-"):
        return None
    try:
        return float(re.sub(r"[^0-9.-]", "", text))
    except ValueError:
        return None


def _get(path: str, corp_code: str, year: int) -> list[dict]:
    res = requests.get(
        f"{BASE_URL}/{path}",
        params={"crtfc_key": _key(), "corp_code": corp_code, "bsns_year": year, "reprt_code": ANNUAL_REPORT},
        timeout=15,
    )
    res.raise_for_status()
    d = res.json()
    if d.get("status") == "013":  # 데이터 없음 (그해 사업보고서가 없거나 아직 안 나옴)
        return []
    if d.get("status") != "000":
        raise DartError(f"{d.get('status')} {d.get('message')}")
    return d.get("list") or []


def fetch_annual(corp_code: str, year: int) -> AnnualAccounts | None:
    rows = _get("fnlttSinglAcnt.json", corp_code, year)
    if not rows:
        return None
    # 연결재무제표(자회사 포함)가 있으면 그것을, 없으면 회사 하나만의 재무제표를
    fs = "CFS" if any(r.get("fs_div") == "CFS" for r in rows) else "OFS"
    values: dict[str, float | None] = {}
    for r in rows:
        key = ACCOUNTS.get(r.get("account_nm", ""))
        if r.get("fs_div") == fs and key and key not in values:
            values[key] = _num(r.get("thstrm_amount"))
    return AnnualAccounts(year=year, **{k: values.get(k) for k in ("revenue", "operating_profit", "net_income", "equity")})


def fetch_shares(corp_code: str, year: int) -> int | None:
    """그해 말 유통 주식 수(발행 주식 − 자기주식), 보통주+우선주 합계."""
    for r in _get("stockTotqySttus.json", corp_code, year):
        if r.get("se") == "합계":
            n = _num(r.get("distb_stock_co"))
            return int(n) if n else None
    return None
