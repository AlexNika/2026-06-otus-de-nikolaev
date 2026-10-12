package ru.otus.de.hw08.adapter.io;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.apache.spark.sql.SaveMode;
import org.checkerframework.checker.nullness.qual.NonNull;
import ru.otus.de.hw08.port.MartWriter;

public final class ParquetMartWriter implements MartWriter {

    @Override
    public void write(@NonNull Dataset<Row> mart, String outputPath) {
        mart.coalesce(1)
                .write()
                .mode(SaveMode.Overwrite)
                .parquet(outputPath);
    }
}