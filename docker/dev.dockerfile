FROM python:3.14.0-alpine@sha256:8373231e1e906ddfb457748bfc032c4c06ada8c759b7b62d9c73ec2a3c56e710

COPY . /tmp/src

RUN addgroup -g 1000 goosebit && \
    adduser -u 1000 -G goosebit -s /bin/sh -D goosebit && \
    mkdir /artifacts && \
    chown goosebit:goosebit /artifacts && \
    pip install --no-cache-dir \
        gunicorn \
        remote-pdb \
        /tmp/src[postgresql] && \
    rm -rf /tmp/src

COPY docker/aerich.toml /

VOLUME /artifacts

EXPOSE 60053

USER goosebit

# We currently do not fully support multiple workers. For more information, see:
# https://github.com/UpstreamDataInc/goosebit/issues/125
ENV GUNICORN_CMD_ARGS="--workers 1 --enable-stdio-inheritance"

SHELL ["/bin/sh", "-c"]
CMD aerich --config /aerich.toml upgrade && \
    gunicorn --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:60053 goosebit:app </dev/null
