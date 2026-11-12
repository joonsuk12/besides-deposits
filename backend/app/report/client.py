"""네이버 증권 리서치에서 종목 리포트를 가져온다. Spring으로 치면 외부 API Client 클래스.

DB는 건드리지 않고, 가져온 데이터를 ReportRow로 돌려주기만 한다.
"""
from dataclasses import dataclass
from datetime import date

from app.core import naver

PAGE_SIZE = 50  # 네이버가 허용하는 최대치
MAX_PAGES = 10  # 하루치 리포트는 보통 수십 건이라 이 정도면 충분하다


@dataclass
class ReportRow:
    nid: str
    item_code: str
    item_name: str
    broker: str
    title: str
    write_date: date
    goal_price: int | None
    opinion: str | None
    opinion_type: str | None
    content_html: str


def fetch_by_date(day: date) -> list[ReportRow]:
    """그날 나온 종목 리포트 전부."""
    rows: list[ReportRow] = []
    for index in range(MAX_PAGES):
        data = naver.get_json(
            "/api/stockSecurity/researches/v2/company",
            {"index": index, "size": PAGE_SIZE, "startDate": day.isoformat(), "endDate": day.isoformat()},
        )
        rows += [_to_row(item) for item in data.get("items", [])]
        if not data.get("hasNext"):
            break
    return [r for r in rows if r is not None]


def fetch_by_stock(code: str, size: int = 10) -> list[ReportRow]:
    """한 종목의 최근 리포트."""
    data = naver.get_json("/api/stockSecurity/researches/v2/company/by-items", {"itemCodes": code, "size": size})
    return [r for r in (_to_row(item) for item in data.get(code, [])) if r is not None]


def _to_row(item: dict) -> ReportRow | None:
    if not item.get("itemCode"):
        return None
    opinion = item.get("opinionText")
    goal = item.get("goalPrice")
    return ReportRow(
        nid=str(item["nid"]),
        item_code=item["itemCode"],
        item_name=item.get("itemName") or "",
        broker=item.get("brokerName") or "",
        title=item.get("title") or "",
        write_date=date.fromisoformat(item["writeDate"]),
        goal_price=int(goal) if goal and str(goal).isdigit() and int(goal) > 0 else None,
        opinion=None if opinion in (None, "", "없음") else opinion,
        opinion_type=item.get("opinionType"),
        content_html=item.get("content") or "",
    )
