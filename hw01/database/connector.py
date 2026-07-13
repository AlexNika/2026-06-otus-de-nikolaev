from contextlib import contextmanager
from typing import List, Tuple

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker, Session

from models.vacancy import Vacancy
from .models import Base, VacancyDB


class DatabaseManager:
    def __init__(self, db_path: str = "vacancies.db"):
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    @contextmanager
    def get_session(self):
        session: Session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_vacancies(self, vacancies: List[Vacancy], source: str) -> Tuple[int, int]:
        """
        Сохраняет вакансии в БД.
        Возвращает кортеж: (количество_сохраненных, количество_дубликатов)
        """
        saved_count = 0
        skipped_count = 0

        with self.get_session() as session:
            for v in vacancies:
                ext_id = v.external_id or f"{source}_{hash(v.title)}"

                stmt = select(VacancyDB).where(
                    VacancyDB.external_id == ext_id,
                    VacancyDB.source == source
                )
                existing = session.execute(stmt).scalar_one_or_none()

                if existing:
                    skipped_count += 1
                    continue

                db_vac = VacancyDB(
                    source=source,
                    external_id=ext_id,
                    title=v.title,
                    key_skills=v.key_skills,
                    description_skills=v.description_skills,
                    description=v.description,
                    salary_min=v.salary.min_value if v.salary else None,
                    salary_max=v.salary.max_value if v.salary else None,
                    salary_currency=v.salary.currency if v.salary else None,
                    url=v.url,
                )
                session.add(db_vac)
                saved_count += 1

        return saved_count, skipped_count

    def get_all_vacancies(self) -> List[VacancyDB]:
        with self.get_session() as session:
            stmt = select(VacancyDB)
            return list(session.execute(stmt).scalars().all())

    def get_vacancies_by_source(self) -> dict[str, int]:
        with self.get_session() as session:
            stmt = select(
                VacancyDB.source,
                func.count(VacancyDB.id)
            ).group_by(VacancyDB.source)
            results = session.execute(stmt).all()
            return {str(row[0]): int(row[1]) for row in results}
