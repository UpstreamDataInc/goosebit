#!/bin/sh

DEVICE_ID=${DEVICE_ID:-$(openssl rand -hex 4)}

echo $DEVICE_ID >/etc/device-id

/usr/bin/supervisord
