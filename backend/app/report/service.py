"""Service. Spring의 @Service에 해당한다.

- 리포트가 필요할 때 DB에 없거나 오래됐으면 네이버에서 가져와 저장한다 (조회할 때 수집).
- 저장된 리포트에 키포인트(한 줄 결론, 근거, 리스크, 용어)와 목표주가 변화를 붙여 DTO로 만든다.
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core import fetch_log
from app.report import client, keypoints, repository
from app.report.models import Report
from app.report.schemas import ReportFeedResponse, ReportResponse, Term
from app.stock import repository as stock_repository

# 같은 데이터를 다시 가져오기 전까지 기다리는 시간 (분)
TODAY_REFRESH_MIN = 30  # 오늘 리포트는 하루 동안 계속 올라오므로 30분마다
STOCK_REFRESH_MIN = 180


def get_feed(db: Session, day: date) -> ReportFeedResponse:
    """그날 나온 종목 리포트 전체."""
    _collect_day(db, day)
    reports = repository.find_by_date(db, day)
    return ReportFeedResponse(date=day, total=len(reports), reports=[_to_response(db, r) for r in reports])


def get_by_stock(db: Session, code: str, limit: int) -> list[ReportResponse]:
    key = f"reports:stock:{code}"
    if not fetch_log.is_fresh(db, key, STOCK_REFRESH_MIN):
        try:
            repository.save_all(db, [_to_entity(row) for row in client.fetch_by_stock(code)])
            fetch_log.mark_fetched(db, key)
            db.commit()
        except Exception as e:  # 네이버 장애로 화면 전체가 죽지 않게, 저장된 것으로 계속 간다
            db.rollback()
            print(f"  리포트 수집 실패({code}): {e!r}")
    return [_to_response(db, r) for r in repository.find_by_stock(db, code, limit)]


def collect_recent_days(db: Session, days: int) -> int:
    """최근 며칠치 리포트를 한꺼번에 받아 둔다 (처음 한 번, 또는 매일 자동 실행용)."""
    total = 0
    for i in range(days):
        total += _collect_day(db, date.today() - timedelta(days=i), force=(i == 0))
    return total


def _collect_day(db: Session, day: date, force: bool = False) -> int:
    if day > date.today():
        return 0
    key = f"reports:day:{day.isoformat()}"
    # 지난 날짜는 한 번 받으면 끝, 오늘은 30분마다 새로 확인
    if not force and fetch_log.is_fresh(db, key, TODAY_REFRESH_MIN if day == date.today() else 60 * 24 * 365):
        return 0
    try:
        saved = repository.save_all(db, [_to_entity(row) for row in client.fetch_by_date(day)])
        fetch_log.mark_fetched(db, key)
        db.commit()
        return saved
    except Exception as e:
        db.rollback()
        print(f"  리포트 수집 실패({day}): {e!r}")
        return 0


def _to_entity(row: client.ReportRow) -> Report:
    return Report(**row.__dict__)


def _to_response(db: Session, r: Report) -> ReportResponse:
    kp = keypoints.extract(r.content_html, r.title)

    prev_goal = repository.find_previous_goal(db, r) if r.goal_price else None
    if r.goal_price is None:
        goal_change = None
    elif prev_goal is None:
        goal_change = "처음"
    else:
        goal_change = "상향" if r.goal_price > prev_goal else "하향" if r.goal_price < prev_goal else "유지"

    recent = stock_repository.find_recent_prices(db, r.item_code, limit=1)
    close = recent[0].close if recent else None
    gap = round((r.goal_price - close) / close * 100, 1) if close and r.goal_price else None

    return ReportResponse(
        nid=r.nid,
        item_code=r.item_code,
        item_name=r.item_name,
        broker=r.broker,
        title=r.title,
        write_date=r.write_date,
        url=f"https://stock.naver.com/research/company/{r.nid}",
        opinion=keypoints.opinion_label(r.opinion, r.opinion_type),
        opinion_type=r.opinion_type if r.opinion else None,
        goal_price=r.goal_price,
        prev_goal_price=prev_goal,
        goal_change=goal_change,
        close=close,
        gap_pct=gap,
        headline=kp.headline,
        points=kp.points,
        risks=kp.risks,
        terms=[Term(term=t, meaning=m) for t, m in kp.terms],
    )
