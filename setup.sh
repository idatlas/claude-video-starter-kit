#!/usr/bin/env bash
# Install everything the kit needs. Safe to run again: it skips what's already there.
# Needs Homebrew (https://brew.sh) first; the course shows how to install it.
set -euo pipefail
cd "$(dirname "$0")"
say() { printf "\n== %s\n" "$1"; }

if ! command -v brew >/dev/null; then
  echo "Homebrew isn't installed yet. Install it first (Module 3, step 1), then run this again."
  exit 1
fi

say "Video and speech tools (ffmpeg, whisper-cpp)"
brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
brew list whisper-cpp >/dev/null 2>&1 || brew install whisper-cpp
brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12

say "Python packages (in a private .venv folder, so nothing else on your Mac changes)"
PY="$(brew --prefix python@3.12)/bin/python3.12"
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

say "Browser for drawing frames (Chromium, about 150 MB)"
.venv/bin/python -m playwright install chromium

say "Speech model for captions (about 470 MB, one time)"
mkdir -p models
M=models/ggml-small.en.bin
[ -s "$M" ] || curl -L --fail -o "$M" https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin

say "Your keys file"
[ -f .env ] || { cp .env.example .env; chmod 600 .env; echo "Made .env from .env.example"; }

say "Check"
bash scripts/doctor.sh
