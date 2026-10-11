from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col

DEFAULT_JAVA_PATH = "/opt/spark/data/output/java"
DEFAULT_PYSPARK_PATH = "/opt/spark/data/output/pyspark"
DEFAULT_TOLERANCE = 1e-9

LONG_COLUMNS = ("crimes_total", "crimes_monthly")
DOUBLE_COLUMNS = ("lat", "lng")
STRING_COLUMNS = ("frequent_crime_types",)

logger = logging.getLogger("compare_marts")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Java and PySpark Boston crimes marts")
    parser.add_argument("--java_path", default=DEFAULT_JAVA_PATH)
    parser.add_argument("--pyspark_path", default=DEFAULT_PYSPARK_PATH)
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    return parser.parse_args(argv)


def schema_pairs(df: DataFrame) -> list[tuple[str, str]]:
    return [(field.name, field.dataType.simpleString()) for field in df.schema.fields]


def check_schemas(java_df: DataFrame, pyspark_df: DataFrame) -> bool:
    java_schema = schema_pairs(java_df)
    pyspark_schema = schema_pairs(pyspark_df)
    print("Java schema:")
    java_df.printSchema()
    print("PySpark schema:")
    pyspark_df.printSchema()
    if java_schema != pyspark_schema:
        print(f"SCHEMA MISMATCH: java={java_schema} pyspark={pyspark_schema}")
        return False
    print(f"Schema check OK: {java_schema}")
    return True


def compare_row(java_row: dict, pyspark_row: dict, tolerance: float) -> tuple[list[str], float, float]:
    diffs: list[str] = []
    for column in LONG_COLUMNS + STRING_COLUMNS:
        if java_row[column] != pyspark_row[column]:
            diffs.append(column)
    lat_diff = abs(java_row["lat"] - pyspark_row["lat"])
    lng_diff = abs(java_row["lng"] - pyspark_row["lng"])
    if lat_diff > tolerance:
        diffs.append("lat")
    if lng_diff > tolerance:
        diffs.append("lng")
    return diffs, lat_diff, lng_diff


def main(argv: Sequence[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    args = parse_args(argv)
    spark = SparkSession.builder.appName("BostonCrimesMartParityCheck").getOrCreate()
    try:
        java_df = spark.read.parquet(args.java_path)
        pyspark_df = spark.read.parquet(args.pyspark_path)

        if not check_schemas(java_df, pyspark_df):
            sys.exit(1)

        java_count = java_df.count()
        pyspark_count = pyspark_df.count()
        print(f"Row counts: java={java_count} pyspark={pyspark_count}")
        differences = 0
        if java_count != pyspark_count:
            print("ROW COUNT MISMATCH")
            differences += abs(java_count - pyspark_count)

        joined = java_df.alias("j").join(pyspark_df.alias("p"), "district", "full_outer")
        value_columns = LONG_COLUMNS + DOUBLE_COLUMNS + STRING_COLUMNS
        joined = joined.select(
            "district",
            *[col(f"j.{c}").alias(f"j_{c}") for c in value_columns],
            *[col(f"p.{c}").alias(f"p_{c}") for c in value_columns],
        )
        rows = {row["district"]: row.asDict() for row in joined.collect()}

        only_java = sorted(d for d, r in rows.items() if r["p_crimes_total"] is None)
        only_pyspark = sorted(d for d, r in rows.items() if r["j_crimes_total"] is None)
        common = sorted(d for d, r in rows.items() if d not in only_java and d not in only_pyspark)

        if only_java:
            print(f"Districts only in Java mart: {only_java}")
            differences += len(only_java)
        if only_pyspark:
            print(f"Districts only in PySpark mart: {only_pyspark}")
            differences += len(only_pyspark)

        print()
        header = (
            f"{'district':<10} | {'crimes_total j/p':<18} | {'crimes_monthly j/p':<20} | "
            f"{'frequent_crime_types j/p':<40} | {'lat diff':<10} | {'lng diff':<10} | MATCH"
        )
        print(header)
        print("-" * len(header))
        for district in common:
            row = rows[district]
            java_values = {c: row[f"j_{c}"] for c in LONG_COLUMNS + DOUBLE_COLUMNS + STRING_COLUMNS}
            pyspark_values = {c: row[f"p_{c}"] for c in LONG_COLUMNS + DOUBLE_COLUMNS + STRING_COLUMNS}
            diffs, lat_diff, lng_diff = compare_row(java_values, pyspark_values, args.tolerance)
            if diffs:
                differences += len(diffs)
            match = "OK" if not diffs else f"DIFF({', '.join(diffs)})"
            print(
                f"{district:<10} | "
                f"{str(java_values['crimes_total']) + '/' + str(pyspark_values['crimes_total']):<18} | "
                f"{str(java_values['crimes_monthly']) + '/' + str(pyspark_values['crimes_monthly']):<20} | "
                f"{str(java_values['frequent_crime_types']) + '/' + str(pyspark_values['frequent_crime_types']):<40} | "
                f"{lat_diff:<10.2e} | {lng_diff:<10.2e} | {match}"
            )
        print()

        total_districts = len(rows)
        if differences == 0:
            print(f"PARITY OK: {total_districts} districts, 0 differences")
        else:
            print(f"PARITY FAILED: {total_districts} districts, {differences} differences")
            sys.exit(1)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
