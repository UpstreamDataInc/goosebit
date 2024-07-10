from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.requests import Request
from fastapi.security import SecurityScopes
from fastapi.websockets import WebSocket
from jose import jwt

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
    if not PWD_CXT.verify(password, user.hashed_pwd):
        raise HTTPException(
            status_code=302,
            headers={"location": str(request.url_for("login"))},
            detail="Invalid credentials",
        )
    return user


sessions = {}


def create_session(email: str) -> str:
    token = jwt.encode({"email": email}, SECRET)
    sessions[token] = email
    return token


def authenticate_session(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id is None or session_id not in sessions:
        raise HTTPException(
            status_code=302,
            headers={"location": str(request.url_for("login"))},
            detail="Invalid session ID",
        )
    user = get_user_from_session(session_id)
    return user


def authenticate_api_session(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id is None or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not logged in")
    user = get_user_from_session(session_id)
    return user


def authenticate_ws_session(websocket: WebSocket):
    session_id = websocket.cookies.get("session_id")
    if session_id is None or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not logged in")
    user = get_user_from_session(session_id)
    return user


def auto_redirect(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id is None or session_id not in sessions:
        return request
    raise HTTPException(
        status_code=302,
        headers={"location": str(request.url_for("ui_root"))},
        detail="Already logged in",
    )


def get_user_from_session(session_id: str):
    for username in USERS:
        if username == sessions.get(session_id):
            return username


def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id is None or session_id not in sessions:
        return None
    user = get_user_from_session(session_id)
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
