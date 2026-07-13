from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, Text, Integer, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class VacancyDB(Base):
    """ORM-модель для хранения вакансий в SQLite (SQLAlchemy 2.0 Mapped)"""
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    key_skills: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    description_skills: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    parsed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<Vacancy(id={self.id}, title='{self.title[:40]}...', source='{self.source}')>"
