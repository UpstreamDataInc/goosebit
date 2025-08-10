FROM ubuntu:plucky AS build

ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /app && apt update && apt install -y build-essential \
    automake \
    cmake \
    curl \
    libzmq3-dev \
    liblua5.2-dev \
    libluajit-5.1-dev \
    libconfig-dev \
    libarchive-dev \
    libbtrfsutil-dev \
    libjson-c-dev \
    libyaml-dev \
    zlib1g-dev \
    git \
    uuid \
    uuid-dev \
    liblzo2-dev \
    libsystemd-dev \
    libsystemd0 \
    check \
    librsync2 \
    librsync-dev \
    libext2fs-dev \
    liburiparser-dev \
    doxygen \
    graphviz \
    autoconf-archive \
    linux-headers-generic \
    libmbedtls-dev \
    libcmocka-dev \
    libfdisk-dev \
    libwebsockets-dev \
    libgpiod-dev \
    libcurl4-openssl-dev \
    libpci-dev \
    gawk \
    cpio \
    meson \
    ninja-build \
    libzstd-dev \
    wget \
    python3 \
    libebgenv-dev \
    libmtd-dev \
    libubi-dev \
    libubootenv-dev \
    libzck-dev

WORKDIR /app

RUN git clone https://github.com/sbabic/swupdate && cd swupdate && git reset --hard cad85ea

COPY config /app/swupdate/.config

RUN cd swupdate/scripts/basic && gcc fixdep.c -o fixdep

RUN cd swupdate && make

FROM ubuntu:plucky AS image

ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt update && apt install -y libubootenv0.1 libjson-c5 liblua5.2-0 libcurl4 libconfig11 libarchive13 libzmq5 liburiparser1 libwebsockets19t64 supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/log/swupdate /var/log/myscript /etc/supervisor/conf.d
COPY --from=build /app/swupdate/swupdate /usr/bin/swupdate
COPY swupdate.cfg /etc/swupdate.cfg
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY myscript.py /usr/local/bin/myscript.py
COPY hwrevision /etc/hwrevision
COPY sw-versions /etc/sw-versions
COPY entrypoint.sh /entrypoint.sh

CMD ["/entrypoint.sh"]
