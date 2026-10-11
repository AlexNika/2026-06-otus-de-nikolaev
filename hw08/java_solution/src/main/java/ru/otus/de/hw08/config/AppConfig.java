package ru.otus.de.hw08.config;

import org.checkerframework.checker.nullness.qual.NonNull;

/** Неизменяемая конфигурация приложения. */
public record AppConfig(String crimesPath,
                        String offenseCodesPath,
                        String outputPath,
                        String master) {

    /** Пути по умолчанию - относительно рабочей директории hw08/java_solution. */
    public static final String DEFAULT_CRIMES_PATH = "../data/crime.csv";
    public static final String DEFAULT_OFFENSE_CODES_PATH = "../data/offense_codes.csv";
    public static final String DEFAULT_OUTPUT_PATH = "../data/output/java";

    public static AppConfig fromArgs(String @NonNull [] args) {
        return new AppConfig(
                argOrDefault(args, 0, DEFAULT_CRIMES_PATH),
                argOrDefault(args, 1, DEFAULT_OFFENSE_CODES_PATH),
                argOrDefault(args, 2, DEFAULT_OUTPUT_PATH),
                argOrDefault(args, 3, null));
    }

    private static String argOrDefault(String @NonNull [] args, int index, String fallback) {
        return args.length > index && !args[index].isBlank() ? args[index] : fallback;
    }
}
