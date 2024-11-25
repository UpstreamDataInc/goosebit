from __future__ import annotations

from fastapi import APIRouter, Security

from goosebit.api.v1.devices.device import routes
from goosebit.auth import validate_user_permissions

router = APIRouter(prefix="/{dev_id}")

router.add_api_route(
    "/log",
    routes.device_logs,
    methods=["GET"],
    dependencies=[Security(validate_user_permissions, scopes=["device.read"])],
    name="bff_device_logs",
)
