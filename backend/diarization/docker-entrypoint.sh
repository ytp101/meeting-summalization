#!/usr/bin/env sh
# docker-entrypoint.sh

# 1) Fix permissions on the shared volume
#    We assume your app user is UID 1000 / GID 1000
chown -R 1000:1000 /data

# 2) Exec the service
exec "$@"
