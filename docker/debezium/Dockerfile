FROM debezium/connect:3.0

USER root
RUN microdnf install -y unzip && microdnf clean all

USER kafka

RUN curl -L -o /tmp/avro-converter.zip \
    "https://api.hub.confluent.io/api/plugins/confluentinc/kafka-connect-avro-converter/versions/7.8.0/archive" \
    && unzip /tmp/avro-converter.zip -d /kafka/connect/ \
    && rm /tmp/avro-converter.zip
