#!/usr/bin/env bash
# SIH-Project Full-Stack Launcher
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

exec npm run dev
