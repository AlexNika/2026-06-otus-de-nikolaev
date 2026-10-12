# syntax=docker/dockerfile:1

# ---------- Stage 1: сборка jar (java_solution) ----------
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build
COPY java_solution/pom.xml .
RUN --mount=type=cache,target=/root/.m2 mvn -B -q dependency:go-offline
COPY java_solution/src ./src
RUN --mount=type=cache,target=/root/.m2 mvn -B -q clean package -DskipTests

# ---------- Stage 2: runtime (Java 21 + Python 3, Spark 4.2.0) ----------
FROM apache/spark:4.2.0-scala2.13-java21-python3-ubuntu
USER root
RUN mkdir -p /opt/spark/app && chown -R spark:spark /opt/spark/app
COPY --from=build --chown=spark:spark /build/target/boston-crimes-mart-1.0.0.jar /opt/spark/app/
COPY --chown=spark:spark pyspark_solution/boston_crimes_mart_app.py /opt/spark/app/
COPY --chown=spark:spark pyspark_solution/boston_crimes_mart /opt/spark/app/boston_crimes_mart
COPY --chown=spark:spark tools /opt/spark/app/tools
USER spark
