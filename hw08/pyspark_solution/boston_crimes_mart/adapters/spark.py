from __future__ import annotations

from pyspark.sql import SparkSession

from ..config import AppConfig
from ..ports import SparkSessionProvider

APP_NAME = "BostonCrimesMart"


class DefaultSparkSessionProvider(SparkSessionProvider):
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def get(self) -> SparkSession:
        builder = SparkSession.builder.appName(APP_NAME)
        if self._config.master:
            builder = builder.master(self._config.master)
        return builder.getOrCreate()
