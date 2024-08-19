import logging.config

import uvicorn

from goosebit import app
from goosebit.settings import config

logging.config.dictConfig(config.logging)

uvicorn_args = {"port": 8080}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", **uvicorn_args)
