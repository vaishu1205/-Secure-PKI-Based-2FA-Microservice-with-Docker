#!/usr/bin/env bash
set -e
if [ ! -d /data ]; then
  mkdir -p /data
fi
if [ ! -d /cron ]; then
  mkdir -p /cron
fi
service cron start || /etc/init.d/cron start || (cron &)
exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --proxy-headers

