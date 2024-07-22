from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.requests import Request
from fastapi.security import SecurityScopes
from fastapi.websockets import WebSocket
from joserfc import jwt
from joserfc.errors import BadSignatureError

from goosebit.settings import PWD_CXT, SECRET, USERS


async def authenticate_user(request: Request):
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")
    user = USERS.get(username)
    if user is None:
        raise HTTPException(
            status_code=302,
            headers={"location": str(request.url_for("login"))},
            detail="Invalid credentials",
        )
    if not PWD_CXT.verify(user.hashed_pwd, password):
        raise HTTPException(
            status_code=302,
            headers={"location": str(request.url_for("login"))},
            detail="Invalid credentials",
        )
    return user


def create_session(username: str) -> str:
    return jwt.encode(
        header={"alg": "HS256"}, claims={"username": username}, key=SECRET
    )


def authenticate_session(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id is None:
        raise HTTPException(
            status_code=302,
            headers={"location": str(request.url_for("login"))},
            detail="Invalid session ID",
        )
    user = get_user_from_session(session_id)
    if user is None:
        raise HTTPException(
            status_code=302,
            headers={"location": str(request.url_for("login"))},
            detail="Invalid username",
        )
    return user


def authenticate_api_session(request: Request):
    session_id = request.cookies.get("session_id")
    user = get_user_from_session(session_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user


def authenticate_ws_session(websocket: WebSocket):
    session_id = websocket.cookies.get("session_id")
    user = get_user_from_session(session_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user


def auto_redirect(request: Request):
    session_id = request.cookies.get("session_id")
    if get_user_from_session(session_id) is None:
        return request
    raise HTTPException(
        status_code=302,
        headers={"location": str(request.url_for("ui_root"))},
        detail="Already logged in",
    )


def get_user_from_session(session_id: str):
    if session_id is None:
        return
    try:
        session_data = jwt.decode(session_id, SECRET)
        return session_data.claims["username"]
    except (BadSignatureError, LookupError):
        pass


def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    user = get_user_from_session(session_id)
    if user is None:
        return None
    return USERS[user]


def validate_user_permissions(
    request: Request,
    security: SecurityScopes,
    username: str = Depends(authenticate_session),
) -> Request:
    user = USERS[username]
    if security.scopes is None:
        return request
    for scope in security.scopes:
        if scope not in user.permissions:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions",
            )


def validate_ws_user_permissions(
    websocket: WebSocket,
    security: SecurityScopes,
    username: str = Depends(authenticate_ws_session),
) -> WebSocket:
    user = USERS[username]
    if security.scopes is None:
        return websocket
    for scope in security.scopes:
        if scope not in user.permissions:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions",
            )
