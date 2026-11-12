"""네이버 증권에서 종목 뉴스를 가져온다. Spring으로 치면 외부 API Client 클래스.

네이버가 같은 사건을 다룬 기사를 묶음(cluster)으로 주므로, 묶음마다 대표 기사 하나와 묶인 기사 수를 돌려준다.
"""
from dataclasses import dataclass, field
from datetime import datetime

from app.core import naver

PAGE_SIZE = 20


@dataclass
class NewsRow:
    id: str
    office: str
    title: str
    body: str
    published_at: datetime
    url: str
    cluster_size: int
    related_titles: list[str] = field(default_factory=list)


def fetch_by_stock(code: str, pages: int = 2) -> list[NewsRow]:
    rows: list[NewsRow] = []
    for page in range(1, pages + 1):
        data = naver.get_json("/api/domestic/detail/news", {"itemCode": code, "page": page, "pageSize": PAGE_SIZE})
        clusters = data.get("clusters") or []
        for cluster in clusters:
            items = cluster.get("items") or []
            if not items:
                continue
            main = items[0]
            rows.append(
                NewsRow(
                    id=f"{main['officeId']}{main['articleId']}",
                    office=main.get("officeName") or "",
                    title=main.get("title") or "",
                    body=main.get("body") or "",
                    published_at=datetime.strptime(main["datetime"], "%Y%m%d%H%M"),
                    url=f"https://n.news.naver.com/article/{main['officeId']}/{main['articleId']}",
                    cluster_size=int(cluster.get("itemTotal") or len(items)),
                    related_titles=[i.get("title") or "" for i in items[1:]],
                )
            )
        if len(clusters) < PAGE_SIZE:
            break
    return rows
