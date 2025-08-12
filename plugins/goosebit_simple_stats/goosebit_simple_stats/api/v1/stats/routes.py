from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.requests import Request
from goosebit_simple_stats.schema import SimpleStatsShow
from goosebit_simple_stats.settings import config

from goosebit.auth import validate_user_permissions
from goosebit.db.models import Device, Software

from .responses import SimpleStatsResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["stats.read"])],
)
async def stats_get(_: Request) -> SimpleStatsResponse:
    data = {}
    if SimpleStatsShow.DEVICE_COUNT in config.simple_stats_show:
        data["device_count"] = await Device.all().count()
    if SimpleStatsShow.SOFTWARE_COUNT in config.simple_stats_show:
        data["software_count"] = await Software.all().count()

    return SimpleStatsResponse(**data)
