"""KRX(한국거래소) 로그인 설정과 "잠깐 쉬기". Spring으로 치면 외부 라이브러리를 위한 @Configuration + 서킷 브레이커다.

pykrx는 KRX 정보데이터시스템에 로그인해야 데이터를 주는데, 아이디·비밀번호를 .env가 아니라
환경 변수(KRX_ID, KRX_PW)에서만 읽는다. 그래서 pykrx를 import하기 전에 settings(.env) 값을
환경 변수로 옮겨 준다. 값은 출력하지 않는다.

KRX는 짧은 시간에 로그인·요청이 몰리면 IP를 잠깐 막는다 (2026-11-24 실제로 막힘: "ip-block-page").
그래서 KRX 호출이 한 번 실패하면 이 프로세스에서는 PAUSE_MIN 동안 KRX를 부르지 않는다 (서킷 브레이커).
pykrx는 import할 때마다 로그인을 다시 시도하므로, 막혔을 때 계속 부르면 더 오래 막힐 수 있다.
"""
import os
import time

from app.core.config import settings

PAUSE_MIN = 60
_paused_until = 0.0


def use_login() -> bool:
    """KRX 계정이 설정돼 있고 쉬는 중이 아니면 pykrx가 볼 수 있게 환경 변수로 넘긴다."""
    if not (settings.krx_id and settings.krx_pw) or is_paused():
        return False
    os.environ.setdefault("KRX_ID", settings.krx_id)
    os.environ.setdefault("KRX_PW", settings.krx_pw)
    return True


def is_paused() -> bool:
    return time.time() < _paused_until


def pause(reason: str = "") -> None:
    """KRX 호출이 실패했을 때 부른다. PAUSE_MIN 동안 KRX를 부르지 않는다."""
    global _paused_until
    _paused_until = time.time() + PAUSE_MIN * 60
    print(f"  KRX 호출 {PAUSE_MIN}분 쉼{f': {reason}' if reason else ''}")
