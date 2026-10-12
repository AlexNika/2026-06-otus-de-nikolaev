package ru.otus.de.hw08.adapter.spark;

import lombok.RequiredArgsConstructor;
import org.apache.spark.sql.SparkSession;
import ru.otus.de.hw08.config.AppConfig;
import ru.otus.de.hw08.port.SparkSessionProvider;

@RequiredArgsConstructor
public final class DefaultSparkSessionProvider implements SparkSessionProvider {

    private final AppConfig config;

    @Override
    public SparkSession get() {
        SparkSession.Builder builder = SparkSession.builder()
                .appName("BostonCrimesMart");
        if (config.master() != null) {
            builder.master(config.master());
        }
        return builder.getOrCreate();
    }
}
