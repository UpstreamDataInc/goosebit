from fastapi import APIRouter

from goosebit.settings import config

from . import prometheus

router = APIRouter(prefix="/telemetry")
if config.metrics.prometheus.enable:
    router.include_router(prometheus.router)
