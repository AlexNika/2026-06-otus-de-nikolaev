# Аналитический отчет: Рынок вакансий Data Engineer

**Дата генерации:** {{ generated_at }}  
**Всего вакансий проанализировано:** {{ total_vacancies }}  
**Уникальных вакансий:** {{ unique_vacancies }}

---

## Источники данных

| Источник | Количество вакансий |
|----------|--------------------:|
{% for source, count in source_stats.items() %}
| {{ source }} | {{ count }} |
{% endfor %}

---

## ТОП-20 требуемых навыков и технологий

| № | Навык | Упоминаний | % вакансий |
|---|-------|------------|-----------:|
{% for skill, stats in top_skills %}
| {{ loop.index }} | **{{ skill }}** | {{ stats[0] }} | {{ "%.1f"|format(stats[1]) }}% |
{% endfor %}

---

## Зарплатная аналитика

{% if salary_stats.count > 0 %}
- **Вакансий с указанной зарплатой:** {{ salary_stats.count }}
- **Средняя зарплата:** {{ "%.0f"|format(salary_stats.avg) }} ₽
- **Минимальная:** {{ "%.0f"|format(salary_stats.min) }} ₽
- **Максимальная:** {{ "%.0f"|format(salary_stats.max) }} ₽
{% else %}
Данные о зарплатах отсутствуют в выборке.
{% endif %}

---

## Ключевые выводы

1. **Самый востребованный стек:** 
   {% if top_skills %}{{ top_skills[0][0] }}, {{ top_skills[1][0] }}, {{ top_skills[2][0] }}{% endif %}

2. **Наиболее активный источник:** 
   {% if source_stats %}{{ source_stats|dictsort(by='value')|last|first }}{% endif %}

---