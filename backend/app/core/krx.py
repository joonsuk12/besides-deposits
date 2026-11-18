"""KRX(한국거래소) 로그인 설정. Spring으로 치면 외부 라이브러리를 위한 @Configuration이다.

pykrx는 KRX 정보데이터시스템에 로그인해야 데이터를 주는데, 아이디·비밀번호를 .env가 아니라
환경 변수(KRX_ID, KRX_PW)에서만 읽는다. 그래서 pykrx를 import하기 전에 settings(.env) 값을
환경 변수로 옮겨 준다. 값은 출력하지 않는다.
"""
import os

from app.core.config import settings


def use_login() -> bool:
    """KRX 계정이 설정돼 있으면 pykrx가 볼 수 있게 환경 변수로 넘긴다. 설정돼 있으면 True."""
    if not (settings.krx_id and settings.krx_pw):
        return False
    os.environ.setdefault("KRX_ID", settings.krx_id)
    os.environ.setdefault("KRX_PW", settings.krx_pw)
    return True
