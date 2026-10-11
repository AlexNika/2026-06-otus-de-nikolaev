package ru.otus.de.hw08.port;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;

@FunctionalInterface
public interface DataEnricher {
    Dataset<Row> enrich(Dataset<Row> left, Dataset<Row> right);
}
