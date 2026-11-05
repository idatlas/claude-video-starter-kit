"""Cut a screen recording: keep the parts you want, speed up the slow parts, level the voice.

    python scripts/cut.py projects/tutorial --suggest   # find long pauses and print a 'keep' list
    python scripts/cut.py projects/tutorial             # apply project.json "keep" -> cut.mp4

In project.json:
    "source": "raw/recording.mov",
    "keep": [[0.8, 14.2], [16.0, 41.5], {"from": 41.5, "to": 70, "speed": 4}, [70, 95.3]]

A pair [from, to] keeps that stretch as it is. {"from", "to", "speed": 4} plays it 4x faster with
no sound (good for waiting on an install). Times are seconds in the original recording. No "keep"
means keep everything. After cutting, transcribe cut.mp4 again: the times have all moved.
"""
import argparse, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit

ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("--suggest", action="store_true")
ap.add_argument("--pause", type=float, default=1.2, help="with --suggest: pauses longer than this get cut")
a = ap.parse_args()
kit.need("ffmpeg")
pj = os.path.join(a.project, "project.json")
p = json.load(open(pj))
src = kit.path_in({"_dir": os.path.abspath(a.project)}, p["source"])
info = kit.probe(src)
D = info["duration"]

if a.suggest:
    if not info.get("audio"):
        sys.exit("This recording has no sound, so there are no pauses to find. Write 'keep' by hand.")
    r = subprocess.run(["ffmpeg", "-i", src, "-af", f"silencedetect=noise=-35dB:d={a.pause}", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    if len(ends) < len(starts):          # silence that runs to the end of the recording
        ends.append(D + 0.25)
    keep, t = [], 0.0
    for s, e in zip(starts, ends):
        if s > t:
            keep.append([round(t, 2), round(min(s + 0.25, D), 2)])
        t = max(e - 0.25, 0)
    if t < D:
        keep.append([round(t, 2), round(D, 2)])
    cut = D - sum(b - a_ for a_, b in keep)
    print(f"Recording: {D:.1f}s. {len(starts)} pauses over {a.pause}s; cutting them saves {cut:.1f}s.")
    print('"keep": ' + json.dumps(keep))
    print("Check before using it: something may be happening on screen during a quiet stretch (a click,"
          " a page loading). Look at a sheet of the recording and keep those parts, or speed them up.")
    sys.exit()

keep = p.get("keep") or [[0, D]]
parts, fc, n = [], [], 0
for k in keep:
    seg = {"from": k[0], "to": k[1]} if isinstance(k, list) else dict(k)
    sp = float(seg.get("speed", 1))
    fc.append(f"[0:v]trim={seg['from']}:{seg['to']},setpts=(PTS-STARTPTS)/{sp},fps={p.get('fps', 30)},"
              f"scale='min(2560,iw)':-2,format=yuv420p[v{n}]")
    length = (seg["to"] - seg["from"]) / sp
    if sp == 1 and info.get("audio") and not seg.get("mute"):
        fc.append(f"[0:a]atrim={seg['from']}:{seg['to']},asetpts=PTS-STARTPTS,aresample=48000[a{n}]")
    else:
        fc.append(f"anullsrc=r=48000:cl=mono,atrim=0:{length:.3f}[a{n}]")
    n += 1
fc.append("".join(f"[v{k}][a{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=1[v][a0]")
fc.append("[a0]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]")
out = os.path.join(a.project, "cut.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", out], check=True)
print(f"cut.mp4: {kit.probe(out)['duration']:.1f}s (from {D:.1f}s). Now transcribe it: python scripts/transcribe.py {out}")
