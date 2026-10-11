from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession

from ..ports import DataLoader, MartWriter


class CsvDataLoader(DataLoader):
    def __init__(self, spark: SparkSession) -> None:
        self._spark = spark

    def load(self, path: str) -> DataFrame:
        return self._spark.read.option("header", "true").option("inferSchema", "true").csv(path)


class ParquetMartWriter(MartWriter):
    def write(self, mart: DataFrame, output_path: str) -> None:
        mart.coalesce(1).write.mode("overwrite").parquet(output_path)
