"""외부 API Client. Spring으로 치면 RestTemplate으로 외부 API를 부르는 @Component다.

네이버 증권 모바일 내부 API에서 종목 지표(EPS·BPS·PER·PBR)와 같은 업종 비교 회사 목록을 받는다.
- /api/stock/{code}/integration : 지표 + industryCode + industryCompareInfo(같은 업종 주요 회사 6곳 안팎)
- /api/stocks/industry/{no}     : 업종 이름 (groupInfo.name)
"""
import re
from dataclasses import dataclass, field

from app.core import naver


@dataclass
class FundamentalRow:
    code: str
    name: str
    price: int | None
    eps: float | None
    bps: float | None
    per: float | None
    pbr: float | None
    cns_per: float | None
    industry_code: str | None
    peer_codes: list[str] = field(default_factory=list)


def _num(text: str | None) -> float | None:
    """'22,292원', '9.38배', '-1.2배' → 숫자. 'N/A'나 '-'는 None."""
    if not text:
        return None
    m = re.search(r"-?[\d,]+(\.\d+)?", text)
    return float(m.group().replace(",", "")) if m else None


def fetch_fundamental(code: str) -> FundamentalRow:
    d = naver.get_json(f"/api/stock/{code}/integration", base_url=naver.MOBILE_BASE_URL)
    info = {t.get("code"): t.get("value") for t in d.get("totalInfos") or []}
    price = _num(info.get("lastClosePrice"))
    return FundamentalRow(
        code=code,
        name=d.get("stockName") or code,
        price=int(price) if price else None,
        eps=_num(info.get("eps")),
        bps=_num(info.get("bps")),
        per=_num(info.get("per")),
        pbr=_num(info.get("pbr")),
        cns_per=_num(info.get("cnsPer")),
        industry_code=str(d["industryCode"]) if d.get("industryCode") else None,
        peer_codes=[p["itemCode"] for p in d.get("industryCompareInfo") or [] if p.get("itemCode") != code],
    )


def fetch_industry_name(industry_code: str) -> str | None:
    d = naver.get_json(
        f"/api/stocks/industry/{industry_code}", {"page": 1, "pageSize": 1}, base_url=naver.MOBILE_BASE_URL
    )
    return (d.get("groupInfo") or {}).get("name")
