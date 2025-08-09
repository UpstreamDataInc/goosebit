#!/bin/sh

openssl rand -hex 4 >/etc/device-id

/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
