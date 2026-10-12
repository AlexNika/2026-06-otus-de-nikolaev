from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DATA = _PROJECT_ROOT / "data"


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Immutable application configuration resolved from CLI arguments."""

    crimes_path: str
    offense_codes_path: str
    output_path: str
    master: str | None = None

    @classmethod
    def from_args(cls, argv: Sequence[str] | None = None) -> AppConfig:
        parser = argparse.ArgumentParser(description="Boston crimes mart PySpark application")
        parser.add_argument("--crimes_path", help="Crimes CSV file path", default=str(_DATA / "crime.csv"))
        parser.add_argument(
            "--codes_path", help="Offense codes CSV file path", default=str(_DATA / "offense_codes.csv")
        )
        parser.add_argument("--output_path", help="Output parquet directory", default=str(_DATA / "output" / "pyspark"))
        parser.add_argument("--master", help="Spark master URL (default: from spark-defaults.conf)", default=None)
        args = parser.parse_args(list(argv) if argv is not None else None)
        return cls(
            crimes_path=args.crimes_path,
            offense_codes_path=args.codes_path,
            output_path=args.output_path,
            master=args.master,
        )


class CrimeColumns:
    DISTRICT = "DISTRICT"
    OFFENSE_CODE = "OFFENSE_CODE"
    LAT = "Lat"
    LNG = "Long"
    OCCURRED_ON_DATE = "OCCURRED_ON_DATE"

    def __init__(self) -> None:
        raise TypeError("CrimeColumns is a static namespace")


class OffenseCodeColumns:
    CODE = "CODE"
    NAME = "NAME"
    CRIME_TYPE = "crime_type"

    def __init__(self) -> None:
        raise TypeError("OffenseCodeColumns is a static namespace")


class MartColumns:
    DISTRICT = "district"
    CRIMES_TOTAL = "crimes_total"
    LAT = "lat"
    LNG = "lng"
    CRIMES_MONTHLY = "crimes_monthly"
    FREQUENT_CRIME_TYPES = "frequent_crime_types"

    def __init__(self) -> None:
        raise TypeError("MartColumns is a static namespace")
