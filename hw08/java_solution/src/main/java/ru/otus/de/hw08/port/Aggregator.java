package ru.otus.de.hw08.port;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;

/**
 * Общий контракт всех агрегаторов.
 * Одинаковая сигнатура позволяет свободно комбинировать их в пайплайне
 * (см. DistrictMartAggregator) и мокать в тестах.
 */
@FunctionalInterface
public interface Aggregator {
    Dataset<Row> aggregate(Dataset<Row> input);
}
