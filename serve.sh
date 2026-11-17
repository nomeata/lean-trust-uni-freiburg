#!/usr/bin/env bash
# Live-reloading preview: rebuilds on change, browser follows.
exec python3 "$(dirname "$0")/tools/serve.py" "$@"
