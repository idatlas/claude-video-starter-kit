"""Show the edit before rendering it: a few frames tiled into one picture with their times.

    python scripts/preview.py projects/promo                 # 8 frames spread across the video
    python scripts/preview.py projects/promo --count 12
    python scripts/preview.py projects/promo --at 0.5,3,7.25 # exact moments (seconds)
    python scripts/preview.py --video projects/promo/out.mp4 --every 2   # sheet of a finished video
    python scripts/preview.py projects/tutorial --at 3 --grid   # grid to read zoom/note positions off

Writes projects/<name>/preview.png (the sheet) and preview/ (each frame at full size).
Claude reads preview.png and shows it to you; give notes by the times printed on each frame.
"""
import argparse, os, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?")
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--at", help="comma-separated times in seconds")
    ap.add_argument("--video", help="make a sheet from a finished video instead")
    ap.add_argument("--every", type=float, default=2.0, help="with --video: seconds between frames")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--grid", action="store_true", help="tutorial template: draw a 0-1 grid over the recording")
    a = ap.parse_args()

    if a.video:
        kit.need("ffmpeg")
        info = kit.probe(a.video)
        tmp = tempfile.mkdtemp()
        # grab the frame at each exact time, so every label is the true time of its picture
        times, t = [], 0.0
        while t < info["duration"] - 0.05:
            times.append(round(t, 3)); t += a.every
        ims, labels = [], []
        for k, t in enumerate(times):
            path = os.path.join(tmp, f"{k:04d}.jpg")
            subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", a.video, "-frames:v", "1",
                            "-vf", "scale=640:-2", path], check=True)
            if os.path.exists(path):
                ims.append(path); labels.append(kit.fmt_time(t))
        out = os.path.splitext(a.video)[0] + "-sheet.png"
        kit.sheet(ims, labels, out, cols=a.cols)
        shutil.rmtree(tmp)
        print(f"{len(ims)} frames, every {a.every}s, of a {info['duration']:.1f}s video -> {out}")
        return

    if not a.project:
        ap.error("give a project folder, or --video")
    p = kit.load_project(a.project)
    data = kit.prepare(p)
    if a.grid:
        data["grid"] = True
    dur = data["duration"]
    fps = p["fps"]
    if a.at:
        times = [float(x) for x in a.at.split(",")]
    else:
        n = a.count
        times = [round(dur * (k + 0.5) / n, 2) for k in range(n)]
    frames = sorted({min(int(round(t * fps)), int(dur * fps) - 1) for t in times})
    out = os.path.join(p["_dir"], "preview")
    shutil.rmtree(out, ignore_errors=True)
    secs, _ = kit.draw(p, data, frames, out, scale=1.0, workers=1)
    ims = [os.path.join(out, f"{i:05d}.jpg") for i in frames]
    labels = [f"{kit.fmt_time(i / fps)}   (frame {i})" for i in frames]
    sheet = kit.sheet(ims, labels, os.path.join(p["_dir"], "preview.png"), cols=a.cols)
    print(f"Preview: {len(frames)} frames of a {dur:.1f}s video in {secs:.1f}s -> {sheet}")


if __name__ == "__main__":   # needed: the parallel browsers re-import this file
    main()
