package ru.otus.de.hw08.adapter.enrich;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.checkerframework.checker.nullness.qual.NonNull;
import ru.otus.de.hw08.config.CrimeColumns;
import ru.otus.de.hw08.config.OffenseCodeColumns;
import ru.otus.de.hw08.port.DataEnricher;

import static org.apache.spark.sql.functions.broadcast;

public final class CrimeDataEnricher implements DataEnricher {

    @Override
    public Dataset<Row> enrich(@NonNull Dataset<Row> crimes, Dataset<Row> codes) {
        return crimes.join(
                broadcast(codes),
                crimes.col(CrimeColumns.OFFENSE_CODE).equalTo(codes.col(OffenseCodeColumns.CODE)),
                "left"
        );
    }
}
