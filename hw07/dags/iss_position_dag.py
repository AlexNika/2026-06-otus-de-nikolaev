"""
DAG для получения положения МКС из API Open Notify.

Получает координаты ISS в реальном времени, парсит ответ,
проверяет idempotency и сохраняет данные в БД analytics.
"""

from airflow.sdk import dag, task, Variable, chain
from airflow.providers.postgres.hooks.postgres import PostgresHook
import requests
from datetime import datetime, timedelta
from pydantic import BaseModel, ValidationError
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


class ISSPosition(BaseModel):
    """Координаты МКС из ответа API."""
    latitude: str
    longitude: str


class ISSPositionResponse(BaseModel):
    """Валидация ответа API Open Notify."""
    timestamp: int
    message: str
    iss_position: ISSPosition


def _create_session() -> requests.Session:
    """HTTP-сессия с автоматическим retry и backoff для запросов к внешним API."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


@task
def fetch_iss_position() -> dict:
    """Запрос к API для получения текущего положения МКС."""
    api_url = Variable.get(
        "iss_api_url",
        default="http://api.open-notify.org/iss-now.json",
    )
    session = _create_session()
    response = session.get(api_url, timeout=(10, 30))
    response.raise_for_status()
    try:
        return response.json()
    except requests.JSONDecodeError as e:
        raise ValueError(f"Expected JSON response, got: {response.text}") from e



@task
def parse_response(data: dict) -> dict:
    """Парсинг и валидация JSON ответа из API."""
    try:
        validated = ISSPositionResponse(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid API response: {e}. Raw response: {data}") from e

    return {
        "timestamp": validated.timestamp,
        "latitude": float(validated.iss_position.latitude),
        "longitude": float(validated.iss_position.longitude),
    }


@task
def save_to_db(parsed_data: dict, **context) -> str:
    """Проверка idempotency и вставка данных в БД."""
    hook = PostgresHook(postgres_conn_id="postgres_analytics")
    data_interval_start = context["data_interval_start"]

    on_conflict_action = Variable.get(
        "iss_on_conflict",
        default="DO NOTHING",
    )

    sql = f"""
        INSERT INTO iss_position (data_interval_start, timestamp, latitude, longitude)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (data_interval_start) {on_conflict_action}
    """

    hook.run(
        sql,
        autocommit=True,
        parameters=(
            data_interval_start,
            parsed_data["timestamp"],
            parsed_data["latitude"],
            parsed_data["longitude"],
        ),
    )

    return f"Inserted record for interval {data_interval_start}"


@dag(
    dag_id="iss_position_dag",
    description="Fetch ISS position from Open Notify API and store in analytics DB",
    schedule="*/30 * * * *",
    start_date=datetime(2026, 9, 27),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "airflow",
        "retries": 3,
        "retry_delay": timedelta(minutes=1),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(minutes=10),
    },
    tags=["iss", "api"],
)
def iss_position_dag():
    data = fetch_iss_position()
    parsed = parse_response(data)
    result = save_to_db(parsed)

    chain(data, parsed, result)  # type: ignore[arg-type]


iss_position_dag_instance = iss_position_dag()