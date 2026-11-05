#!/usr/bin/env bash
# Check that everything is installed and the keys are in place. Prints no secrets.
cd "$(dirname "$0")/.."
ok=1
check() { if eval "$2" >/dev/null 2>&1; then echo "OK   $1"; else echo "MISSING  $1  ->  $3"; ok=0; fi; }
check "Homebrew"            "command -v brew"                         "install from https://brew.sh"
check "ffmpeg"              "command -v ffmpeg"                       "brew install ffmpeg"
check "whisper-cpp"         "command -v whisper-cli"                  "brew install whisper-cpp"
check "Python packages"     ".venv/bin/python -c 'import playwright, PIL, requests'" "./setup.sh"
check "Background remover"  ".venv/bin/python -c 'import rembg'"      "./setup.sh"
check "Chromium"            ".venv/bin/python -c 'from playwright.sync_api import sync_playwright as s; p=s().start(); b=p.chromium.launch(); b.close(); p.stop()'" ".venv/bin/python -m playwright install chromium"
check "Speech model"        "test -s models/ggml-small.en.bin -o -n \"\$WHISPER_MODEL\""   "./setup.sh"
check ".env file"           "test -f .env"                            "bash scripts/keys.sh"
for k in PEXELS_API_KEY ELEVENLABS_API_KEY; do
  check "$k in .env" "grep -Eq '^$k=[^p ].{8,}' .env" "bash scripts/keys.sh, then paste the key"
done
[ $ok = 1 ] && echo "Everything is installed. Next: .venv/bin/python scripts/check_keys.py" || echo "Fix the MISSING lines above."
