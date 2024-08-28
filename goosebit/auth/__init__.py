from __future__ import annotations

import logging
from typing import Annotated, Iterable

from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException
from fastapi.requests import HTTPConnection, Request
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from joserfc import jwt
from joserfc.errors import BadSignatureError

from goosebit.settings import PWD_CXT, USERS, config
from goosebit.settings.schema import User

logger = logging.getLogger(__name__)


oauth2_auth = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


async def session_auth(connection: HTTPConnection) -> str:
    return connection.cookies.get("session_id")


def create_token(username: str) -> str:
    return jwt.encode(header={"alg": "HS256"}, claims={"username": username}, key=config.secret_key)


def get_user_from_token(token: str) -> User | None:
    if token is None:
        return
    try:
        token_data = jwt.decode(token, config.secret_key)
        username = token_data.claims["username"]
        return USERS.get(username)
    except (BadSignatureError, LookupError, ValueError):
        pass


def login_user(username: str, password: str) -> str:
    user = USERS.get(username)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        PWD_CXT.verify(user.hashed_pwd, password)
    except VerifyMismatchError:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_token(user.username)


def get_current_user(
    session_token: Annotated[str, Depends(session_auth)] = None,
    oauth2_token: Annotated[str, Depends(oauth2_auth)] = None,
) -> User:
    session_user = get_user_from_token(session_token)
    oauth2_user = get_user_from_token(oauth2_token)
    user = session_user or oauth2_user
    return user


# using | Request because oauth2_auth.__call__ expects is
async def get_user_from_request(connection: HTTPConnection | Request) -> User:
    token = await session_auth(connection) or await oauth2_auth(connection)
    return get_user_from_token(token)


def redirect_if_unauthenticated(connection: HTTPConnection, user: Annotated[User, Depends(get_current_user)]):
    if user is None:
        raise HTTPException(
            status_code=302,
            headers={"location": str(connection.url_for("login_get"))},
            detail="Invalid username",
        )


def redirect_if_authenticated(connection: HTTPConnection, user: Annotated[User, Depends(get_current_user)]):
    if user is not None:
        raise HTTPException(
            status_code=302,
            headers={"location": str(connection.url_for("ui_root"))},
            detail="Already logged in",
        )


def validate_current_user(user: Annotated[User, Depends(get_current_user)]):
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def validate_user_permissions(
    connection: HTTPConnection,
    security: SecurityScopes,
    user: User = Depends(get_current_user),
) -> HTTPConnection:
    if not check_permissions(security.scopes, user.permissions):
        logger.warning(f"{user.username} does not have sufficient permissions")
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return connection


def check_permissions(scopes: Iterable[str] | None, permissions: Iterable[str]) -> bool:
    deny_permissions = [p.lstrip("!") for p in permissions if p.startswith("!")]
    allow_permissions = [p for p in permissions if not p.startswith("!")]
    if scopes is None:
        return True
    for scope in scopes:
        if any([_check_permission(scope, permission) for permission in deny_permissions]):
            return False
        if not any([_check_permission(scope, permission) for permission in allow_permissions]):
            return False
    return True


def _check_permission(scope: str, permission: str) -> bool:
    split_scope = scope.split(".")
    for idx, permission in enumerate(permission.split(".")):
        if permission == "*":
            continue
        if not split_scope[idx] == permission:
            return False
    return True
