"""외부 API Client. Spring으로 치면 RestTemplate으로 외부 API를 부르는 @Component다.

네이버 증권 모바일 내부 API: /api/stock/{code}/trend?pageSize=60[&bizdate=YYYYMMDD]
- 한 번에 최대 60거래일. bizdate를 주면 그날 이전 60일을 준다 (더 과거로 넘겨 보기).
"""
import re
from dataclasses import dataclass
from datetime import date, datetime

from app.core import naver

PAGE_SIZE = 60


@dataclass
class TrendRow:
    date: date
    foreign: int
    organ: int
    individual: int
    foreign_ratio: float | None


def _int(text: str | None) -> int:
    return int(re.sub(r"[^0-9-]", "", text or "0") or 0)


def fetch_trend(code: str, before: date | None = None) -> list[TrendRow]:
    params: dict = {"pageSize": PAGE_SIZE}
    if before:
        params["bizdate"] = before.strftime("%Y%m%d")
    rows = naver.get_json(f"/api/stock/{code}/trend", params, base_url=naver.MOBILE_BASE_URL) or []
    out = []
    for r in rows:
        ratio = re.sub(r"[^0-9.]", "", r.get("foreignerHoldRatio") or "")
        out.append(
            TrendRow(
                date=datetime.strptime(r["bizdate"], "%Y%m%d").date(),
                foreign=_int(r.get("foreignerPureBuyQuant")),
                organ=_int(r.get("organPureBuyQuant")),
                individual=_int(r.get("individualPureBuyQuant")),
                foreign_ratio=float(ratio) if ratio else None,
            )
        )
    return out
