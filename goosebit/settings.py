import secrets
from dataclasses import dataclass
from pathlib import Path

import yaml
from argon2 import PasswordHasher

from goosebit.permissions import Permissions

BASE_DIR = Path(__file__).resolve().parent.parent
TOKEN_SWU_DIR = BASE_DIR.joinpath("swugen")
SWUPDATE_FILES_DIR = BASE_DIR.joinpath("swupdate")
UPDATES_DIR = BASE_DIR.joinpath("updates")
DB_MIGRATIONS_LOC = BASE_DIR.joinpath("migrations")

SECRET = secrets.token_hex(16)
PWD_CXT = PasswordHasher()

with open(BASE_DIR.joinpath("settings.yaml"), "r") as f:
    config = yaml.safe_load(f.read())

POLL_TIME = config.get("poll_time_default", "00:01:00")
POLL_TIME_UPDATING = config.get("poll_time_updating", "00:00:05")

DB_LOC = BASE_DIR.joinpath(config.get("db_location", "db.sqlite3"))
DB_URI = f"sqlite:///{DB_LOC}"


users = {}


@dataclass
class User:
    username: str
    hashed_pwd: str
    permissions: set

    def get_json_permissions(self):
        return [str(p) for p in self.permissions]


def add_user(u: User):
    users[u.username] = u


for user in config.get("users", []):
    permissions = set()
    for p in user["permissions"]:
        permissions.update(Permissions.from_str(p))
    add_user(
        User(
            username=user["email"],
            hashed_pwd=PWD_CXT.hash(user["password"]),
            permissions=permissions,
        )
    )

USERS = users
