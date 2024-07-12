import uvicorn

from goosebit import app

uvicorn_args = {"port": 80}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", **uvicorn_args)
