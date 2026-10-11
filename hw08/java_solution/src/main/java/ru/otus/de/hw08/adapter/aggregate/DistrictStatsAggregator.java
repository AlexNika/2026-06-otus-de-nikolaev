package ru.otus.de.hw08.adapter.aggregate;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.checkerframework.checker.nullness.qual.NonNull;
import ru.otus.de.hw08.config.CrimeColumns;
import ru.otus.de.hw08.port.Aggregator;

import static org.apache.spark.sql.functions.avg;
import static org.apache.spark.sql.functions.count;

/** crimes_total + средние координаты (lat, lng). */
public final class DistrictStatsAggregator implements Aggregator {

    @Override
    public Dataset<Row> aggregate(@NonNull Dataset<Row> enriched) {
        return enriched.groupBy(CrimeColumns.DISTRICT)
                .agg(
                        count("*").as("crimes_total"),
                        avg(CrimeColumns.LAT).as("lat"),
                        avg(CrimeColumns.LNG).as("lng")
                );
    }
}
