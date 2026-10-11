package ru.otus.de.hw08;

import org.apache.spark.sql.SparkSession;
import org.checkerframework.checker.nullness.qual.NonNull;
import ru.otus.de.hw08.adapter.aggregate.DistrictMartAggregator;
import ru.otus.de.hw08.adapter.aggregate.DistrictStatsAggregator;
import ru.otus.de.hw08.adapter.aggregate.FrequentCrimeTypesAggregator;
import ru.otus.de.hw08.adapter.aggregate.MonthlyMedianAggregator;
import ru.otus.de.hw08.adapter.clean.CrimeDataCleaner;
import ru.otus.de.hw08.adapter.clean.OffenseCodeDataCleaner;
import ru.otus.de.hw08.adapter.enrich.CrimeDataEnricher;
import ru.otus.de.hw08.adapter.io.CsvDataLoader;
import ru.otus.de.hw08.adapter.io.ParquetMartWriter;
import ru.otus.de.hw08.adapter.spark.DefaultSparkSessionProvider;
import ru.otus.de.hw08.config.AppConfig;
import ru.otus.de.hw08.pipeline.CrimesMartPipeline;
import ru.otus.de.hw08.port.Aggregator;
import ru.otus.de.hw08.port.DataLoader;

import java.util.List;

/**
 * Ручной DI-контейнер. Единственное место в приложении,
 * которое знает конкретные реализации портов.
 */
@SuppressWarnings("ClassCanBeRecord")
public final class AppContext {

    public final SparkSession spark;
    public final CrimesMartPipeline pipeline;

    public AppContext(AppConfig config) {
        this(new DefaultSparkSessionProvider(config).get(), config);
    }

    /**
     * Конструктор для тестов: подсовываем готовую SparkSession.
     */
    public AppContext(SparkSession spark, AppConfig config) {
        this(spark, defaultPipeline(spark));
    }

    /**
     * Конструктор для тестов: подсовываем готовый pipeline.
     */
    public AppContext(SparkSession spark, CrimesMartPipeline pipeline) {
        this.spark = spark;
        this.pipeline = pipeline;
    }

    private static @NonNull CrimesMartPipeline defaultPipeline(SparkSession spark) {
        DataLoader loader = new CsvDataLoader(spark);

        Aggregator martAggregator = new DistrictMartAggregator(List.of(
                new DistrictStatsAggregator(),
                new MonthlyMedianAggregator(),
                new FrequentCrimeTypesAggregator()
        ));

        return new CrimesMartPipeline(
                loader,
                new CrimeDataCleaner(),
                new OffenseCodeDataCleaner(),
                new CrimeDataEnricher(),
                martAggregator,
                new ParquetMartWriter()
        );
    }
}