FROM alpine:3.22 AS build

WORKDIR /app

RUN apk add --no-cache alpine-sdk python3 cmake zlib-dev linux-headers \
    bsd-compat-headers yaml-dev json-c-dev curl-dev libconfig-dev \
    libarchive-dev openssl-dev mtd-utils-dev xz-dev zstd-dev zeromq-dev \
    libwebsockets-dev uriparser-dev lua5.2-dev

RUN ln -s /usr/lib/lua5.2/liblua.so /usr/lib/liblua.so

RUN git clone https://github.com/sbabic/libubootenv && \
    cd libubootenv && \
    git reset --hard 5e6d8b6318be809ac5a8989756ade45ece88ca7e && \
    mkdir -p build && cd build && cmake .. && make && make install

RUN git clone https://github.com/sbabic/swupdate && cd swupdate && \
    git reset --hard cad85ea38ccd53bb5174c2f5fa3fb31a8d469a39 && \
    cd scripts/basic && gcc fixdep.c -o fixdep

COPY config /app/swupdate/.config

RUN cd /app/swupdate && make

FROM alpine:3.22 AS image

RUN apk add --no-cache yaml json-c lua5.2-libs libcurl libconfig \
    libarchive mtd-utils xz zstd zeromq libwebsockets uriparser \
    supervisor openssl bash

COPY --from=build /usr/local/lib/libubootenv.so.0.3.6 /usr/local/lib/libubootenv.so.0

RUN mkdir -p /var/log/swupdate /var/log/myscript /var/log/supervisor
COPY --from=build /app/swupdate/swupdate /usr/bin/swupdate
COPY swupdate.cfg /etc/swupdate.cfg
COPY supervisord.conf /etc/supervisord.conf
COPY myscript.py /usr/local/bin/myscript.py
COPY hwrevision /etc/hwrevision
COPY sw-versions /etc/sw-versions
COPY entrypoint.sh /entrypoint.sh

CMD ["/entrypoint.sh"]
