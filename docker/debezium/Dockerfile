FROM quay.io/debezium/connect:3.0

USER root
RUN microdnf install -y unzip && microdnf clean all

USER kafka

RUN curl -L -o /tmp/avro-converter.zip \
    "https://api.hub.confluent.io/api/plugins/confluentinc/kafka-connect-avro-converter/versions/7.8.0/archive" \
    && unzip /tmp/avro-converter.zip -d /tmp/avro-converter/ \
    && mkdir -p /kafka/connect/confluent-avro-converter \
    && mv /tmp/avro-converter/confluentinc-kafka-connect-avro-converter-7.8.0/lib/*.jar \
    /kafka/connect/confluent-avro-converter/ \
    && rm -rf /tmp/avro-converter.zip /tmp/avro-converter
