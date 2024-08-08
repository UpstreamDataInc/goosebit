import logging

from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException
from fastapi.requests import HTTPConnection, Request
from fastapi.security import SecurityScopes
from joserfc import jwt
from joserfc.errors import BadSignatureError

from goosebit.settings import PWD_CXT, SECRET, USERS

logger = logging.getLogger(__name__)


class Authentication:
    def __init__(self, redirect: bool = False):
        if redirect:
            self.status_code = 302
        else:
            self.status_code = 401

    def __call__(self, connection: HTTPConnection):
        session_id = connection.cookies.get("session_id")
        headers = {"location": str(connection.url_for("login"))}
        if session_id is None:
            raise HTTPException(
                status_code=self.status_code,
                headers=headers,
                detail="Invalid session ID",
            )
        user = get_user_from_session(session_id)
        if user is None:
            raise HTTPException(
                status_code=self.status_code,
                headers=headers,
                detail="Invalid username",
            )
        return user


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
    try:
        if not PWD_CXT.verify(user.hashed_pwd, password):
            raise HTTPException(
                status_code=302,
                headers={"location": str(request.url_for("login"))},
                detail="Invalid credentials",
            )
    except VerifyMismatchError:
        raise HTTPException(
            status_code=302,
            headers={"location": str(request.url_for("login"))},
            detail="Invalid credentials",
        )
    return user


def create_session(username: str) -> str:
    return jwt.encode(header={"alg": "HS256"}, claims={"username": username}, key=SECRET)


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
    except (BadSignatureError, LookupError, ValueError):
        pass


def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    user = get_user_from_session(session_id)
    if user is None:
        return None
    return USERS[user]


def validate_user_permissions(
    connection: HTTPConnection,
    security: SecurityScopes,
    username: str = Depends(Authentication()),
) -> HTTPConnection:
    user = USERS[username]
    if security.scopes is None:
        return connection
    for scope in security.scopes:
        if scope not in user.permissions:
            logger.warning(f"User {username} does not have permission {scope}")
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions",
            )
