"""DTO. Spring의 Response DTO에 해당한다."""
import datetime

from pydantic import BaseModel


class DisclosureResponse(BaseModel):
    rcept_no: str
    stock_code: str
    corp_name: str
    title: str  # 보고서 이름 그대로
    filer: str
    date: datetime.date
    url: str  # DART 원문

    # 초보용 분류
    category: str  # 예: "유상증자", "실적 발표"
    level: str  # warn / good / key / info
    explain: str  # 쉬운 설명 한 줄
    is_correction: bool  # 정정 공시 여부
    by_company: bool  # 회사가 직접 낸 공시인지 (아니면 대주주·투자자가 낸 보고)


class DisclosureListResponse(BaseModel):
    available: bool  # OpenDART 키가 설정돼 있는지
    message: str | None = None  # 키가 없거나 오류가 났을 때 안내
    items: list[DisclosureResponse]
