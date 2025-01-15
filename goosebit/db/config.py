import logging
from urllib.parse import parse_qs, urlparse

from goosebit.db.pg_ssl_context import PostgresSSLContext
from goosebit.settings import config


def add_models(models_path: str):
    models.append(models_path)


models = ["goosebit.db.models", "aerich.models"]

TORTOISE_CONF = {
    "connections": {"default": config.db_uri},
    "apps": {
        "models": {
            "models": models,
        },
    },
}

if config.db_ssl_crt is not None:
    # config.db_uri must have the following style:
    # postgres://<user>:<password>@<host>:<port>/<database>?sslmode=<sslmode>
    parsed = urlparse(config.db_uri)
    if parsed.scheme != "postgres":
        logging.error("database scheme must be postgres!")
        exit(1)

    # parse parameters
    params = parse_qs(parsed.query)

    # create ssl context for postgres
    ssl_context = PostgresSSLContext()

    # set certificate file
    ssl_context.load_verify_locations(config.db_ssl_crt)

    # parse and set verify-flags
    if params.get("verifyflags") is not None:
        ssl_context.parse_verify_flags(params["verifyflags"][0])

    # parse and set ssl verify-mode
    if params.get("sslmode") is not None:
        ssl_context.parse_ssl_mode(params["sslmode"][0])

    # update database configuration
    TORTOISE_CONF = {
        "connections": {
            "default": {
                "engine": "tortoise.backends.asyncpg",
                "credentials": {
                    "host": parsed.hostname,
                    "port": parsed.port,
                    "user": parsed.username,
                    "password": parsed.password,
                    "database": parsed.path.lstrip("/"),
                    "ssl": ssl_context.context,
                },
            },
        },
        "apps": {
            "models": {"models": ["goosebit.db.models", "aerich.models"], "default_connection": "default"},
        },
    }
