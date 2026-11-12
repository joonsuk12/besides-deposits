"""네이버 증권 내부 API 호출. Spring으로 치면 외부 API를 부르는 공용 Client(RestTemplate 래퍼)다.

공개 API가 아니라 네이버 증권 웹페이지가 내부적으로 쓰는 주소다 (사용자가 개인용·저빈도 조건으로 허용, 2026-11-12).
- 요청 사이에 쉬는 시간을 둬서 짧은 시간에 몰아서 부르지 않는다.
- 같은 데이터는 fetch_log로 일정 시간 다시 부르지 않는다 (service에서 처리).
- 네이버가 주소나 응답 모양을 바꾸면 여기와 각 도메인의 client.py만 고치면 된다.
"""
import time

import requests

BASE_URL = "https://stock.naver.com"
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://stock.naver.com/"}
REQUEST_GAP_SECONDS = 0.5

_last_request_at = 0.0


def get_json(path: str, params: dict | list | None = None):
    global _last_request_at
    wait = REQUEST_GAP_SECONDS - (time.monotonic() - _last_request_at)
    if wait > 0:
        time.sleep(wait)
    try:
        res = requests.get(BASE_URL + path, params=params, headers=HEADERS, timeout=10)
    finally:
        _last_request_at = time.monotonic()
    res.raise_for_status()
    return res.json()
