package ru.otus.de.hw08.port;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;

@FunctionalInterface
public interface DataCleaner {
    Dataset<Row> clean(Dataset<Row> raw);
}
