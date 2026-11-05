# Video starter kit for Claude

Make instructional and marketing videos by describing them to Claude. This kit gives Claude
the tools and the habits: AI voiceover with word timings (ElevenLabs), stock footage (Pexels),
captions from speech (Whisper, on your Mac), background removal for cutout art, and three video
templates (screen-recording tutorial, stock promo, paper-cutout explainer). Every frame is drawn
from an HTML page and joined with ffmpeg. There's no subscription video tool involved.

Made for the course *Make Instructional Videos with Claude* by [ID Atlas](https://idatlas.org).
You can use it without the course: open this folder in the Claude desktop app's Code tab and
describe the video you want.

## Setup (Mac)

1. Install [Homebrew](https://brew.sh) in Terminal and run its "Next steps".
2. In this folder: `./setup.sh` (about 10 minutes, mostly downloads; safe to run again).
3. Add your keys: `bash scripts/keys.sh` opens `.env` in TextEdit. Paste your Pexels and
   ElevenLabs keys after the `=` signs and save.
4. Check: `bash scripts/doctor.sh` then `.venv/bin/python scripts/check_keys.py`.

Then open this folder in the Claude desktop app's Code tab and describe the video you want.
`CLAUDE.md` tells Claude how to work here.

## Commands

All Python runs as `.venv/bin/python` from this folder.

| Job | Command |
|---|---|
| Voiceover + word timings | `scripts/voiceover.py projects/X/script.txt [--voice ID]` |
| List voices | `scripts/voiceover.py --voices [--search warm]` |
| Stock search / download | `scripts/stock.py search projects/X "query" --type video` / `get projects/X ID` |
| Cut a recording | `scripts/cut.py projects/X --suggest`, then without `--suggest` |
| Transcribe for captions | `scripts/transcribe.py projects/X/cut.mp4 --words "Names, Terms"` |
| Remove backgrounds | `scripts/cutout.py projects/X/art` |
| Find and hide private info | `scripts/redact.py shot.png --auto`, then `--blur` / `--replace` / `--dots` boxes |
| Preview sheet | `scripts/preview.py projects/X [--at 1,4.5] [--grid]` |
| Render | `scripts/render.py projects/X [--draft] [--from 10 --to 18]` |
| Caption files | `scripts/captions.py projects/X` |
| Sheet of a finished video | `scripts/preview.py --video projects/X/out.mp4 --every 2` |

## How a project works

`projects/<name>/project.json` names a template and lists what happens when. Each template's
`comp.html` starts with a comment documenting every field. Templates draw the frame for any time
`t` and must not depend on the clock or randomness, which is what lets the renderer split the work
across 8 browsers.

## Licenses

- Kit code: MIT ([LICENSE](LICENSE))
- Fonts in `templates/fonts/`: SIL Open Font License (Inter, Poppins, Caveat), license files included.
- Stock you download is under the Pexels License; `stock/credits.json` records each creator.
- Whisper models (downloaded by setup) are MIT.
