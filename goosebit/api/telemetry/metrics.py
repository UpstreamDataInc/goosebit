from collections.abc import Iterable

from opentelemetry import metrics
from opentelemetry.metrics import CallbackOptions, Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from goosebit.settings import config

from . import prometheus

readers = []

if config.metrics.prometheus.enable:
    readers.append(prometheus.reader)  # type: ignore[attr-defined]


resource = Resource(attributes={SERVICE_NAME: "goosebit"})

provider = MeterProvider(resource=resource, metric_readers=readers)
metrics.set_meter_provider(provider)

meter = metrics.get_meter("goosebit.meter")

# refreshed per scrape by refresh_counts(); gauge callbacks are sync and must not query the DB
_devices_count = 0
_users_count = 0


def _observe_devices(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(_devices_count)


def _observe_users(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(_users_count)


devices_count = meter.create_observable_gauge(
    "devices.count",
    callbacks=[_observe_devices],
    description="The number of connected devices",
)

users_count = meter.create_observable_gauge(
    "users.count",
    callbacks=[_observe_users],
    description="The number of registered users",
)


async def refresh_counts() -> None:
    global _devices_count, _users_count
    # lazy import, avoids a circular import with goosebit.db.models
    from goosebit.db.models import Device, User

    _devices_count = await Device.all().count()
    _users_count = await User.all().count()
