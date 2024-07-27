import logging.config

import uvicorn
import yaml

from goosebit import app

with open("logging_config.yaml", "r") as file:
    config = yaml.safe_load(file.read())
    logging.config.dictConfig(config)

uvicorn_args = {"port": 80}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", **uvicorn_args)
