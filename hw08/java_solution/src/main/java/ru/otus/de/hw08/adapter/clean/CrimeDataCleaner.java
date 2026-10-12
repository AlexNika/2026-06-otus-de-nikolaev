package ru.otus.de.hw08.adapter.clean;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.checkerframework.checker.nullness.qual.NonNull;
import ru.otus.de.hw08.config.CrimeColumns;
import ru.otus.de.hw08.port.DataCleaner;

import static org.apache.spark.sql.functions.col;

public final class CrimeDataCleaner implements DataCleaner {

    @Override
    public Dataset<Row> clean(@NonNull Dataset<Row> raw) {
        return raw.dropDuplicates()
                .filter(col(CrimeColumns.DISTRICT).isNotNull()
                        .and(col(CrimeColumns.LAT).isNotNull())
                        .and(col(CrimeColumns.LNG).isNotNull()));
    }
}
