FROM python:3.12.5-alpine

ARG GOOSEBIT_VERSION

RUN addgroup -g 1000 goosebit && \
    adduser -u 1000 -G goosebit -s /bin/sh -D goosebit && \
    pip install --no-cache-dir \
        gunicorn \
        goosebit[postgresql]==$GOOSEBIT_VERSION

COPY aerich.toml /

VOLUME /artifacts

EXPOSE 60053

USER goosebit

# We currently do not fully support multiple workers. For more information, see:
# https://github.com/UpstreamDataInc/goosebit/issues/125
ENV GUNICORN_CMD_ARGS="--workers 1 --enable-stdio-inheritance"

CMD aerich --config /aerich.toml upgrade && \
    gunicorn --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:60053 goosebit:app </dev/null
