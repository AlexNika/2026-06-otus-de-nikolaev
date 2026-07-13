import json
import os
from typing import List, Any

import requests


def _parse_skills_from_response(response_text: str) -> List[str]:
    """Извлекает JSON-массив из ответа LLM"""
    try:
        start_idx = response_text.find("[")
        end_idx = response_text.rfind("]") + 1

        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            skills = json.loads(json_str)
            return [skill.strip() for skill in skills if isinstance(skill, str)]

        return []
    except json.JSONDecodeError:
        return []


class YandexGPTSkillExtractor:
    """
    Извлечение навыков из текста вакансии с помощью YandexGPT API.
    Документация: https://cloud.yandex.ru/docs/yandexgpt/
    """

    def __init__(self, api_key: str = Any, folder_id: str = Any):
        self.api_key = api_key or os.getenv("YANDEX_GPT_API_KEY")
        self.folder_id = folder_id or os.getenv("YANDEX_GPT_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

        if not self.api_key or not self.folder_id:
            raise ValueError("Требуется YANDEX_GPT_API_KEY и YANDEX_GPT_FOLDER_ID")

    def extract_skills(self, job_description: str) -> List[str]:
        """
        Отправляет описание вакансии в YandexGPT и получает список навыков.
        Использует Zero-shot промптинг.
        """
        prompt = f"""
        Ты — эксперт по анализу вакансий Data Engineer.
        Проанализируй следующее описание вакансии и извлеки ВСЕ упомянутые технологии, 
        инструменты, языки программирования, базы данных и концепции.

        Описание вакансии:
        "{job_description[:2000]}"  # Ограничиваем длину для API

        Верни ТОЛЬКО JSON-массив со списком навыков. Пример:
        ["Python", "Apache Airflow", "PostgreSQL", "Docker", "ETL"]

        Ответ:
        """

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.1,
                "maxTokens": 500
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            completion_text = result["result"]["alternatives"][0]["message"]["text"]

            skills = _parse_skills_from_response(completion_text)
            return skills

        except Exception as e:
            print(f"Ошибка YandexGPT API: {e}")
            return []

    def batch_extract(self, descriptions: List[str]) -> List[List[str]]:
        """Пакетная обработка нескольких описаний"""
        return [self.extract_skills(desc) for desc in descriptions]
