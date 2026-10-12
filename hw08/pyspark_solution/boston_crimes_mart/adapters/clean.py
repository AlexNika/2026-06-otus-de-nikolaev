from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, split, trim

from ..config import CrimeColumns, OffenseCodeColumns
from ..ports import DataCleaner


class CrimeDataCleaner(DataCleaner):
    def clean(self, raw: DataFrame) -> DataFrame:
        return raw.dropDuplicates().filter(
            col(CrimeColumns.DISTRICT).isNotNull()
            & col(CrimeColumns.LAT).isNotNull()
            & col(CrimeColumns.LNG).isNotNull()
        )


class OffenseCodeDataCleaner(DataCleaner):
    def clean(self, raw: DataFrame) -> DataFrame:
        return raw.dropDuplicates([OffenseCodeColumns.CODE]).select(
            col(OffenseCodeColumns.CODE),
            trim(split(col(OffenseCodeColumns.NAME), "-").getItem(0)).alias(OffenseCodeColumns.CRIME_TYPE),
        )
