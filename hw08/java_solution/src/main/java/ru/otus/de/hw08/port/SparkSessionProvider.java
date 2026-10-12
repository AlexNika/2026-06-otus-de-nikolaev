package ru.otus.de.hw08.port;

import org.apache.spark.sql.SparkSession;

@FunctionalInterface
public interface SparkSessionProvider {
    SparkSession get();
}
