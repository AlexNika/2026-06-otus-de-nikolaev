package ru.otus.de.hw08;

import ru.otus.de.hw08.config.AppConfig;

/**
 * Entry point. Отвечает только за lifecycle:
 * собрать контекст, запустить пайплайн, корректно закрыть Spark.
 * Логика пайплайна живёт в CrimesMartPipeline.
 */
public final class BostonCrimesMartApp {

    public static void main(String[] args) {
        AppConfig config = AppConfig.fromArgs(args);
        AppContext ctx = new AppContext(config);
        try {
            ctx.pipeline.execute(
                    config.crimesPath(),
                    config.offenseCodesPath(),
                    config.outputPath()
            );
        } finally {
            ctx.spark.stop();
        }
    }

    private BostonCrimesMartApp() {
    }
}
