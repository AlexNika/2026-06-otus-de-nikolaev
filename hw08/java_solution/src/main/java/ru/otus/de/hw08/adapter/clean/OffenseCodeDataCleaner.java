package ru.otus.de.hw08.adapter.clean;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import ru.otus.de.hw08.config.OffenseCodeColumns;
import ru.otus.de.hw08.port.DataCleaner;

import static org.apache.spark.sql.functions.col;
import static org.apache.spark.sql.functions.split;
import static org.apache.spark.sql.functions.trim;

/**
 * Оставляет уникальные коды и сразу извлекает crime_type
 * (первая часть NAME по разделителю "-").
 */
public final class OffenseCodeDataCleaner implements DataCleaner {

    @Override
    public Dataset<Row> clean(Dataset<Row> raw) {
        return raw.dropDuplicates(OffenseCodeColumns.CODE)
                .select(
                        col(OffenseCodeColumns.CODE),
                        trim(split(col(OffenseCodeColumns.NAME), "-")
                                .getItem(0)).as(OffenseCodeColumns.CRIME_TYPE)
                );
    }
}
