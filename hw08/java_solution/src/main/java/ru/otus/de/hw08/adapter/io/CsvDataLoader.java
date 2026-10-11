package ru.otus.de.hw08.adapter.io;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.apache.spark.sql.SparkSession;
import ru.otus.de.hw08.port.DataLoader;

public final class CsvDataLoader implements DataLoader {

    private final SparkSession spark;

    public CsvDataLoader(SparkSession spark) {
        this.spark = spark;
    }

    @Override
    public Dataset<Row> load(String path) {
        return spark.read()
                .option("header", "true")
                .option("inferSchema", "true")
                .csv(path);
    }
}
