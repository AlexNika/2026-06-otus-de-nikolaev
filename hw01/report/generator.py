from datetime import datetime
from typing import Dict, List

import markdown
from jinja2 import Environment, FileSystemLoader

from database.models import VacancyDB


def generate_pdf(markdown_path: str, pdf_path: str):
    """Конвертирует Markdown в PDF (требует установки markdown-pdf)"""
    try:
        with open(markdown_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        html_content = markdown.markdown(md_content)

        # Для PDF нужен pdfkit или weasyprint
        # Здесь упрощенная версия - просто сохраняем HTML
        html_path = pdf_path.replace(".pdf", ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"HTML отчет сохранен: {html_path}")
        print(f"Для конвертации в PDF установи: pip install weasyprint")

    except Exception as e:
        print(f"Ошибка генерации PDF: {e}")


class ReportGenerator:
    """Генератор отчетов в форматах Markdown и PDF"""

    def __init__(self, templates_dir: str = "templates"):
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def generate_markdown(
            self,
            output_path: str,
            vacancies: List[VacancyDB],
            skills_stats: Dict,
            source_stats: dict,
            salary_stats: dict
    ):
        """Генерирует отчет в формате Markdown из шаблона Jinja2"""
        template = self.env.get_template("report_template.md")

        top_skills = list(skills_stats.items())[:20]

        context = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_vacancies": len(vacancies),
            "unique_vacancies": len(set(v.external_id for v in vacancies)),
            "source_stats": source_stats,
            "top_skills": top_skills,
            "salary_stats": salary_stats
        }

        report_content = template.render(**context)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"Markdown отчет сохранен: {output_path}")
