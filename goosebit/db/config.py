from goosebit.settings import config

TORTOISE_CONF = {
    "connections": {"default": config.db_uri},
    "apps": {
        "models": {
            "models": ["goosebit.db.models", "aerich.models"],
        },
    },
}
