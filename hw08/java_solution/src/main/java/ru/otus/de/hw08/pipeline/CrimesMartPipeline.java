package ru.otus.de.hw08.pipeline;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import ru.otus.de.hw08.port.Aggregator;
import ru.otus.de.hw08.port.DataCleaner;
import ru.otus.de.hw08.port.DataEnricher;
import ru.otus.de.hw08.port.DataLoader;
import ru.otus.de.hw08.port.MartWriter;

/**
 * Чистая оркестрация пайплайна:
 * load → clean → enrich → aggregate → write.
 * Зависит только от портов. Никакого знания о Spark-сессии, config, файлах.
 */
@Slf4j
@RequiredArgsConstructor
public final class CrimesMartPipeline {

    private final DataLoader loader;
    private final DataCleaner crimeCleaner;
    private final DataCleaner codesCleaner;
    private final DataEnricher enricher;
    private final Aggregator aggregator;
    private final MartWriter writer;

    public void execute(String crimesPath, String codesPath, String outputPath) {
        log.info("Loading raw data...");
        Dataset<Row> rawCrimes = loader.load(crimesPath);
        Dataset<Row> rawCodes  = loader.load(codesPath);

        log.info("Cleaning...");
        Dataset<Row> crimes = crimeCleaner.clean(rawCrimes);
        Dataset<Row> codes  = codesCleaner.clean(rawCodes);

        log.info("Enriching...");
        Dataset<Row> enriched = enricher.enrich(crimes, codes);

        log.info("Aggregating...");
        Dataset<Row> mart = aggregator.aggregate(enriched);

        log.info("Writing mart to {}...", outputPath);
        writer.write(mart, outputPath);

        log.info("Done.");
    }
}
