"""OpenDART(금융감독원 전자공시 공식 API) 호출. Spring으로 치면 외부 API Client 클래스.

공식·무료 API이고 인증키가 필요하다 (.env의 DART_API_KEY). 하루 2만 번까지 부를 수 있다.
- corpCode.xml : 전체 회사의 고유번호 목록 (zip 안에 XML) → 종목코드와 연결
- list.json    : 회사별 공시 목록
"""
import io
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from datetime import date

import requests

from app.core.config import settings

BASE_URL = "https://opendart.fss.or.kr/api"


class DartError(Exception):
    """OpenDART가 오류 상태를 돌려줬을 때 (키 없음·잘못된 키·한도 초과 등)."""


@dataclass
class DisclosureRow:
    rcept_no: str
    corp_name: str
    report_nm: str
    filer: str
    rcept_dt: date
    remark: str


def _key() -> str:
    if not settings.dart_api_key:
        raise DartError("OpenDART 인증키가 없습니다. backend/.env에 DART_API_KEY를 넣어 주세요.")
    return settings.dart_api_key


def fetch_corp_codes() -> list[tuple[str, str, str]]:
    """상장사의 (종목코드, 고유번호, 회사명) 목록."""
    res = requests.get(f"{BASE_URL}/corpCode.xml", params={"crtfc_key": _key()}, timeout=60)
    res.raise_for_status()
    try:
        archive = zipfile.ZipFile(io.BytesIO(res.content))
    except zipfile.BadZipFile:
        # 키가 틀리면 zip 대신 오류 XML/JSON이 온다
        raise DartError(f"회사 목록을 받지 못했습니다: {res.text[:200]}")
    root = ET.fromstring(archive.read(archive.namelist()[0]))
    rows = []
    for item in root.iter("list"):
        stock_code = (item.findtext("stock_code") or "").strip()
        if stock_code:  # 비상장사는 종목코드가 비어 있다
            rows.append((stock_code, item.findtext("corp_code").strip(), (item.findtext("corp_name") or "").strip()))
    return rows


def fetch_disclosures(corp_code: str, start: date, end: date) -> list[DisclosureRow]:
    """한 회사의 기간 내 공시 목록 (최신순)."""
    rows: list[DisclosureRow] = []
    page = 1
    while True:
        res = requests.get(
            f"{BASE_URL}/list.json",
            params={
                "crtfc_key": _key(),
                "corp_code": corp_code,
                "bgn_de": start.strftime("%Y%m%d"),
                "end_de": end.strftime("%Y%m%d"),
                "page_no": page,
                "page_count": 100,
            },
            timeout=15,
        )
        res.raise_for_status()
        data = res.json()
        status = data.get("status")
        if status == "013":  # 조회된 데이터 없음
            return rows
        if status != "000":
            raise DartError(f"OpenDART 오류 {status}: {data.get('message')}")
        for item in data.get("list", []):
            d = item["rcept_dt"]
            rows.append(
                DisclosureRow(
                    rcept_no=item["rcept_no"],
                    corp_name=item.get("corp_name", ""),
                    report_nm=" ".join((item.get("report_nm") or "").split()),
                    filer=item.get("flr_nm", ""),
                    rcept_dt=date(int(d[:4]), int(d[4:6]), int(d[6:])),
                    remark=item.get("rm", ""),
                )
            )
        if page >= int(data.get("total_page") or 1):
            return rows
        page += 1
