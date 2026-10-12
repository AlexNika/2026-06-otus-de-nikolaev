package ru.otus.de.hw08.adapter.aggregate;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import ru.otus.de.hw08.config.CrimeColumns;
import ru.otus.de.hw08.port.Aggregator;

import java.util.Iterator;
import java.util.List;

/**
 * Фасад: собирает произвольный набор агрегаторов в одну витрину.
 * Open/Closed: чтобы добавить метрику - регистрируем новый Aggregator
 * в AppContext. Сам класс не меняется.
 *
 * <p>Первый агрегатор в списке даёт базовый набор строк (по district);
 * остальные джойнятся к нему по district. Порядок значим.
 */
public final class DistrictMartAggregator implements Aggregator {

    private final List<Aggregator> aggregators;

    public DistrictMartAggregator(List<Aggregator> aggregators) {
        if (aggregators == null || aggregators.isEmpty()) {
            throw new IllegalArgumentException("At least one aggregator required");
        }
        this.aggregators = List.copyOf(aggregators);
    }

    @Override
    public Dataset<Row> aggregate(Dataset<Row> enriched) {
        Iterator<Aggregator> it = aggregators.iterator();
        Dataset<Row> result = it.next().aggregate(enriched);
        while (it.hasNext()) {
            result = result.join(it.next().aggregate(enriched), CrimeColumns.DISTRICT);
        }
        return result.withColumnRenamed(CrimeColumns.DISTRICT, "district");
    }
}
