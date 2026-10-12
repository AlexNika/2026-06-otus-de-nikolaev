from __future__ import annotations

from collections.abc import Sequence

from pyspark.sql import DataFrame, Window
from pyspark.sql.functions import (
    avg,
    collect_list,
    col,
    concat_ws,
    count,
    expr,
    month,
    percentile_approx,
    row_number,
    sort_array,
    struct,
    year,
)

from ..config import CrimeColumns, MartColumns, OffenseCodeColumns
from ..ports import Aggregator

_YEAR = "year"
_MONTH = "month"
_MONTHLY_COUNT = "monthly_count"
_CRIME_COUNT = "cnt"
_RANK = "rank"
_RANKED = "ranked"


class DistrictStatsAggregator(Aggregator):
    def aggregate(self, df: DataFrame) -> DataFrame:
        return df.groupBy(CrimeColumns.DISTRICT).agg(
            count("*").alias(MartColumns.CRIMES_TOTAL),
            avg(col(CrimeColumns.LAT)).alias(MartColumns.LAT),
            avg(col(CrimeColumns.LNG)).alias(MartColumns.LNG),
        )


class MonthlyMedianAggregator(Aggregator):
    def aggregate(self, df: DataFrame) -> DataFrame:
        monthly = (
            df.withColumn(_YEAR, year(col(CrimeColumns.OCCURRED_ON_DATE)))
            .withColumn(_MONTH, month(col(CrimeColumns.OCCURRED_ON_DATE)))
            .groupBy(CrimeColumns.DISTRICT, _YEAR, _MONTH)
            .agg(count("*").alias(_MONTHLY_COUNT))
        )
        return monthly.groupBy(CrimeColumns.DISTRICT).agg(
            percentile_approx(col(_MONTHLY_COUNT), 0.5).alias(MartColumns.CRIMES_MONTHLY)
        )


class FrequentCrimeTypesAggregator(Aggregator):
    TOP_N = 3

    def aggregate(self, df: DataFrame) -> DataFrame:
        counts = (
            df.filter(col(OffenseCodeColumns.CRIME_TYPE).isNotNull())
            .groupBy(CrimeColumns.DISTRICT, OffenseCodeColumns.CRIME_TYPE)
            .agg(count("*").alias(_CRIME_COUNT))
        )
        by_frequency = Window.partitionBy(CrimeColumns.DISTRICT).orderBy(
            col(_CRIME_COUNT).desc(), col(OffenseCodeColumns.CRIME_TYPE).asc()
        )
        ranked = counts.withColumn(_RANK, row_number().over(by_frequency)).filter(col(_RANK) <= self.TOP_N)
        grouped = ranked.groupBy(CrimeColumns.DISTRICT).agg(
            sort_array(collect_list(struct(col(_RANK), col(OffenseCodeColumns.CRIME_TYPE)))).alias(_RANKED)
        )
        return grouped.select(
            col(CrimeColumns.DISTRICT),
            concat_ws(
                ", ", expr(f"transform({_RANKED}, x -> x.{OffenseCodeColumns.CRIME_TYPE})")
            ).alias(MartColumns.FREQUENT_CRIME_TYPES),
        )


class DistrictMartAggregator(Aggregator):
    """Composite aggregator: folds per-metric aggregations into a single mart by district."""

    def __init__(self, aggregators: Sequence[Aggregator]) -> None:
        if not aggregators:
            raise ValueError("At least one aggregator is required")
        self._aggregators = tuple(aggregators)

    def aggregate(self, df: DataFrame) -> DataFrame:
        mart = self._aggregators[0].aggregate(df)
        for aggregator in self._aggregators[1:]:
            mart = mart.join(aggregator.aggregate(df), CrimeColumns.DISTRICT)
        return mart.withColumnRenamed(CrimeColumns.DISTRICT, MartColumns.DISTRICT)
