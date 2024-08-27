import logging.config

import uvicorn

from goosebit import app
from goosebit.settings import config

logging.config.dictConfig(config.logging)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.port)
