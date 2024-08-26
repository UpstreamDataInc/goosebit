from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.websockets import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from websockets.exceptions import ConnectionClosed

from goosebit.auth import validate_user_permissions
from goosebit.updater.manager import get_update_manager

router = APIRouter(prefix="/logs")


class RealtimeLogModel(BaseModel):
    log: str | None
    progress: int | None
    clear: bool = False


@router.websocket(
    "/{dev_id}",
    dependencies=[Security(validate_user_permissions, scopes=["home.read"])],
)
async def device_logs(websocket: WebSocket, dev_id: str):
    await websocket.accept()

    manager = await get_update_manager(dev_id)
    device = await manager.get_device()

    async def callback(log_update):
        data = RealtimeLogModel(log=log_update, progress=device.progress)
        if log_update is None:
            data.clear = True
            data.log = ""
        await websocket.send_json(dict(data))

    async with manager.subscribe_log(callback):
        try:
            while True:
                await websocket.receive()
        except (WebSocketDisconnect, ConnectionClosed, RuntimeError):
            pass
