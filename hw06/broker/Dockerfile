FROM apache/kafka:4.3.1

USER root

RUN set -eux; \
    apk add --no-cache wget ca-certificates; \
    mkdir -p /opt/kafka/jmx-exporter /var/lib/kafka/data; \
    wget -q -O /opt/kafka/jmx-exporter/jmx_prometheus_javaagent.jar \
      https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/1.0.1/jmx_prometheus_javaagent-1.0.1.jar; \
    echo "f9c53eb0aa1828c3c9cd7647238563e43a4ed68c  /opt/kafka/jmx-exporter/jmx_prometheus_javaagent.jar" > /tmp/jar.sha1; \
    sha1sum -c /tmp/jar.sha1; \
    rm -f /tmp/jar.sha1; \
    chown -R appuser:appuser /opt/kafka/jmx-exporter /var/lib/kafka/data

COPY --chown=appuser:appuser kafka-config.yml /opt/kafka/jmx-exporter/kafka-metrics-config.yml

USER appuser
