# Video starter kit: instructions for Claude

You are helping someone who is new to the terminal make instructional and marketing videos. They
will not read code. Explain what you're doing in plain words, show them pictures, and ask before
anything that costs money or takes more than a few minutes.

## How a video is made here

Each video is a folder in `projects/` with a `project.json`. The `template` in it is an HTML page
in `templates/` that draws one frame for any time `t`. You change the video by editing
`project.json` (most edits) or the template (new kinds of motion). Copy a starting point from
`examples/`.

Always run Python as `.venv/bin/python` from this folder.

| Step | Command |
|---|---|
| Check the setup | `bash scripts/doctor.sh`, then `.venv/bin/python scripts/check_keys.py` |
| Voiceover from a script | `.venv/bin/python scripts/voiceover.py projects/X/script.txt [--voice ID]` |
| List voices | `.venv/bin/python scripts/voiceover.py --voices [--search "warm"]` |
| Stock search / download | `.venv/bin/python scripts/stock.py search projects/X "query" --type video` / `get projects/X ID --type video` |
| Cut a recording | `.venv/bin/python scripts/cut.py projects/X --suggest`, then write `keep`, then run without `--suggest` |
| Captions from speech | `.venv/bin/python scripts/transcribe.py projects/X/cut.mp4 --words "names, terms"` |
| Remove backgrounds | `.venv/bin/python scripts/cutout.py projects/X/art` |
| Find private info | `.venv/bin/python scripts/redact.py <image> --auto` |
| Redact a screenshot | `.venv/bin/python scripts/redact.py shot.png --blur x,y,w,h --replace "x,y,w,h=Alex Rivera" --dots x,y,w,h` |
| **Preview** | `.venv/bin/python scripts/preview.py projects/X [--at 1,4.5,9]` |
| Draft render | `.venv/bin/python scripts/render.py projects/X --draft` |
| Final render | `.venv/bin/python scripts/render.py projects/X` |
| Caption files | `.venv/bin/python scripts/captions.py projects/X` |
| Check a finished video | `.venv/bin/python scripts/preview.py --video projects/X/out.mp4 --every 2` |

## Order of work (follow it every time)

1. **Inspect what you were given.** For a recording, `ffprobe` it and make a sheet
   (`preview.py --video ... --every 3`) and look at it before planning.
2. **Privacy check.** Screen recordings and screenshots show names, emails, account IDs, keys,
   other people's work and sidebars full of client names. Run `scripts/redact.py <frame> --auto`
   on a few frames (and on every screenshot), list what you'd hide and how (blur, fake text,
   dots), and get a yes. Then add `blur` / `replace` / `dots` notes (recordings) or run
   `redact.py` with boxes (screenshots). Use believable fake details ("Alex Rivera",
   "alex@example.com"), make the box a little wider than the real text, and keep the fake text
   no longer than the real. Check the result in the preview: nothing real may show in any frame.
3. **Plan in a table** (time, what's said, what's on screen) and show it to the person. Get a yes.
4. **Sound first.** The voice (recorded or generated) sets every time. Make `words.json` before
   timing anything. Nothing is timed by eye.
5. **Build `project.json`**, keying each scene, zoom and note to a word's start time in `words.json`.
6. **Preview before rendering.** Run `preview.py`, open `preview.png` with the Read tool so you can
   see it, check it yourself (text cut off? caption covering something important? wrong picture?),
   fix what you find, then show the person the sheet and ask for notes. Never skip this.
7. **Draft render** if the timing or sound needs checking, then the **final render**.
8. **Check the output**: make a sheet of `out.mp4` and look at it; confirm the length matches the voice.
9. Tell the person where the file is, how long the render took, and what you did NOT do.

## Captions (default style)

White, bold, black outline and shadow, bottom center, whole phrase at a time (`"mode": "phrase"`).
Change with `"captions": {"mode": "karaoke" | "pop" | "phrase" | "off", "position": "top", "topDuring": [[12, 15.5]], "style": {...}}`
(`topDuring` moves captions to the top for those seconds only, e.g. while a click happens at the bottom),
where style is CSS variables from `templates/lib/base.css`: `--cap-color`, `--cap-size`,
`--cap-font`, `--cap-weight`, `--cap-bg` (a box behind the words), `--cap-highlight`,
`--cap-bottom`, `--cap-shadow`. Always also offer `captions.py` for a `.srt`/`.vtt` file.

## Rules

- **Never ask for, print, or echo an API key.** Keys live in `.env`. If one is missing, run
  `bash scripts/keys.sh` (it opens `.env` in TextEdit) and ask the person to paste it there.
  If they paste a key into the chat anyway, tell them to make a new key and delete that one.
- **Ask before spending credits**: say roughly how many characters a voiceover is before running it.
- **Templates must stay deterministic**: what's drawn depends only on `t`. No `Date.now()`,
  `Math.random()`, CSS transitions or CSS animations. Use `K.hash(n)` for repeatable randomness.
- **Positions in notes and zooms are fractions of the recording** (0 to 1). Find them with
  `preview.py projects/X --at <time> --grid`, which draws a 0.1 grid over the recording.
- **Calm motion.** One effect at a time. Zooms take 0.7 s. Nothing flashes.
- **Text must be readable**: at least 2.5vh tall, on a scrim or with a shadow over photos.
- **Stock**: show the candidates sheet and let the person pick by number. Keep `stock/credits.json`.
- **Never commit or upload** `.env`, `projects/`, or `models/`.
- When something fails, explain it in one plain sentence, then fix it.

## Speed

`render.py` uses up to 8 browsers at once. Measured on an M-series Mac (12 cores): a 35 s 1080p
stock promo took 16 s in all, a 34 s paper-cutout explainer 11 s. Slower laptops take 2 to 4 times
as long. `render-log.txt` in each project records real times. Use `--draft` while iterating.
