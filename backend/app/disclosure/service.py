"""Service. Spring의 @Service에 해당한다.

- 처음 한 번: OpenDART에서 종목코드 ↔ DART 고유번호 대응표를 받아 저장한다.
- 종목 공시를 조회할 때 오래됐으면(6시간) OpenDART에서 새로 받아 저장하고, 초보용 분류를 붙여 돌려준다.
- 키가 없으면 오류 대신 available=False와 안내 문구를 돌려준다 (화면이 깨지지 않게).
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core import fetch_log
from app.core.config import settings
from app.disclosure import client, keypoints, repository
from app.disclosure.models import Disclosure
from app.disclosure.schemas import DisclosureListResponse, DisclosureResponse
from app.stock import repository as stock_repository

REFRESH_MIN = 360
FIRST_FETCH_DAYS = 365  # 처음 받을 때 1년치


def get_by_stock(db: Session, code: str, days: int) -> DisclosureListResponse:
    if not settings.dart_api_key:
        return DisclosureListResponse(
            available=False, message="OpenDART 인증키가 없어 공시를 불러올 수 없습니다. backend/.env에 DART_API_KEY를 넣어 주세요.", items=[]
        )
    message = None
    try:
        _collect(db, code)
    except client.DartError as e:  # 키 오류·한도 초과 등은 안내만 하고, 저장된 것으로 계속 간다
        db.rollback()
        message = str(e)
    except Exception as e:
        db.rollback()
        message = "공시를 새로 불러오지 못했습니다. 저장된 공시만 보여 줍니다."
        print(f"  공시 수집 실패({code}): {e!r}")

    since = date.today() - timedelta(days=days)
    items = [_to_response(d) for d in repository.find_by_stock(db, code, since)]
    return DisclosureListResponse(available=True, message=message, items=items)


def collect_watchlist(db: Session) -> int:
    """관심 종목 공시를 모두 새로 받는다 (매일 자동 수집용). 새로 저장한 개수."""
    total = 0
    for stock in stock_repository.find_watched_stocks(db):
        total += _collect(db, stock.code, force=True)
    return total


def _collect(db: Session, code: str, force: bool = False) -> int:
    key = f"disclosure:{code}"
    if not force and fetch_log.is_fresh(db, key, REFRESH_MIN):
        return 0
    _ensure_corp_codes(db)
    corp = repository.find_corp(db, code)
    if corp is None:  # ETF 등 DART에 회사로 등록되지 않은 종목
        fetch_log.mark_fetched(db, key)
        db.commit()
        return 0

    # 처음이면 1년치, 그다음부터는 최근 2주치만 다시 확인 (정정 공시가 늦게 붙는 경우 대비)
    first = fetch_log.is_fresh(db, key, 60 * 24 * 365 * 10) is False
    start = date.today() - timedelta(days=FIRST_FETCH_DAYS if first else 14)
    rows = client.fetch_disclosures(corp.corp_code, start, date.today())
    saved = repository.save_all(
        db,
        [
            Disclosure(
                rcept_no=r.rcept_no,
                stock_code=code,
                corp_name=r.corp_name,
                report_nm=r.report_nm,
                filer=r.filer,
                rcept_dt=r.rcept_dt,
                remark=r.remark,
            )
            for r in rows
        ],
    )
    fetch_log.mark_fetched(db, key)
    db.commit()
    return saved


def _ensure_corp_codes(db: Session) -> None:
    if repository.count_corps(db) == 0:
        repository.save_corps(db, client.fetch_corp_codes())
        db.commit()


def _to_response(d: Disclosure) -> DisclosureResponse:
    rule = keypoints.classify(d.report_nm)
    return DisclosureResponse(
        rcept_no=d.rcept_no,
        stock_code=d.stock_code,
        corp_name=d.corp_name,
        title=d.report_nm,
        filer=d.filer,
        date=d.rcept_dt,
        url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={d.rcept_no}",
        category=rule.category,
        level=rule.level,
        explain=rule.explain,
        is_correction=keypoints.is_correction(d.report_nm),
        by_company=d.filer.replace(" ", "") == d.corp_name.replace(" ", ""),
    )
