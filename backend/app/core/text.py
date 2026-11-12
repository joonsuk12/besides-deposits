"""HTML·문장 처리 도우미. 리포트와 뉴스 키포인트 뽑기에서 같이 쓴다."""
import html
import re

_BREAKS = re.compile(r"<\s*(br|/p|/li|/div|/h\d)\s*/?\s*>", re.I)
_TAGS = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"[ \t ]+")
# "~다." "~함." "~음." 같은 문장 끝, 또는 마침표 뒤 공백에서 자른다
_SENTENCE_END = re.compile(r"(?<=[다음함임됨])\.\s+|(?<=\.)\s+(?=[가-힣A-Z‘'\"(\[])")


def html_to_lines(text: str) -> list[str]:
    """HTML을 줄 단위 평문으로 바꾼다."""
    text = _BREAKS.sub("\n", text or "")
    text = html.unescape(_TAGS.sub("", text))
    lines = (_SPACES.sub(" ", line).strip(" -·•■□▶►◆◇*") for line in text.split("\n"))
    return [line.strip() for line in lines if line.strip()]


def split_sentences(lines: list[str]) -> list[str]:
    sentences = []
    for line in lines:
        for s in _SENTENCE_END.split(line):
            s = s.strip()
            if len(s) >= 8:
                sentences.append(s)
    return sentences


def first_strong(text: str) -> str | None:
    """HTML에서 첫 번째 <strong> 안의 글 (증권사가 단 소제목)."""
    m = re.search(r"<strong[^>]*>(.*?)</strong>", text or "", re.S | re.I)
    if not m:
        return None
    s = html.unescape(_TAGS.sub("", m.group(1))).strip()
    return s or None


def shorten(s: str, limit: int) -> str:
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"
