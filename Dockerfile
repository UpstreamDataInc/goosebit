FROM python:3.12.4-alpine

ARG GOOSEBIT_VERSION

#RUN pip install --no-cache-dir goosebit[postgresql]==$GOOSEBIT_VERSION

COPY . /tmp/src
RUN cd /tmp/src && \
    pip install --no-cache-dir .[postgresql] && \
    cd - && \
    rm -rf /tmp/src

VOLUME /artifacts

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips=*", "goosebit:app"]
