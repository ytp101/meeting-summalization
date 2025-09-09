#!/bin/sh
set -e

# Read models from OLLAMA_MODELS, or fall back to PASS1_MODEL + PASS2_MODEL.
MODELS="${OLLAMA_MODELS:-}"
[ -z "$MODELS" ] && MODELS="${PASS1_MODEL:-} ${PASS2_MODEL:-}"

echo "[entrypoint] Starting ollama serve…"
/bin/ollama serve &
pid=$!

# Ensure child is reaped on SIGTERM/SIGINT
trap 'echo "[entrypoint] Stopping ollama…"; kill $pid 2>/dev/null || true; wait $pid 2>/dev/null || true; exit 0' INT TERM

# Wait until the server is responsive. Use the CLI so we don’t depend on curl.
echo "[entrypoint] Waiting for ollama to be ready…"
tries=0
max_tries="${OLLAMA_WAIT_TRIES:-60}"     # ~60 seconds by default
sleep_s="${OLLAMA_WAIT_SLEEP:-1}"

until /bin/ollama ps >/dev/null 2>&1; do
  tries=$((tries+1))
  if [ "$tries" -ge "$max_tries" ]; then
    echo "[entrypoint] ERROR: ollama did not become ready in time."
    kill $pid 2>/dev/null || true
    wait $pid 2>/dev/null || true
    exit 1
  fi
  sleep "$sleep_s"
done
echo "[entrypoint] Ollama is up."

# Pull models (space-separated)
for m in $MODELS; do
  if [ -n "$m" ]; then
    echo "[entrypoint] Pulling model: $m"
    /bin/ollama pull "$m" || echo "[entrypoint] WARN: pull failed for $m (may already exist)"
  fi
done

echo "[entrypoint] Warmup complete. Handing off to ollama (PID $pid)…"
wait $pid
