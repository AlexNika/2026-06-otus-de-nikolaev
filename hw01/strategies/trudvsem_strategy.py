import re
from typing import List, Optional

import requests

from models.vacancy import Vacancy, Salary
from strategies.base_strategy import JobParserStrategy


def _parse_salary_from_text(text: str) -> Optional[Salary]:
    """Парсинг зарплаты из текста с улучшенными регулярными выражениями"""
    patterns = [
        r'(\d{1,3}(?:\s*\d{3})*)\s*-\s*(\d{1,3}(?:\s*\d{3})*)',
        r'от\s*(\d{1,3}(?:\s*\d{3})*)\s*(?:до\s*(\d{1,3}(?:\s*\d{3})*))?',
        r'до\s*(\d{1,3}(?:\s*\d{3})*)',
        r'(\d{1,3}(?:\s*\d{3})*)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            min_salary = None
            max_salary = None

            if groups[0]:
                min_salary = int(groups[0].replace(' ', ''))
            if len(groups) > 1 and groups[1]:
                max_salary = int(groups[1].replace(' ', ''))
            elif len(groups) == 1:
                max_salary = min_salary

            if min_salary is not None:
                return Salary(
                    min_value=min_salary,
                    max_value=max_salary,
                    currency="RUR",
                )
    return None


def _parse_salary(vac: dict) -> Optional[Salary]:
    """Парсинг зарплаты из вакансии с правильной обработкой нулевых значений"""

    salary_min = vac.get("salary_min")
    salary_max = vac.get("salary_max")

    if salary_max == 0:
        salary_max = None

    if salary_min is not None or salary_max is not None:
        return Salary(
            min_value=int(salary_min) if salary_min is not None else None,
            max_value=int(salary_max) if salary_max is not None else None,
            currency="RUR",
        )

    salary_str = vac.get("salary")
    if salary_str:
        return _parse_salary_from_text(str(salary_str))

    requirements = vac.get("requirements", "")
    if requirements:
        return _parse_salary_from_text(requirements)

    return None


class TrudvsemParser(JobParserStrategy):
    """
    Стратегия для портала «Работа России» (Trudvsem.ru).
    Open Data API — бесплатный, открытый, без регистрации и ключей.

    Поддерживает два режима извлечения навыков:
    - USE_LLM=False: Словарный поиск (быстро, бесплатно)
    - USE_LLM=True: YandexGPT API (точно, требует регистрации в Yandex Cloud)
    """

    def __init__(self, use_llm: bool = False, debug: bool = False):
        self.url = "http://opendata.trudvsem.ru/api/v1/vacancies"
        self.headers = {"User-Agent": "DataEngineer-Homework/1.0"}
        self.use_llm = use_llm
        self.debug = debug
        self._llm_extractor = None

        if use_llm:
            try:
                from nlp.yandex_gpt import YandexGPTSkillExtractor
                self._llm_extractor = YandexGPTSkillExtractor()
                print("Trudvsem: YandexGPT инициализирован")
            except Exception as e:
                print(f"Trudvsem: YandexGPT недоступен ({e}). Переход на словарь.")
                self.use_llm = False

        self.common_tools = [
            "Python", "SQL", "Airflow", "Spark", "Kafka", "Hadoop", "dbt",
            "Docker", "Kubernetes", "PostgreSQL", "ClickHouse", "Greenplum",
            "Redis", "AWS", "GCP", "Azure", "Yandex Cloud", "Git", "Linux",
            "ETL", "ELT", "Databricks", "Snowflake", "Apache NiFi",
            "Prefect", "Dagster", "Great Expectations", "Terraform",
            "Bash", "Shell", "Pandas", "NumPy", "PySpark", "r"
        ]

    def _extract_skills(self, text: str) -> List[str]:
        """
        Извлекает навыки из текста.
        Если включен LLM — отправляет в YandexGPT.
        Иначе — ищет по словарю.
        """
        if self.use_llm and self._llm_extractor:
            return self._llm_extractor.extract_skills(text)

        text_lower = text.lower()
        return [t.lower() for t in self.common_tools if t.lower() in text_lower]

    def parse(self, query: str, max_pages: int = 2) -> List[Vacancy]:
        vacancies = []
        limit = 100

        for page in range(max_pages):
            offset = page * limit
            params = {"text": query, "offset": offset, "limit": limit}
            print(f"[Работа России] Запрос: offset={offset}...")

            try:
                response = requests.get(self.url, params=params, headers=self.headers, timeout=15)

                if response.status_code == 500:
                    print(
                        f"Trudvsem: API не поддерживает пагинацию глубже (вернул 500 на offset={offset}). Останавливаемся.")
                    break
                elif response.status_code != 200:
                    print(f"Trudvsem: HTTP {response.status_code} на offset={offset}")
                    break

                response.raise_for_status()
                data = response.json()

                if self.debug and page == 0 and data.get("results", {}).get("vacancies"):
                    print("\n DEBUG: Структура первой вакансии:")
                    first_vac = data["results"]["vacancies"][0]
                    import json
                    print(json.dumps(first_vac, indent=2, ensure_ascii=False))
                    print("\n DEBUG: Поля с зарплатой:")
                    vac_data = first_vac.get("vacancy", {})
                    for key in vac_data.keys():
                        if "salary" in key.lower() or "pay" in key.lower():
                            print(f"  {key}: {vac_data[key]}")
                    print()

                status = data.get("status")
                if status != "200":
                    error_msg = data.get("meta", {}).get("error", "Неизвестная ошибка")
                    print(f"Trudvsem: API вернул статус {status}: {error_msg}")
                    break

                items = data.get("results", {}).get("vacancies", [])
                if not items:
                    print("Trudvsem: Достигнут конец выборки (пустой ответ).")
                    break

                for item in items:
                    vac = item.get("vacancy", {})
                    title = vac.get("job-name", "")
                    requirements = vac.get("requirements", "")

                    desc_skills = self._extract_skills(requirements)

                    salary = _parse_salary(vac)

                    vacancies.append(Vacancy(
                        title=title,
                        key_skills=[],
                        description_skills=desc_skills,
                        description=requirements,
                        salary=salary,
                        url=vac.get("vac_url"),
                        external_id=vac.get("id"),
                    ))

                if len(items) < limit:
                    print(
                        f"Trudvsem: Найдено {len(items)} < {limit}. Это последняя страница, останавливаем пагинацию.")
                    break

            except requests.exceptions.Timeout:
                print(f"Trudvsem: Таймаут на offset={offset}")
                break
            except requests.exceptions.RequestException as e:
                print(f"Trudvsem: Ошибка сети на offset={offset}: {e}")
                break
            except Exception as e:
                print(f"Trudvsem: Непредвиденная ошибка: {e}")
                break

        return vacancies
