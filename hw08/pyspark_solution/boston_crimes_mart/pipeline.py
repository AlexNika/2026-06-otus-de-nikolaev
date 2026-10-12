from __future__ import annotations

import logging

from .ports import Aggregator, DataCleaner, DataLoader, DataEnricher, MartWriter

logger = logging.getLogger(__name__)


class CrimesMartPipeline:
    """Pure orchestration: load -> clean -> enrich -> aggregate -> write."""

    def __init__(
            self,
            loader: DataLoader,
            crime_cleaner: DataCleaner,
            codes_cleaner: DataCleaner,
            enricher: DataEnricher,
            aggregator: Aggregator,
            writer: MartWriter,
    ) -> None:
        self._loader = loader
        self._crime_cleaner = crime_cleaner
        self._codes_cleaner = codes_cleaner
        self._enricher = enricher
        self._aggregator = aggregator
        self._writer = writer

    def execute(self, crimes_path: str, offense_codes_path: str, output_path: str) -> None:
        logger.info("Loading raw data...")
        raw_crimes = self._loader.load(crimes_path)
        raw_codes = self._loader.load(offense_codes_path)

        logger.info("Cleaning...")
        crimes = self._crime_cleaner.clean(raw_crimes)
        codes = self._codes_cleaner.clean(raw_codes)

        logger.info("Enriching...")
        enriched = self._enricher.enrich(crimes, codes)

        logger.info("Aggregating...")
        mart = self._aggregator.aggregate(enriched)

        logger.info("Writing mart to %s...", output_path)
        self._writer.write(mart, output_path)

        logger.info("Done.")
