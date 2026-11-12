"""Service. Spring의 @Service에 해당한다.

종목 뉴스를 조회할 때 오래됐으면 네이버에서 새로 받아 저장하고, 키포인트를 붙여 돌려준다.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core import fetch_log
from app.news import client, keypoints, repository
from app.news.models import News
from app.news.schemas import NewsResponse

REFRESH_MIN = 30


def get_by_stock(db: Session, code: str, days: int, limit: int) -> list[NewsResponse]:
    key = f"news:{code}"
    if not fetch_log.is_fresh(db, key, REFRESH_MIN):
        try:
            rows = client.fetch_by_stock(code)
            repository.save_all(
                db,
                [
                    News(
                        id=r.id,
                        stock_code=code,
                        office=r.office,
                        title=r.title,
                        body=r.body,
                        published_at=r.published_at,
                        url=r.url,
                        cluster_size=r.cluster_size,
                        related_titles="\n".join(t for t in r.related_titles if t),
                    )
                    for r in rows
                ],
            )
            fetch_log.mark_fetched(db, key)
            db.commit()
        except Exception as e:  # 네이버 장애로 화면 전체가 죽지 않게, 저장된 것으로 계속 간다
            db.rollback()
            print(f"  뉴스 수집 실패({code}): {e!r}")

    since = datetime.now() - timedelta(days=days)
    return [_to_response(n) for n in repository.find_by_stock(db, code, since, limit)]


def _to_response(n: News) -> NewsResponse:
    return NewsResponse(
        id=n.id,
        stock_code=n.stock_code,
        office=n.office,
        title=n.title,
        url=n.url,
        published_at=n.published_at,
        date=n.published_at.date(),
        summary=keypoints.summary(n.body),
        cluster_size=n.cluster_size,
        related_titles=[t for t in n.related_titles.split("\n") if t],
        tone=keypoints.tone(n.title, n.body),
        topics=keypoints.topics(n.title, n.body),
    )
