FROM quay.io/debezium/connect:3.0

USER root
RUN microdnf install -y unzip && microdnf clean all

USER kafka

# Confluent Hub archive extracts to:
#   confluentinc-kafka-connect-avro-converter-7.8.0/lib/*.jar
# Kafka Connect plugin.path=/kafka/connect scans only ONE level deep:
#   /kafka/connect/<plugin-dir>/*.jar  ← OK
#   /kafka/connect/<plugin-dir>/lib/*.jar  ← NOT scanned
# So we move the JARs up to the plugin root directory.
RUN curl -L -o /tmp/avro-converter.zip \
    "https://api.hub.confluent.io/api/plugins/confluentinc/kafka-connect-avro-converter/versions/7.8.0/archive" \
    && unzip /tmp/avro-converter.zip -d /tmp/avro-converter/ \
    && mkdir -p /kafka/connect/confluent-avro-converter \
    && mv /tmp/avro-converter/confluentinc-kafka-connect-avro-converter-7.8.0/lib/*.jar \
       /kafka/connect/confluent-avro-converter/ \
    && rm -rf /tmp/avro-converter.zip /tmp/avro-converter
