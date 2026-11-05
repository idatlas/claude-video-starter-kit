"""Hide private information in a screenshot before it goes in a course: blur it, or cover it
with believable fake text.

    python scripts/redact.py shot.png --find                       # list every line of text and where it is
    python scripts/redact.py shot.png --auto                       # also flag emails, keys and long numbers
    python scripts/redact.py shot.png --out clean.png \\
        --blur 0.70,0.02,0.18,0.04 \\
        --replace "0.12,0.30,0.20,0.03=Alex Rivera" \\
        --dots 0.25,0.45,0.40,0.04

Boxes are x,y,w,h as fractions of the image (0 to 1), the same as the tutorial template uses,
so a box found on a screenshot also works on a recording of the same screen.
  --blur     heavy blur, for things nobody needs to read (avatars, sidebars, other people's names)
  --replace  covers the text with the background color and writes fake text in a similar size
             ("x,y,w,h=**Fake Bold**" for bold text)
  --dots     covers the text and draws ●●●●●●●●, the way apps show a hidden key
Text finding uses macOS's built-in Vision (scripts/find_text.swift), so nothing leaves your Mac.
"""
import argparse, json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(os.path.dirname(HERE), "templates", "fonts", "Inter.ttf")
PRIVATE = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("key-like", re.compile(r"\b(sk|pk|xi|api|key)[-_]?[A-Za-z0-9]{12,}|\b[A-Za-z0-9]{28,}\b", re.I)),
    ("long number", re.compile(r"\b\d[\d -]{8,}\d\b")),
]


def find_text(path):
    r = subprocess.run(["swift", os.path.join(HERE, "find_text.swift"), path], capture_output=True, text=True)
    if r.returncode:
        sys.exit("Text finding needs macOS (swift). On Windows, give the boxes by hand.\n" + r.stderr[-300:])
    return json.loads(r.stdout)


def box(s, W, H):
    x, y, w, h = map(float, s.split(","))
    return int(x * W), int(y * H), int((x + w) * W), int((y + h) * H)


def bg_color(im, b):
    """The most common color in a thin ring just outside the box (the background behind the text)."""
    x0, y0, x1, y1 = b
    ring = []
    for xx in range(max(0, x0 - 4), min(im.width, x1 + 4), 2):
        for yy in (max(0, y0 - 3), min(im.height - 1, y1 + 2)):
            ring.append(im.getpixel((xx, yy))[:3])
    return max(set(ring), key=ring.count) if ring else (255, 255, 255)


def text_color(im, b, bg):
    """The pixel in the box that differs most from the background: the ink."""
    crop = im.crop(b).convert("RGB")
    px = [crop.getpixel((x, y)) for x in range(0, crop.width, 2) for y in range(0, crop.height, 2)]
    return max(px, key=lambda p: sum(abs(p[i] - bg[i]) for i in range(3)))


def cover(im, b, text, scale=0.9, pad=3):
    """Paint over box b (a little past its edges) and write text sized to the original's height."""
    bg = bg_color(im, (b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad))
    ink = text_color(im, b, bg)
    d = ImageDraw.Draw(im)
    d.rectangle((b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad), fill=bg)
    hgt = b[3] - b[1]
    size = max(8, int(hgt * scale))
    bold = text.startswith("**") and text.endswith("**")
    text = text.strip("*") if bold else text
    f = ImageFont.truetype(FONT, size)
    try:   # Inter is a variable font: set its weight axis
        axes = f.get_variation_axes()
        f.set_variation_by_axes([(700 if bold else 400) if str(a.get("name", "")).lower() in ("weight", "b'weight'") or a.get("minimum") == 100 else a.get("default", a["minimum"]) for a in axes])
    except Exception:
        pass
    top = f.getbbox("Hg")[1]
    d.text((b[0] + 1, b[1] + (hgt - (f.getbbox("Hg")[3] - top)) / 2 - top), text, fill=ink, font=f)


ap = argparse.ArgumentParser()
ap.add_argument("image")
ap.add_argument("--out")
ap.add_argument("--find", action="store_true")
ap.add_argument("--auto", action="store_true")
ap.add_argument("--blur", action="append", default=[])
ap.add_argument("--replace", action="append", default=[], help='"x,y,w,h=fake text"')
ap.add_argument("--dots", action="append", default=[])
a = ap.parse_args()

if a.find or a.auto:
    for t in find_text(a.image):
        flags = [n for n, rx in PRIVATE if rx.search(t["text"])] if a.auto else []
        mark = f"  <-- {', '.join(flags)}" if flags else ""
        print(f'{t["x"]:.3f},{t["y"]:.3f},{t["w"]:.3f},{t["h"]:.3f}  {t["text"]}{mark}')
    if not (a.blur or a.replace or a.dots):
        sys.exit()

im = Image.open(a.image).convert("RGB")
W, H = im.size
for s in a.blur:
    b = box(s, W, H)
    region = im.crop(b)
    r = max(6, (b[3] - b[1]) // 2)
    region = region.resize((max(1, region.width // 8), max(1, region.height // 8))).resize(region.size).filter(ImageFilter.GaussianBlur(r))
    im.paste(region, b)
for s in a.replace:
    spec, text = s.split("=", 1)
    cover(im, box(spec, W, H), text)
for s in a.dots:
    b = box(s, W, H)
    hgt = b[3] - b[1]
    cover(im, b, "●" * max(6, int((b[2] - b[0]) / max(1, hgt * 0.62))), scale=0.5)
out = a.out or os.path.splitext(a.image)[0] + "-clean.png"
im.save(out)
print(f"Saved {out}: {len(a.blur)} blurred, {len(a.replace)} replaced, {len(a.dots)} hidden as dots")
