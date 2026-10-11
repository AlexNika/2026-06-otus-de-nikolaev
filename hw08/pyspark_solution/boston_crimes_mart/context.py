from __future__ import annotations

from types import TracebackType

from pyspark.sql import SparkSession

from .adapters.aggregate import (
    DistrictMartAggregator,
    DistrictStatsAggregator,
    FrequentCrimeTypesAggregator,
    MonthlyMedianAggregator,
)
from .adapters.clean import CrimeDataCleaner, OffenseCodeDataCleaner
from .adapters.enrich import CrimeDataEnricher
from .adapters.io import CsvDataLoader, ParquetMartWriter
from .adapters.spark import DefaultSparkSessionProvider
from .config import AppConfig
from .pipeline import CrimesMartPipeline
from .ports import SparkSessionProvider


class AppContext:
    """Composition root: wires concrete adapters into ports and owns the SparkSession lifecycle."""

    def __init__(
            self,
            config: AppConfig,
            spark: SparkSession | None = None,
            spark_provider: SparkSessionProvider | None = None,
    ) -> None:
        self.config = config
        self.spark = spark
        self._spark_provider = spark_provider or DefaultSparkSessionProvider(config)
        self.pipeline: CrimesMartPipeline | None = None

    def __enter__(self) -> AppContext:
        if self.spark is None:
            self.spark = self._spark_provider.get()
        self.pipeline = CrimesMartPipeline(
            loader=CsvDataLoader(self.spark),
            crime_cleaner=CrimeDataCleaner(),
            codes_cleaner=OffenseCodeDataCleaner(),
            enricher=CrimeDataEnricher(),
            aggregator=DistrictMartAggregator(
                [
                    DistrictStatsAggregator(),
                    MonthlyMedianAggregator(),
                    FrequentCrimeTypesAggregator(),
                ]
            ),
            writer=ParquetMartWriter(),
        )
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
    ) -> bool:
        if self.spark is not None:
            self.spark.stop()
        return False
