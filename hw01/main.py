import time

from database.connector import DatabaseManager
from report.generator import ReportGenerator
from strategies.trudvsem_strategy import TrudvsemParser
from transform.analyzer import DataAnalyzer


def run_etl_pipeline():
    """Основной ETL-пайплайн: Extract -> Load -> Transform -> Report"""

    search_queries = [
        '"Data Engineer"',
        '"Инженер данных"',
        '"ETL Developer"',
        '"BI Engineer"'
    ]
    timeout_between_queries = 5

    print("=" * 70)
    print("ЗАПУСК ETL-ПАЙПЛАЙНА: Анализ рынка Data Engineer")
    print("=" * 70)

    db = DatabaseManager("vacancies.db")
    analyzer = DataAnalyzer()
    reporter = ReportGenerator("templates")

    print("\n ЭТАП 1: Извлечение данных из различных источников")
    print("-" * 70)

    strategies = [
        (TrudvsemParser(use_llm=False, debug=False), "trudvsem"),
    ]

    total_saved = 0
    total_skipped = 0

    for strategy, source_name in strategies:
        print(f"\nПарсинг источника: {source_name}")

        for i, query in enumerate(search_queries):
            print(f"\n [{i + 1}/{len(search_queries)}] Запрос: {query}")
            try:
                vacancies = strategy.parse(query, max_pages=3)

                saved, skipped = db.save_vacancies(vacancies, source_name)

                total_saved += saved
                total_skipped += skipped

                print(f"   Найдено: {len(vacancies)} | Новых: {saved} | Уже в БД: {skipped}")
            except Exception as e:
                print(f"   Ошибка при парсинге {source_name}: {e}")

            if i < len(search_queries) - 1:
                print(f"   Таймаут {timeout_between_queries} сек...")
                time.sleep(timeout_between_queries)

    print(f"\n ИТОГО: Новых записей: {total_saved} | Пропущено дубликатов: {total_skipped}")

    print("\n ЭТАП 3: Трансформация и анализ данных из БД")
    print("-" * 70)

    all_vacancies = db.get_all_vacancies()
    print(f" Загружено из БД: {len(all_vacancies)} вакансий")

    unique_vacancies = analyzer.deduplicate_by_title(all_vacancies)
    print(f" После дедупликации: {len(unique_vacancies)} уникальных")

    skills_stats = analyzer.analyze_skills(unique_vacancies)
    print(f" Уникальных навыков выявлено: {len(skills_stats)}")

    source_stats = db.get_vacancies_by_source()

    salary_stats = analyzer.get_salary_statistics(unique_vacancies)

    print("\n ЭТАП 4: Генерация итогового отчета")
    print("-" * 70)

    reporter.generate_markdown(
        output_path="data_engineer_market_report.md",
        vacancies=unique_vacancies,
        skills_stats=skills_stats,
        source_stats=source_stats,
        salary_stats=salary_stats
    )

    print("\n" + "=" * 70)
    print("ETL-ПАЙПЛАЙН УСПЕШНО ЗАВЕРШЕН!")
    print("=" * 70)


if __name__ == "__main__":
    run_etl_pipeline()
