from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import broadcast

from ..config import CrimeColumns, OffenseCodeColumns
from ..ports import DataEnricher


class CrimeDataEnricher(DataEnricher):
    def enrich(self, left: DataFrame, right: DataFrame) -> DataFrame:
        return left.join(
            broadcast(right),
            left[CrimeColumns.OFFENSE_CODE] == right[OffenseCodeColumns.CODE],
            "left",
        )
