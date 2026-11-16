"""Repository. Spring의 @Repository(JPA Repository)에 해당한다."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.valuation.models import CompanyOverview, Fundamental


def find(db: Session, code: str) -> Fundamental | None:
    return db.get(Fundamental, code)


def find_many(db: Session, codes: list[str]) -> list[Fundamental]:
    if not codes:
        return []
    return list(db.scalars(select(Fundamental).where(Fundamental.stock_code.in_(codes))))


def find_industry_name(db: Session, industry_code: str) -> str | None:
    """이미 받아 둔 같은 업종 회사에 업종 이름이 있으면 재사용한다."""
    return db.scalar(
        select(Fundamental.industry_name)
        .where(Fundamental.industry_code == industry_code, Fundamental.industry_name.is_not(None))
        .limit(1)
    )


def save(db: Session, row: Fundamental) -> None:
    db.merge(row)  # 있으면 덮어쓰고 없으면 넣는다 (JPA의 merge와 같다)


def find_overview(db: Session, code: str) -> CompanyOverview | None:
    return db.get(CompanyOverview, code)


def save_overview(db: Session, row: CompanyOverview) -> None:
    db.merge(row)
