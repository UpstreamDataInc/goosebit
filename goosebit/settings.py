from dataclasses import dataclass
from pathlib import Path

from passlib.context import CryptContext

from goosebit import permissions

POLL_SECONDS = 0
POLL_MINUTES = 1
POLL_HOURS = 0
POLL_TIME = ":".join(
    [
        str(POLL_HOURS).rjust(2, "0"),
        str(POLL_MINUTES).rjust(2, "0"),
        str(POLL_SECONDS).rjust(2, "0"),
    ]
)

BASE_DIR = Path(__file__).resolve().parent
TOKEN_SWU_DIR = BASE_DIR.joinpath("swugen")
SWUPDATE_FILES_DIR = BASE_DIR.joinpath("swupdate")
UPDATES_DIR = BASE_DIR.joinpath("updates")
DB_LOC = BASE_DIR.joinpath("db.sqlite3")
DB_MIGRATIONS_LOC = BASE_DIR.joinpath("migrations")
DB_URI = f"sqlite:///{DB_LOC}"

SECRET = "123456789"
PWD_CXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

users = {}


@dataclass
class User:
    username: str
    hashed_pwd: str
    permissions: list

    def get_json_permissions(self):
        return [str(p) for p in self.permissions]


def add_user(user: User):
    users[user.username] = user


# User configuration
add_user(
    User(
        username="admin@goosebit.local",
        hashed_pwd=PWD_CXT.hash("admin"),
        permissions=permissions.ADMIN,
    )
)
USERS = users
