import os
from pathlib import Path

from argon2 import PasswordHasher

GOOSEBIT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CURRENT_DIR = Path(os.getcwd())

PWD_CXT = PasswordHasher()

LOGGING_DEFAULT = {
    "version": 1,
    "formatters": {"simple": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple", "level": "DEBUG"}},
    "loggers": {
        "tortoise": {"handlers": ["console"], "level": "WARNING", "propagate": True},
        "aiosqlite": {"handlers": ["console"], "level": "WARNING", "propagate": True},
        "multipart": {"handlers": ["console"], "level": "INFO", "propagate": True},
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}
