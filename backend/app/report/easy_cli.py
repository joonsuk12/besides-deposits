"""'쉽게 말하면' 요약을 서버 없이 다루는 명령줄 도구. Spring으로 치면 CommandLineRunner.

예약 작업(Claude Code)이 백엔드 서버가 꺼져 있어도 DB에 직접 읽고 쓰도록 만든 입구다.
안에서 하는 일은 API(router)와 똑같이 service를 부르는 것뿐이다.

    # 오늘 리포트를 수집한 뒤, 요약이 없는 리포트를 JSON 파일로 내보내기 (관심 종목 먼저, 최근 3일, 최대 30건)
    python -m app.report.easy_cli pending data/easy_pending.json --days 3 --limit 30

    # Claude가 쓴 요약 JSON 파일을 저장하기 ([{nid, one_liner, story, watch_out}, ...])
    python -m app.report.easy_cli save data/easy_written.json
"""
import argparse
import json
from pathlib import Path

from app.core.database import SessionLocal, create_tables
from app.report import service
from app.report.schemas import EasySaveRequest


def main() -> None:
    parser = argparse.ArgumentParser(prog="easy_cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pending")
    p.add_argument("out")
    p.add_argument("--days", type=int, default=3)
    p.add_argument("--limit", type=int, default=30)
    s = sub.add_parser("save")
    s.add_argument("file")
    args = parser.parse_args()

    create_tables()
    with SessionLocal() as db:
        if args.cmd == "pending":
            # 서버를 아무도 열어 보지 않은 날에도 오늘 리포트가 DB에 있도록 먼저 수집한다
            new = service.collect_recent_days(db, 1)
            if new:
                print(f"오늘 리포트 {new}건 새로 수집")
            items = service.get_easy_pending(db, args.days, args.limit)
            Path(args.out).write_text(
                json.dumps([i.model_dump(mode="json") for i in items], ensure_ascii=False, indent=1), encoding="utf-8"
            )
            print(f"요약할 리포트 {len(items)}건 → {args.out}")
        else:
            raw = json.loads(Path(args.file).read_text(encoding="utf-8"))
            saved = service.save_easy(db, [EasySaveRequest(**r) for r in raw])
            print(f"쉬운 요약 {saved}건 저장")


if __name__ == "__main__":
    main()
