from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from goosebit.settings import USERS, config

from . import prometheus

readers = []

if config.metrics.prometheus.enable:
    readers.append(prometheus.reader)


resource = Resource(attributes={SERVICE_NAME: "goosebit"})

provider = MeterProvider(resource=resource, metric_readers=readers)
metrics.set_meter_provider(provider)

meter = metrics.get_meter("goosebit.meter")

devices_count = meter.create_gauge(
    "devices.count",
    description="The number of connected devices",
)

users_count = meter.create_gauge(
    "users.count",
    description="The number of registered users",
)


async def init():
    users_count.set(len(USERS))
