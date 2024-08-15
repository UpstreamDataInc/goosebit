from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import start_http_server

from goosebit.settings import PROMETHEUS_PORT

# separate file to enable it as a feature later.
reader = PrometheusMetricReader()
start_http_server(port=PROMETHEUS_PORT, addr="0.0.0.0")
