from prometheus_client import Counter, Gauge, Histogram, start_http_server


# Counters

EVENTS_PROCESSED = Counter(
    "worker_events_processed_total",
    "Total number of events successfully processed and acked",
)

PROCESSING_ERRORS = Counter(
    "worker_processing_errors_total", "Total number of processing errors", ["error_type"]
)

# Histograms

BATCH_PROCESSING_TIME = Histogram(
    "worker_batch_processing_seconds",
    "Time spent processing a single batch (read + db_save + ack)",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Gauges

# Lag.
CONSUMER_LAG = Gauge(
    "worker_consumer_group_lag",
    "Approximate number of pending messages in the stream for this group",
)

# DLQ size
DLQ_SIZE = Gauge("worker_dlq_size", "Current number of messages in the Dead Letter Queue stream")


def start_metrics_server(port: int = 8001) -> None:
    start_http_server(port)
