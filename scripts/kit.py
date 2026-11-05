"""Shared code for the starter kit: load a project, prepare its media, draw frames, encode.

You don't run this file. preview.py and render.py use it.

A project is a folder under projects/ with a project.json. The template named in project.json
is an HTML page that draws one frame for a given time when the kit calls window.render(t).
"""
import hashlib, json, math, os, shutil, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------- environment ----------

def load_env():
    """Read KEY=value lines from the kit's .env into os.environ (never printed)."""
    path = os.path.join(KIT, ".env")
    if not os.path.exists(path):
        return
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def need(cmd):
    if not shutil.which(cmd):
        sys.exit(f"'{cmd}' isn't installed. Run ./setup.sh, or ask Claude to run scripts/doctor.sh.")


def run(args, **kw):
    return subprocess.run(args, check=True, **kw)


def probe(path):
    """Duration (s), width, height, fps of a media file."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration:stream=codec_type,width,height,r_frame_rate",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    info = {"duration": float(j["format"].get("duration", 0))}
    for s in j.get("streams", []):
        if s.get("codec_type") == "video" and "width" in s:
            n, d = s["r_frame_rate"].split("/")
            info.update(width=s["width"], height=s["height"], fps=float(n) / float(d or 1))
        if s.get("codec_type") == "audio":
            info["audio"] = True
    return info


# ---------- captions ----------

SHORT = {"a", "an", "the", "it", "to", "of", "and", "or", "with", "your", "my", "in", "on", "for", "at", "is", "that", "this", "you", "we", "i"}


def phrases(words, max_words=6, max_chars=42, max_gap=0.45):
    """Group word timings into caption phrases.

    A phrase ends at sentence punctuation, at a pause longer than max_gap, or when it gets too
    long. Used both for the burned-in captions and the .srt/.vtt files, so they always match.
    """
    out, cur = [], []
    for k, w in enumerate(words):
        cur.append(w)
        text = " ".join(x["word"] for x in cur)
        nxt = words[k + 1] if k + 1 < len(words) else None
        end_sentence = w["word"].rstrip('"\'”’)').endswith((".", "?", "!", ":", ";"))
        comma = w["word"].endswith(",") and len(cur) >= 3
        gap = nxt is not None and nxt["start"] - w["end"] > max_gap
        too_long = len(cur) >= max_words or (nxt is not None and len(text) + 1 + len(nxt["word"]) > max_chars)
        if too_long and nxt is not None:
            # don't strand one or two words of a sentence on their own ("...describe / it?")
            rest = []
            for x in words[k + 1:k + 3]:
                rest.append(x["word"])
                if x["word"].rstrip('"\'”’)').endswith((".", "?", "!")):
                    break
            else:
                rest = None
            if rest and len(text) + 1 + len(" ".join(rest)) <= max_chars + 14:
                too_long = False
        if nxt is None or end_sentence or comma or gap or too_long:
            carry = []
            # a line shouldn't end on "it", "the", "a"...: move that word to the next line
            while too_long and not (end_sentence or comma or gap) and len(cur) > 2 and cur[-1]["word"].lower() in SHORT:
                carry.insert(0, cur.pop())
            out.append({"start": cur[0]["start"], "end": cur[-1]["end"],
                        "text": " ".join(x["word"] for x in cur), "words": cur})
            cur = carry
    # hold each phrase on screen until the next one starts (up to 0.7 s), so captions don't flicker
    for a, b in zip(out, out[1:]):
        a["hold"] = min(b["start"], a["end"] + 0.7)
    if out:
        out[-1]["hold"] = out[-1]["end"] + 0.7
    return out


# ---------- projects ----------

def load_project(pdir):
    pdir = os.path.abspath(pdir)
    pj = os.path.join(pdir, "project.json")
    if not os.path.exists(pj):
        sys.exit(f"No project.json in {pdir}")
    try:
        p = json.load(open(pj))
    except json.JSONDecodeError as e:
        sys.exit(f"project.json has a typo near line {e.lineno}: {e.msg}")
    p["_dir"] = pdir
    p.setdefault("fps", 30)
    p.setdefault("size", "1920x1080")
    tpl = p.get("template")
    comp = os.path.join(KIT, "templates", tpl or "", "comp.html")
    if not tpl or not os.path.exists(comp):
        names = sorted(d for d in os.listdir(os.path.join(KIT, "templates")) if os.path.exists(os.path.join(KIT, "templates", d, "comp.html")))
        sys.exit(f"project.json 'template' must be one of: {', '.join(names)}")
    p["_comp"] = comp
    return p


def path_in(p, rel):
    return rel if os.path.isabs(rel) else os.path.join(p["_dir"], rel)


def duration(p):
    """Length of the video: project 'duration', else the audio's length, else the last scene's end."""
    if isinstance(p.get("duration"), (int, float)):
        return float(p["duration"])
    if p.get("audio"):
        return probe(path_in(p, p["audio"]))["duration"] + float(p.get("tail", 0.6))
    if p.get("video"):
        return probe(path_in(p, p["video"]))["duration"]
    ends = [s["end"] for s in p.get("scenes", []) if "end" in s]
    if ends:
        return max(ends)
    sys.exit("Can't tell how long the video is: add \"duration\" (seconds) to project.json")


def _cache_key(*parts):
    return hashlib.md5(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:10]


def extract_frames(src, dest, fps, start=0.0, length=None, width=None):
    """Video file -> numbered JPGs (00001.jpg ...). Skipped if already done with the same settings."""
    key = _cache_key(os.path.abspath(src), os.path.getmtime(src), fps, start, length, width)
    stamp = os.path.join(dest, ".done")
    if os.path.exists(stamp) and open(stamp).read() == key:
        return len([f for f in os.listdir(dest) if f.endswith(".jpg")])
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    vf = f"fps={fps}" + (f",scale={width}:-2" if width else "")
    args = ["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", src]
    if length:
        args += ["-t", str(length)]
    run(args + ["-vf", vf, "-q:v", "2", os.path.join(dest, "%05d.jpg")])
    open(stamp, "w").write(key)
    return len([f for f in os.listdir(dest) if f.endswith(".jpg")])


def prepare(p):
    """Work out everything the template needs and return it as the page's window.DATA."""
    need("ffmpeg")
    data = {k: v for k, v in p.items() if not k.startswith("_")}
    data["base"] = "file://" + p["_dir"] + "/"
    data["kit"] = "file://" + KIT + "/"
    data["duration"] = duration(p)
    cache = os.path.join(p["_dir"], ".cache")
    fps = p["fps"]

    # the main video (screen recording) as an image sequence
    if p.get("video"):
        src = path_in(p, p["video"])
        n = extract_frames(src, os.path.join(cache, "video"), fps)
        data["videoFrames"] = {"dir": "file://" + os.path.join(cache, "video") + "/", "count": n}

    # video clips used inside scenes (stock footage)
    for k, s in enumerate(p.get("scenes", [])):
        if s.get("kind") == "video" and s.get("src"):
            src = path_in(p, s["src"])
            length = s["end"] - s["start"] + 1.0
            d = os.path.join(cache, f"scene{k:02d}")
            n = extract_frames(src, d, fps, start=float(s.get("in", 0)), length=length, width=1920)
            s["frames"] = {"dir": "file://" + d + "/", "count": n}

    # captions
    cap = p.get("captions", {})
    words_file = p.get("words")
    if words_file and cap.get("mode", "phrase") != "off":
        words = json.load(open(path_in(p, words_file)))
        data["phrases"] = phrases(words, cap.get("maxWords", 6), cap.get("maxChars", 42))
    return data


# ---------- drawing frames ----------

def _worker(args):
    comp, data_json, w, h, frames, fps, outdir, fmt = args
    from playwright.sync_api import sync_playwright
    done = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--allow-file-access-from-files", "--disable-web-security"])
        pg = b.new_page(viewport={"width": w, "height": h})
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.add_init_script(f"window.DATA={data_json};")
        pg.goto("file://" + comp)
        pg.evaluate("document.fonts.ready.then(()=>true)")
        pg.evaluate("async()=>{ if (window.READY) await window.READY; return true; }")
        if errors:
            raise RuntimeError("The template has an error: " + errors[0])
        for i in frames:
            t = i / fps
            pg.evaluate("async t=>{ await window.render(t); return true; }", t)
            if errors:
                raise RuntimeError(f"Template error at {t:.2f}s: {errors[0]}")
            path = os.path.join(outdir, f"{i:05d}.{fmt}")
            if fmt == "jpg":
                pg.screenshot(path=path, type="jpeg", quality=94)
            else:
                pg.screenshot(path=path)
            done += 1
        b.close()
    return done


def draw(p, data, frames, outdir, scale=1.0, workers=0, fmt="jpg"):
    """Draw the listed frame numbers into outdir. Returns seconds taken."""
    W, H = map(int, p["size"].lower().split("x"))
    w, h = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    os.makedirs(outdir, exist_ok=True)
    n = workers or min(8, os.cpu_count() or 2, max(1, len(frames) // 20))
    chunks = [frames[k::n] for k in range(n)]
    js = json.dumps(data)
    t0 = time.time()
    if n == 1:
        _worker((p["_comp"], js, w, h, frames, p["fps"], outdir, fmt))
    else:
        with ProcessPoolExecutor(n) as ex:
            list(ex.map(_worker, [(p["_comp"], js, w, h, c, p["fps"], outdir, fmt) for c in chunks]))
    return time.time() - t0, n


# ---------- sound and encode ----------

def encode(p, framedir, out, draft=False, start=0.0, length=None):
    """Numbered frames + voice/recording audio (+ optional music under it) -> mp4.

    start/length: encode only part of the video (the frames in framedir already start at `start`)."""
    fps = p["fps"]
    dur = length or duration(p)
    args = ["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", os.path.join(framedir, "%05d.jpg")]
    audio_src = p.get("audio") or (p.get("video") if p.get("video") else None)
    music = p.get("music")
    filters, amap = [], None
    k = 1
    if audio_src:
        args += ["-ss", str(start), "-i", path_in(p, audio_src)]
        filters.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={dur}[voice]")
        k += 1
    if music:
        m = music if isinstance(music, dict) else {"file": music}
        args += ["-stream_loop", "-1", "-ss", str(start), "-i", path_in(p, m["file"])]
        fade = float(m.get("fadeOut", 2.0))
        filters.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{dur},"
                       f"volume={m.get('db', -18)}dB,afade=t=in:d=0.5,afade=t=out:st={max(0, dur - fade)}:d={fade}[mus]")
        k += 1
    if audio_src and music:
        if p.get("music", {}).get("duck", True) if isinstance(music, dict) else True:
            filters.append("[voice]asplit[v1][v2];[mus][v2]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=500[md];"
                           "[v1][md]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]")
        else:
            filters.append("[voice][mus]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]")
        amap = "[a]"
    elif audio_src:
        amap = "[voice]"
    elif music:
        amap = "[mus]"
    if filters:
        args += ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", amap]
    else:
        args += ["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a"]
    crf, preset = ("26", "veryfast") if draft else ("18", "medium")
    args += ["-c:v", "libx264", "-crf", crf, "-preset", preset, "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", "-movflags", "+faststart", out]
    t0 = time.time()
    run(args)
    return time.time() - t0


# ---------- contact sheets ----------

def sheet(images, labels, out, cols=4, thumb_w=480):
    """Tile images into one labelled picture (the 'timeline preview')."""
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(x).convert("RGB") for x in images]
    tw = thumb_w
    th = int(ims[0].height * tw / ims[0].width)
    rows = math.ceil(len(ims) / cols)
    pad, lab = 12, 30
    S = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + lab + pad) + pad), (24, 24, 28))
    d = ImageDraw.Draw(S)
    try:
        font = ImageFont.truetype(os.path.join(KIT, "templates", "fonts", "Inter.ttf"), 20)
    except OSError:
        font = ImageFont.load_default()
    for k, (im, l) in enumerate(zip(ims, labels)):
        x = pad + (k % cols) * (tw + pad)
        y = pad + (k // cols) * (th + lab + pad)
        S.paste(im.resize((tw, th)), (x, y + lab))
        d.text((x + 2, y + 4), l, fill=(235, 235, 240), font=font)
    S.save(out)
    return out


def fmt_time(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"
