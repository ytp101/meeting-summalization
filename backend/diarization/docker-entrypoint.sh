#!/usr/bin/env sh
chown -R "${APP_UID:-2000}:${APP_GID:-2000}" /data 2>/dev/null || true
chown -R app:appgroup /home/app/.cache || true
exec "$@"