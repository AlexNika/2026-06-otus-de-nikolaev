package ru.otus.de.hw08.adapter.aggregate;

import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import ru.otus.de.hw08.config.CrimeColumns;
import ru.otus.de.hw08.port.Aggregator;

import static org.apache.spark.sql.functions.col;
import static org.apache.spark.sql.functions.count;
import static org.apache.spark.sql.functions.expr;
import static org.apache.spark.sql.functions.month;
import static org.apache.spark.sql.functions.year;

/** crimes_monthly - медиана числа преступлений в месяц (год + месяц). */
public final class MonthlyMedianAggregator implements Aggregator {

    @Override
    public Dataset<Row> aggregate(Dataset<Row> enriched) {
        Dataset<Row> monthly = enriched
                .withColumn("year",  year(col(CrimeColumns.OCCURRED_ON_DATE)))
                .withColumn("month", month(col(CrimeColumns.OCCURRED_ON_DATE)))
                .groupBy(CrimeColumns.DISTRICT, "year", "month")
                .agg(count("*").as("monthly_count"));

        return monthly.groupBy(CrimeColumns.DISTRICT)
                .agg(expr("percentile_approx(monthly_count, 0.5)").as("crimes_monthly"));
    }
}
