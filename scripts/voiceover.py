"""Turn a script into an ElevenLabs voiceover, with the time of every word (for captions).

    python scripts/voiceover.py projects/promo/script.txt                 # -> voice.mp3 + words.json beside it
    python scripts/voiceover.py projects/promo/script.txt --voice <id>
    python scripts/voiceover.py --voices                                  # list the voices on your account
    python scripts/voiceover.py --voices --search "warm british"          # narrow the list

The voice comes from --voice, else ELEVENLABS_VOICE_ID in .env, else the first voice on your account.
Each run costs ElevenLabs credits (about one per character on most models).
"""
import argparse, base64, json, os, sys
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit

kit.load_env()
KEY = os.environ.get("ELEVENLABS_API_KEY")
if not KEY:
    sys.exit("No ELEVENLABS_API_KEY in .env. Run scripts/keys.sh and paste it there.")
H = {"xi-api-key": KEY}
API = "https://api.elevenlabs.io"

ap = argparse.ArgumentParser()
ap.add_argument("script", nargs="?")
ap.add_argument("--voice")
ap.add_argument("--model", default=os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"))
ap.add_argument("--voices", action="store_true")
ap.add_argument("--search")
ap.add_argument("--stability", type=float, default=0.5)
ap.add_argument("--speed", type=float, default=1.0, help="0.7 to 1.2")
ap.add_argument("--out", help="mp3 path (default: voice.mp3 next to the script)")
a = ap.parse_args()


def voices():
    r = requests.get(f"{API}/v2/voices", headers=H, params={"page_size": 100, "search": a.search or ""}, timeout=30)
    if r.status_code == 401:
        sys.exit("ElevenLabs refused the key for listing voices. Give the key the 'Voices: Read' permission, or pass --voice.")
    r.raise_for_status()
    return r.json().get("voices", [])


if a.voices:
    for v in voices():
        lab = v.get("labels") or {}
        desc = ", ".join(x for x in [lab.get("gender"), lab.get("age"), lab.get("accent"), lab.get("descriptive") or lab.get("description"), lab.get("use_case") or lab.get("use case")] if x)
        print(f"{v['voice_id']}  {v['name']:<28} {desc}")
    sys.exit()

if not a.script:
    ap.error("give a script file, or --voices")
text = open(a.script).read().strip()
voice = a.voice or os.environ.get("ELEVENLABS_VOICE_ID") or voices()[0]["voice_id"]
r = requests.post(f"{API}/v1/text-to-speech/{voice}/with-timestamps", headers=H, timeout=300,
                  params={"output_format": "mp3_44100_128"},
                  json={"text": text, "model_id": a.model,
                        "voice_settings": {"stability": a.stability, "similarity_boost": 0.75, "speed": a.speed}})
if r.status_code != 200:
    sys.exit(f"ElevenLabs said {r.status_code}: {r.text[:300]}")
j = r.json()
out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.script)), "voice.mp3")
open(out, "wb").write(base64.b64decode(j["audio_base64"]))

# characters with times -> words with times
al = j.get("normalized_alignment") or j["alignment"]
chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
words, cur = [], None
for c, s, e in zip(chars, st, en):
    if c.isspace():
        if cur: words.append(cur); cur = None
        continue
    if cur is None:
        cur = {"word": c, "start": round(s, 3), "end": round(e, 3)}
    else:
        cur["word"] += c; cur["end"] = round(e, 3)
if cur: words.append(cur)
wpath = os.path.join(os.path.dirname(out), "words.json")
json.dump(words, open(wpath, "w"), indent=0)
dur = kit.probe(out)["duration"]
print(f"Voice: {out} ({dur:.1f}s, {len(text)} characters)\nWords: {wpath} ({len(words)} words)")
