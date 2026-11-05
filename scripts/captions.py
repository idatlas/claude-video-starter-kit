"""Export captions as .srt and .vtt files (for YouTube, an LMS, or a video player's CC button).

    python scripts/captions.py projects/promo

Uses the same phrases as the burned-in captions, so they match exactly. Burned-in captions are
for viewers with the sound off; caption files are for accessibility and can be turned on or off.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit

p = kit.load_project(sys.argv[1])
if not p.get("words"):
    sys.exit("project.json has no \"words\" file. Make one with voiceover.py or transcribe.py.")
cap = p.get("captions", {})
ph = kit.phrases(json.load(open(kit.path_in(p, p["words"]))), cap.get("maxWords", 6), cap.get("maxChars", 42))


def ts(t, sep):
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h:02d}:{m:02d}:{t % 60:06.3f}".replace(".", sep)


srt = "\n".join(f"{k}\n{ts(x['start'], ',')} --> {ts(x['hold'], ',')}\n{x['text']}\n" for k, x in enumerate(ph, 1))
vtt = "WEBVTT\n\n" + "\n".join(f"{ts(x['start'], '.')} --> {ts(x['hold'], '.')}\n{x['text']}\n" for x in ph)
for ext, body in (("srt", srt), ("vtt", vtt)):
    open(os.path.join(p["_dir"], f"captions.{ext}"), "w").write(body)
print(f"{len(ph)} captions -> captions.srt and captions.vtt in {p['_dir']}")
