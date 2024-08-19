from fastapi import APIRouter, Header
from fastapi.requests import Request
from fastapi.responses import Response
from prometheus_client import REGISTRY
from prometheus_client.exposition import _bake_output

router = APIRouter(prefix="/prometheus", tags=["prometheus"])


@router.get("/metrics")
async def metrics(
    request: Request, accept: list[str] = Header(None), accept_encoding: list[str] = Header(None)
) -> Response:
    status, http_headers, output = _bake_output(
        REGISTRY, ",".join(accept), ",".join(accept_encoding), request.query_params, False
    )
    headers = {h[0]: h[1] for h in http_headers}
    return Response(content=output, headers=headers)
