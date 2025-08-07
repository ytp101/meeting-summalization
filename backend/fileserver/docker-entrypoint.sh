# docker-entrypoint.sh
chown -R app:appgroup /data 2>/dev/null || true
exec "$@"
