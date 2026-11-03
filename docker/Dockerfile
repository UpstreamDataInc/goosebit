FROM python:3.15.0-alpine@sha256:2699b90f4d562a22e2dd076c82f964032f64814204bff36d271a54ba4cc2c7e2

ARG GOOSEBIT_VERSION

RUN addgroup -g 1000 goosebit && \
    adduser -u 1000 -G goosebit -s /bin/sh -D goosebit && \
    mkdir /artifacts && \
    chown goosebit:goosebit /artifacts && \
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

SHELL ["/bin/sh", "-c"]
CMD aerich --config /aerich.toml upgrade && \
    gunicorn --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:60053 goosebit:app </dev/null
