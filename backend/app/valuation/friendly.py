"""회사 소개 문장을 초보가 읽기 편한 말투(해요체)로 바꾼다. 유료 AI 없이 문장 끝 규칙으로.

네이버 기업개요는 "동사는 ~를 영위하고 있음." 같은 보고서 말투라, 끝맺음과 주어만 바꾼다.
예) "동사는 1933년 설립되어 다수 계열사를 지배하고 있음." → "이 회사는 1933년 설립되어 다수 계열사를 지배하고 있어요."
뜻은 바꾸지 않고 말투만 바꾸므로, 어려운 단어("영위" 등)는 그대로 둔다.
"""
import re

# 문장 끝 → 해요체. 위에서부터 먼저 맞는 것 하나만 바꾼다 (긴 것을 앞에).
ENDINGS: tuple[tuple[str, str], ...] = (
    ("하고 있음", "하고 있어요"),
    ("되고 있음", "되고 있어요"),
    ("할 예정임", "할 예정이에요"),
    ("될 전망임", "될 전망이에요"),
    ("되었음", "되었어요"),
    ("하였음", "했어요"),
    ("했음", "했어요"),
    ("였음", "였어요"),
    ("있음", "있어요"),
    ("없음", "없어요"),
    ("같음", "같아요"),
    ("받음", "받아요"),
    ("높음", "높아요"),
    ("낮음", "낮아요"),
    ("많음", "많아요"),
    ("함", "해요"),
    ("됨", "돼요"),
)

SUBJECTS = (("동사는", "이 회사는"), ("동사의", "이 회사의"), ("동사가", "이 회사가"), ("당사는", "이 회사는"))


def _has_batchim(ch: str) -> bool:
    code = ord(ch) - 0xAC00
    return 0 <= code <= 11171 and code % 28 != 0


def friendly(sentence: str) -> str:
    s = sentence.strip()
    for a, b in SUBJECTS:
        s = s.replace(a, b)
    m = re.match(r"^(.*?)([.。]?)$", s, re.S)
    body, dot = m.group(1), m.group(2) or "."
    for old, new in ENDINGS:
        if body.endswith(old):
            return body[: -len(old)] + new + dot
    # "~사업자임" 같은 "명사+임" → 받침이 있으면 "이에요", 없으면 "예요"
    if body.endswith("임") and len(body) >= 2:
        prev = body[-2]
        return body[:-1] + ("이에요" if _has_batchim(prev) else "예요") + dot
    return body + dot
