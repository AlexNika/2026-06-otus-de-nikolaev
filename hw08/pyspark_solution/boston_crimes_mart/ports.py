from __future__ import annotations

from abc import ABC, abstractmethod

from pyspark.sql import DataFrame, SparkSession


class SparkSessionProvider(ABC):
    @abstractmethod
    def get(self) -> SparkSession:
        """Return a configured SparkSession."""


class DataLoader(ABC):
    @abstractmethod
    def load(self, path: str) -> DataFrame:
        """Load a raw dataset from the given path."""


class DataCleaner(ABC):
    @abstractmethod
    def clean(self, raw: DataFrame) -> DataFrame:
        """Return a deduplicated and filtered dataset."""


class DataEnricher(ABC):
    @abstractmethod
    def enrich(self, left: DataFrame, right: DataFrame) -> DataFrame:
        """Join the left dataset with the right reference dataset."""


class Aggregator(ABC):
    @abstractmethod
    def aggregate(self, df: DataFrame) -> DataFrame:
        """Return a per-district aggregation of the enriched dataset."""


class MartWriter(ABC):
    @abstractmethod
    def write(self, mart: DataFrame, output_path: str) -> None:
        """Persist the mart to the given path."""
