from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import start_http_server

from goosebit import settings

PROMETHEUS_PORT = (
    settings.config.get("metrics", {}).get("prometheus", {}).get("port", 9090)
)

# separate file to enable it as a feature later.
reader = PrometheusMetricReader()
start_http_server(port=PROMETHEUS_PORT, addr="0.0.0.0")
