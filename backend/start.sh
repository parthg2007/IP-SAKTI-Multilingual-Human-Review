#!/usr/bin/env bash
# IP-SAKTI Full-Stack Platform Launcher
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================================="
echo "  🌿 IP-SAKTI Full-Stack Launcher"
echo "================================================================="

# Run unified python runner
exec python3 run_dev.py "$@"
