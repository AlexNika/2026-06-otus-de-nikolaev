package ru.otus.de.hw08.adapter.aggregate;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.apache.spark.sql.expressions.Window;
import org.apache.spark.sql.expressions.WindowSpec;
import org.checkerframework.checker.nullness.qual.NonNull;
import ru.otus.de.hw08.config.CrimeColumns;
import ru.otus.de.hw08.config.OffenseCodeColumns;
import ru.otus.de.hw08.port.Aggregator;

import static org.apache.spark.sql.functions.col;
import static org.apache.spark.sql.functions.collect_list;
import static org.apache.spark.sql.functions.concat_ws;
import static org.apache.spark.sql.functions.count;
import static org.apache.spark.sql.functions.expr;
import static org.apache.spark.sql.functions.row_number;
import static org.apache.spark.sql.functions.sort_array;
import static org.apache.spark.sql.functions.struct;

/** Топ-3 crime_type в каждом районе, объединённые через ", " по убыванию частоты. */
public final class FrequentCrimeTypesAggregator implements Aggregator {

    private static final int TOP_N = 3;

    @Override
    public Dataset<Row> aggregate(@NonNull Dataset<Row> enriched) {
        Dataset<Row> counts = enriched
                .filter(col(OffenseCodeColumns.CRIME_TYPE).isNotNull())
                .groupBy(CrimeColumns.DISTRICT, OffenseCodeColumns.CRIME_TYPE)
                .agg(count("*").as("cnt"));

        WindowSpec window = Window.partitionBy(CrimeColumns.DISTRICT)
                .orderBy(col("cnt").desc(), col(OffenseCodeColumns.CRIME_TYPE).asc());

        return counts
                .withColumn("rank", row_number().over(window))
                .filter(col("rank").leq(TOP_N))
                .groupBy(CrimeColumns.DISTRICT)
                .agg(sort_array(collect_list(
                        struct(col("rank"), col(OffenseCodeColumns.CRIME_TYPE)))).as("ranked"))
                .select(
                        col(CrimeColumns.DISTRICT),
                        concat_ws(", ", expr("transform(ranked, x -> x." + OffenseCodeColumns.CRIME_TYPE + ")"))
                                .as("frequent_crime_types"));
    }
}