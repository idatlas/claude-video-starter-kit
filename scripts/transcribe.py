"""Find the time of every spoken word in a recording, for captions and cuts. Runs on your Mac.

    python scripts/transcribe.py projects/tutorial/cut.mp4
    python scripts/transcribe.py projects/tutorial/cut.mp4 --words "Claude, ElevenLabs, Pexels, .env"

Writes words.json and transcript.txt next to the recording. --words gives Whisper the spelling of
names it doesn't know, which fixes most caption mistakes.
"""
import argparse, json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit

ap = argparse.ArgumentParser()
ap.add_argument("media")
ap.add_argument("--words", default="", help="names and terms to spell right")
ap.add_argument("--lang", default="en")
a = ap.parse_args()
kit.need("ffmpeg"); kit.need("whisper-cli")
model = os.environ.get("WHISPER_MODEL") or os.path.join(kit.KIT, "models", "ggml-small.en.bin")
if not os.path.exists(model):
    sys.exit(f"No Whisper model at {model}. Run ./setup.sh (it downloads one).")
if a.lang != "en" and model.endswith(".en.bin"):
    sys.exit("This model only knows English. Download a multilingual one (see README) and set WHISPER_MODEL.")

tmp = tempfile.mkdtemp()
wav = os.path.join(tmp, "a.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.media, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
args = ["whisper-cli", "-m", model, "-f", wav, "-l", a.lang, "-ojf", "-of", os.path.join(tmp, "w"), "-np"]
if a.words:
    args += ["--prompt", f"Glossary: {a.words}."]
subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
j = json.load(open(os.path.join(tmp, "w.json"), errors="replace"))

# whisper gives sub-word tokens; join them into words (a token starting with a space starts a word)
words = []
for seg in j["transcription"]:
    for tok in seg.get("tokens", []):
        txt = tok["text"]
        if txt.startswith("[_") or txt.startswith("<|") or not txt.strip():
            continue
        s, e = tok["offsets"]["from"] / 1000, tok["offsets"]["to"] / 1000
        if txt.startswith(" ") or not words:
            words.append({"word": txt.strip(), "start": s, "end": e})
        else:
            words[-1]["word"] += txt
            words[-1]["end"] = e
words = [w for w in words if w["word"]]
base = os.path.dirname(os.path.abspath(a.media))
json.dump(words, open(os.path.join(base, "words.json"), "w"), indent=0)
open(os.path.join(base, "transcript.txt"), "w").write(" ".join(w["word"] for w in words) + "\n")
print(f"{len(words)} words -> {os.path.join(base, 'words.json')}")
print(" ".join(w["word"] for w in words)[:400] + ("..." if len(words) > 60 else ""))
