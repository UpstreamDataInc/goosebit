from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send


class ForwardedHeaderMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            headers = MutableHeaders(scope=scope)
            if (forwarded_raw := headers.get("forwarded")) is not None:
                # We are only interested in the values set by the first proxy
                forwarded_pairs = [p.split("=") for p in forwarded_raw.split(",")[0].split(";")]
                forwarded = {k.strip(): v.strip() for k, v in forwarded_pairs}

                if (for_ := forwarded.get("for")) is not None:
                    # We've lost the connecting client's port information by
                    # now, so only include the host.
                    port = 0
                    scope["client"] = (for_, port)

                if (host := forwarded.get("host")) is not None:
                    headers["host"] = host

                if (proto := forwarded.get("proto")) is not None:
                    if scope["type"] == "websocket":
                        scope["scheme"] = proto.replace("http", "ws")
                    else:
                        scope["scheme"] = proto

        await self.app(scope, receive, send)
