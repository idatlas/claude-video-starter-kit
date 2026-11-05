#!/usr/bin/env bash
# Open your .env file in a plain text editor so you can paste your keys. Never paste keys into a chat.
cd "$(dirname "$0")/.."
[ -f .env ] || cp .env.example .env
chmod 600 .env
if [ "$(uname)" = "Darwin" ]; then open -e .env; else notepad .env 2>/dev/null || ${EDITOR:-nano} .env; fi
echo "Opened .env. Paste each key after its = sign, save (Cmd+S), and close the window."
