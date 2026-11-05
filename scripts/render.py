"""Render a project to an mp4.

    python scripts/render.py projects/promo            # final: full size, best quality
    python scripts/render.py projects/promo --draft    # half size, fast: for checking timing and sound
    python scripts/render.py projects/promo --from 10 --to 18   # just one stretch (seconds)

Writes projects/<name>/out.mp4 (or out-draft.mp4) and adds a line to render-log.txt with how long
each step took, so you learn what to expect on your own computer.
"""
import argparse, json, os, shutil, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--from", dest="t0", type=float, default=0)
    ap.add_argument("--to", dest="t1", type=float)
    ap.add_argument("--workers", type=int, default=0)
    a = ap.parse_args()

    T = time.time()
    p = kit.load_project(a.project)
    t_prep = time.time()
    data = kit.prepare(p)
    t_prep = time.time() - t_prep
    dur = data["duration"]
    fps = p["fps"]
    last = int(min(a.t1 or dur, dur) * fps)
    frames = list(range(int(a.t0 * fps), last))
    partial = a.t0 > 0 or a.t1 is not None
    name = "out-draft" if a.draft else "out"
    if partial:
        name += f"-{a.t0:g}-{a.t1 or dur:g}s"
    framedir = os.path.join(p["_dir"], ".cache", "frames-draft" if a.draft else "frames")
    shutil.rmtree(framedir, ignore_errors=True)

    print(f"Drawing {len(frames)} frames ({len(frames) / fps:.1f}s at {fps} fps, "
          f"{'half size draft' if a.draft else p['size']})...", flush=True)
    secs, workers = kit.draw(p, data, frames, framedir, scale=0.5 if a.draft else 1.0, workers=a.workers)
    print(f"  drawn in {secs:.1f}s with {workers} browsers ({len(frames) / max(secs, 0.01):.1f} frames/s)", flush=True)

    # frames must be numbered from 1 with no gaps for ffmpeg; renumber a partial render
    if partial:
        for k, i in enumerate(frames):
            os.rename(os.path.join(framedir, f"{i:05d}.jpg"), os.path.join(framedir, f"tmp{k:05d}.jpg"))
        for k in range(len(frames)):
            os.rename(os.path.join(framedir, f"tmp{k:05d}.jpg"), os.path.join(framedir, f"{k:05d}.jpg"))
    out = os.path.join(p["_dir"], name + ".mp4")
    enc = kit.encode(p, framedir, out, draft=a.draft, start=a.t0, length=len(frames) / fps)
    total = time.time() - T
    size = os.path.getsize(out) / 1e6
    print(f"  encoded in {enc:.1f}s")
    print(f"Done: {out}  ({len(frames) / fps:.1f}s of video, {size:.1f} MB, {total:.0f}s total)")
    with open(os.path.join(p["_dir"], "render-log.txt"), "a") as f:
        f.write(json.dumps({"when": time.strftime("%Y-%m-%d %H:%M"), "mode": "draft" if a.draft else "final",
                            "video_s": round(len(frames) / fps, 1), "size": p["size"], "prepare_s": round(t_prep, 1),
                            "draw_s": round(secs, 1), "browsers": workers, "encode_s": round(enc, 1),
                            "total_s": round(total, 1), "mb": round(size, 1)}) + "\n")


if __name__ == "__main__":   # needed: the parallel browsers re-import this file
    main()
