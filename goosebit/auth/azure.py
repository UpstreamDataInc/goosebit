import asyncio
from logging import getLogger

from fastapi import APIRouter
from fastapi.requests import Request
from starlette.responses import RedirectResponse

from goosebit.settings import config

logger = getLogger(__name__)

router = APIRouter(prefix="/azure", include_in_schema=False)

if config.auth.azure is not None:
    try:
        from msal import ConfidentialClientApplication
    except ImportError:
        logger.exception(
            """Azure config was specified, but `msal` is not installed.
            Please install with `pip install goosebit[azure]`"""
        )
        loop = asyncio.get_running_loop()
        loop.stop()

    app = ConfidentialClientApplication(
        client_id=config.auth.azure.client_id,
        authority=config.auth.azure.authority,
        client_credential=config.auth.azure.client_secret,
    )

    @router.get("")
    async def login_azure(request: Request):
        auth_url = app.initiate_auth_code_flow(["User.Read"], redirect_uri=str(request.url_for("login_azure_post")))
        return RedirectResponse(auth_url)

    @router.post("")
    async def login_azure_post(request: Request, code: str):
        # TODO: Not sure how to use this exactly...
        app.acquire_token_by_auth_code_flow(
            code, scopes=["User.Read"], redirect_uri=str(request.url_for("login_azure_post"))
        )
