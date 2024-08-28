from .const import BASE_DIR, PWD_CXT  # noqa: F401
from .schema import GooseBitSettings

config = GooseBitSettings()

USERS = {u.username: u for u in config.users}
