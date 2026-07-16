from collections import Counter
from typing import List, Dict, Tuple

from database.models import VacancyDB


class DataAnalyzer:
    """Аналитик, работающий с данными из БД (Transform этап ETL)"""

    def __init__(self):
        self.tech_dictionary = {
            "python": "Python", "sql": "SQL", "scala": "Scala",
            "java": "Java", "go": "Go", "rust": "Rust",
            "bash": "Bash", "shell": "Shell", "r": "R",

            "postgresql": "PostgreSQL", "clickhouse": "ClickHouse",
            "greenplum": "Greenplum", "redis": "Redis",
            "mongodb": "MongoDB", "elasticsearch": "Elasticsearch",
            "cassandra": "Cassandra", "mysql": "MySQL", "oracle": "Oracle",

            "spark": "Apache Spark", "pyspark": "PySpark",
            "hadoop": "Hadoop", "kafka": "Apache Kafka",
            "airflow": "Apache Airflow", "dbt": "dbt",
            "nifi": "Apache NiFi", "luigi": "Luigi",
            "beam": "Apache Beam", "prefect": "Prefect",
            "dagster": "Dagster", "flink": "Apache Flink",

            "docker": "Docker", "kubernetes": "Kubernetes",
            "aws": "AWS", "gcp": "GCP", "azure": "Azure",
            "yandex cloud": "Yandex Cloud", "terraform": "Terraform",
            "ansible": "Ansible", "git": "Git", "ci/cd": "CI/CD",
            "jenkins": "Jenkins", "gitlab ci": "GitLab CI",

            "mlflow": "MLflow", "pandas": "Pandas", "numpy": "NumPy",
            "scikit-learn": "Scikit-learn", "pytorch": "PyTorch",
            "tensorflow": "TensorFlow",

            "etl": "ETL", "elt": "ELT", "dwh": "DWH",
            "data lake": "Data Lake", "data warehouse": "Data Warehouse",
            "data pipeline": "Data Pipeline",
            "great expectations": "Great Expectations",
        }

    def analyze_skills(self, vacancies: List[VacancyDB]) -> Dict[str, Tuple[int, float]]:
        """
        Анализирует навыки из БД и возвращает словарь:
        {skill_name: (count, percentage)}
        """
        all_skills = []
        total = len(vacancies)

        for v in vacancies:
            skills_list = (v.key_skills or []) + (v.description_skills or [])
            all_skills.extend([s.lower() for s in skills_list])

            if v.description:
                text_lower = v.description.lower()
                for pattern, canonical in self.tech_dictionary.items():
                    if pattern in text_lower:
                        all_skills.append(canonical.lower())

        skill_counts = Counter(all_skills)
        result = {}
        for skill, count in skill_counts.items():
            pct = (count / total) * 100 if total > 0 else 0
            result[skill] = (count, pct)
        return dict(sorted(result.items(), key=lambda x: x[1][0], reverse=True))

    @staticmethod
    def deduplicate_by_title(vacancies: List[VacancyDB]) -> List[VacancyDB]:
        """Удаляет дубликаты по схожести заголовков"""
        seen = set()
        unique = []
        for v in vacancies:
            norm = v.title.lower().strip()
            if norm not in seen:
                seen.add(norm)
                unique.append(v)
        return unique

    @staticmethod
    def get_salary_statistics(vacancies: List[VacancyDB]) -> dict:
        """
        Анализ зарплатных вилок с правильной обработкой нулевых значений.
        Игнорирует записи, где salary_min = 0 или None.
        """
        salaries = []
        for v in vacancies:
            if v.salary_min is not None and v.salary_min > 0:
                mn = v.salary_min
                mx = v.salary_max if v.salary_max is not None and v.salary_max > 0 else mn
                salaries.append((mn + mx) / 2)

        if not salaries:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}

        return {
            "count": len(salaries),
            "avg": sum(salaries) / len(salaries),
            "min": min(salaries),
            "max": max(salaries),
        }
