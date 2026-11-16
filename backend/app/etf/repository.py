"""Repository. Spring의 @Repository(JPA Repository)에 해당한다."""
from sqlalchemy.orm import Session

from app.etf.models import EtfInfo


def find(db: Session, code: str) -> EtfInfo | None:
    return db.get(EtfInfo, code)


def save(db: Session, row: EtfInfo) -> None:
    db.merge(row)
