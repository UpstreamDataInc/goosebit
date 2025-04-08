from __future__ import annotations

import logging
from typing import Annotated, Iterable

from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException
from fastapi.requests import HTTPConnection, Request
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from joserfc import jwt
from joserfc.errors import BadSignatureError

from goosebit.db.models import User
from goosebit.settings import PWD_CXT, config
from goosebit.users import UserManager

logger = logging.getLogger(__name__)


oauth2_bearer = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


async def oauth2_auth(connection: HTTPConnection):
    return await oauth2_bearer(connection)


async def session_auth(connection: HTTPConnection) -> str:
    return connection.cookies.get("session_id")


def create_token(username: str) -> str:
    return jwt.encode(header={"alg": "HS256"}, claims={"username": username}, key=config.secret_key)


async def get_user_from_token(token: str | None) -> User | None:
    if token is None:
        return None
    try:
        token_data = jwt.decode(token, config.secret_key)
        username = token_data.claims["username"]
        return await UserManager.get_user(username)
    except (BadSignatureError, LookupError, ValueError):
        return None


async def login_user(username: str, password: str) -> str:
    user = await UserManager.get_user(username)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.enabled:
        raise HTTPException(
            status_code=401,
            detail="User has been disabled, please contact your administrator",
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


async def get_current_user(
    session_token: Annotated[str | None, Depends(session_auth)] = None,
    oauth2_token: Annotated[str | None, Depends(oauth2_auth)] = None,
) -> User | None:
    session_user = await get_user_from_token(session_token)
    oauth2_user = await get_user_from_token(oauth2_token)
    user = session_user or oauth2_user
    return user


# using | Request because oauth2_auth.__call__ expects is
async def get_user_from_request(connection: HTTPConnection | Request) -> User | None:
    token = await session_auth(connection) or await oauth2_auth(connection)
    return await get_user_from_token(token)


async def redirect_if_unauthenticated(connection: HTTPConnection, user: Annotated[User, Depends(get_current_user)]):
    if user is None:
        raise HTTPException(
            status_code=302,
            headers={"location": str(connection.url_for("login_get"))},
            detail="Invalid username",
        )
    if not user.enabled:
        raise HTTPException(
            status_code=302,
            headers={"location": str(connection.url_for("login_get"))},
            detail="Disabled user",
        )


async def redirect_if_authenticated(connection: HTTPConnection, user: Annotated[User, Depends(get_current_user)]):
    if user is not None:
        if not user.enabled:
            return
        raise HTTPException(
            status_code=302,
            headers={"location": str(connection.url_for("ui_root"))},
            detail="Already logged in",
        )
    if await User.all().count() == 0:
        raise HTTPException(
            status_code=302,
            headers={"location": str(connection.url_for("setup_get"))},
            detail="No users set up",
        )


async def redirect_if_users_exist(connection: HTTPConnection):
    if await User.all().count() > 0:
        raise HTTPException(
            status_code=302,
            headers={"location": str(connection.url_for("login_get"))},
            detail="An admin user already exists",
        )


async def validate_current_user(user: Annotated[User, Depends(get_current_user)]):
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.enabled:
        raise HTTPException(
            status_code=401,
            detail="Disabled user",
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
