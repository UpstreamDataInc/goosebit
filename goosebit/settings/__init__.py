from .const import BASE_DIR, DB_MIGRATIONS_LOC, PWD_CXT  # noqa: F401
from .schema import GooseBitSettings

config = GooseBitSettings()

USERS = {u.username: u for u in config.users}
