"""매일 한 번 돌리는 수집. Spring으로 치면 @Scheduled 메서드 하나를 밖에서 부르는 진입점이다.

관심 종목의 주가·뉴스·공시와 오늘 나온 증권사 리포트를 한꺼번에 받아 둔다.
서버가 꺼져 있어도 되고, 화면을 열지 않은 날에도 데이터가 쌓인다.
윈도우 작업 스케줄러가 레포 루트의 daily_collect.cmd로 이것을 부른다.

    python -m app.daily
"""
from datetime import datetime

from app.core.database import SessionLocal, create_tables
from app.disclosure import service as disclosure_service
from app.news import service as news_service
from app.practice import service as practice_service
from app.report import service as report_service
from app.stock import repository as stock_repository
from app.stock import service as stock_service
from app.trend import service as trend_service


def main() -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] 매일 수집 시작")
    create_tables()
    with SessionLocal() as db:
        steps = [
            ("주가", lambda: sum(r.saved for r in stock_service.collect_watchlist_prices(db))),
            ("오늘 리포트", lambda: report_service.collect_recent_days(db, 1)),
            ("뉴스", lambda: sum(len(news_service.get_by_stock(db, s.code, 1, 300)) for s in stock_repository.find_watched_stocks(db))),
            ("공시", lambda: disclosure_service.collect_watchlist(db)),
            # 매매동향은 네이버가 최근 60일만 주므로 매일 받아 두면 긴 기간이 쌓인다
            ("매매동향", lambda: sum(len(trend_service.get_by_stock(db, s.code, 7).items) for s in stock_repository.find_watched_stocks(db))),
            # 타임머신 연습용: 업종 PER·PBR, 금리 10년치 (KRX). 문제를 낼 때 KRX에 묻지 않게 미리 받아 둔다
            ("업종 PER·PBR·금리", lambda: practice_service.refresh_market_history(db)),
        ]
        for name, step in steps:
            # 하나가 실패해도 나머지는 계속한다
            try:
                print(f"  {name}: {step()}건")
            except Exception as e:
                db.rollback()
                print(f"  {name}: 실패 {e!r}")
    print("끝")


if __name__ == "__main__":
    main()
