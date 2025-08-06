#!/bin/sh

# Fix permissions on mounted cache
echo "🔧 Fixing /home/app/.cache permissions..."
chown -R app:appgroup /home/app/.cache || true

exec "$@"
