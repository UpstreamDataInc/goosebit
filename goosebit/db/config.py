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
