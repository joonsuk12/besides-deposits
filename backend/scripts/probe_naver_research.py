"""네이버 리서치 내부 API 응답 형식 확인용 스크립트 (사용자가 직접 실행).

네이버 금융 리서치 화면이 내부적으로 부르는 API를 SK하이닉스 1건 기준으로 한 번씩만 호출해서,
응답 앞부분을 backend/data/probe_research.txt 에 저장한다. 수집 코드를 짜기 전에 응답 모양을 보려는 용도.

실행 (backend 폴더에서):
    .venv\\Scripts\\python scripts\\probe_naver_research.py
"""
from pathlib import Path

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://finance.naver.com/research/company_list.naver",
}
PATH = "/api/stockSecurity/researches/v2/company/by-items?itemCodes=000660&size=3"
HOSTS = ["https://finance.naver.com", "https://stock.naver.com", "https://m.stock.naver.com"]

out = Path(__file__).resolve().parents[1] / "data" / "probe_research.txt"
out.parent.mkdir(exist_ok=True)

lines = []
for host in HOSTS:
    try:
        r = requests.get(host + PATH, headers=HEADERS, timeout=10)
        lines.append(f"=== {host}  status={r.status_code}  type={r.headers.get('content-type')}")
        lines.append(r.text[:4000])
    except Exception as e:
        lines.append(f"=== {host}  error={e!r}")

out.write_text("\n".join(lines), encoding="utf-8")
print(f"저장했습니다: {out}")
