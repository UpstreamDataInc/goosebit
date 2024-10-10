import importlib.metadata
from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor as Instrumentor
from tortoise.exceptions import ValidationError

from goosebit import api, auth, db, realtime, ui, updater
from goosebit.api.telemetry import metrics
from goosebit.auth import get_user_from_request
from goosebit.ui.nav import nav
from goosebit.ui.static import static

logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.init()
    await metrics.init()
    yield
    await db.close()


app = FastAPI(
    title="gooseBit",
    summary="A simplistic, opinionated remote update server implementing hawkBit™'s DDI API.",
    version=importlib.metadata.version("goosebit"),
    lifespan=lifespan,
    license_info={
        "name": "Apache 2.0",
        "identifier": "Apache-2.0",
    },
    redoc_url=None,
    docs_url=None,
    openapi_tags=[
        {
            "name": "login",
            "description": "API authentication.  "
            "Can be used in the `authorization` header, in the format `{token_type} {access_token}`.",
        }
    ],
)
app.include_router(updater.router)
app.include_router(ui.router)
app.include_router(api.router)
app.include_router(realtime.router)
app.include_router(auth.router)
app.mount("/static", static, name="static")
Instrumentor.instrument_app(app)


# Custom exception handler for Tortoise ValidationError
@app.exception_handler(ValidationError)
async def tortoise_validation_exception_handler(request: Request, exc: ValidationError):
    raise HTTPException(422, str(exc))


@app.middleware("http")
async def attach_user(request: Request, call_next):
    request.scope["user"] = await get_user_from_request(request)
    return await call_next(request)


@app.middleware("http")
async def attach_nav(request: Request, call_next):
    request.scope["nav"] = nav.get()
    return await call_next(request)


@app.get("/", include_in_schema=False)
def root_redirect(request: Request):
    return RedirectResponse(request.url_for("ui_root"))


@app.get("/logout", include_in_schema=False)
async def logout(request: Request):
    resp = RedirectResponse(request.url_for("login_get"), status_code=302)
    resp.delete_cookie(key="session_id")
    return resp


@app.get("/docs")
async def swagger_docs(request: Request):
    return get_swagger_ui_html(
        title="gooseBit docs",
        openapi_url="/openapi.json",
        swagger_favicon_url=str(request.url_for("static", path="/favicon.svg")),
        swagger_ui_parameters={"operationsSorter": "alpha"},
    )
