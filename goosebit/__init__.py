from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from goosebit import api, db, realtime, ui, updater
from goosebit.auth import (
    authenticate_user,
    auto_redirect,
    create_session,
    get_current_user,
)
from goosebit.ui.static import static
from goosebit.ui.templates import templates


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.init()
    yield
    await db.close()


app = FastAPI(lifespan=lifespan)
app.include_router(updater.router)
app.include_router(ui.router)
app.include_router(api.router)
app.include_router(realtime.router)
app.mount("/static", static, name="static")


@app.middleware("http")
async def attach_user(request: Request, call_next):
    request.scope["user"] = get_current_user(request)
    return await call_next(request)


@app.get("/", include_in_schema=False)
def root_redirect(request: Request):
    return RedirectResponse(request.url_for("ui_root"))


@app.get("/login", dependencies=[Depends(auto_redirect)], include_in_schema=False)
async def login_ui(request: Request):
    return templates.TemplateResponse("login.html", context={"request": request})


@app.post("/login", include_in_schema=False, dependencies=[Depends(authenticate_user)])
async def login(request: Request, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    resp = RedirectResponse(request.url_for("ui_root"), status_code=302)
    resp.set_cookie(key="session_id", value=create_session(form_data.username))
    return resp


@app.get("/logout", include_in_schema=False)
async def logout(request: Request):
    resp = RedirectResponse(request.url_for("login_ui"), status_code=302)
    resp.delete_cookie(key="session_id")
    return resp
