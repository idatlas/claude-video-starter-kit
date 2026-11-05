"""Remove the background from images so they can be animated as cutouts.

    python scripts/cutout.py projects/explainer/art            # every .png/.jpg in the folder
    python scripts/cutout.py projects/explainer/art/sun.png

Writes <name>-cut.png (transparent background) next to each image and trims the empty edges.
Works best on art generated on a plain, flat background.

The background remover sometimes punches holes in an object where its inside looks like the
background (a light screen, a pale square). This script fills those holes back in: any see-through
patch that's enclosed by the object and isn't the background color is made solid again. Real holes,
like a palette's thumb hole, show the background color, so they stay open.
"""
import glob, os, sys
import numpy as np
from PIL import Image, ImageDraw
from rembg import remove, new_session

target = sys.argv[1]
files = [target] if os.path.isfile(target) else sorted(
    f for f in glob.glob(os.path.join(target, "*")) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and not f.endswith("-cut.png"))
if not files:
    sys.exit("No images found.")


def fill_holes(src, cut, tolerance=28):
    """Make enclosed see-through patches solid again unless they're the background color."""
    rgb = np.asarray(src.convert("RGB")).astype(int)
    a = np.asarray(cut)[..., 3].copy()
    h, w = a.shape
    # background color = median of a 10-px border around the original
    border = np.concatenate([rgb[:10].reshape(-1, 3), rgb[-10:].reshape(-1, 3), rgb[:, :10].reshape(-1, 3), rgb[:, -10:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    # see-through pixels reachable from the edge are the real outside (flood fill from a padded border)
    clear = a < 128
    m = Image.fromarray(np.pad(clear, 1, constant_values=True).astype(np.uint8) * 255, "L")
    ImageDraw.floodfill(m, (0, 0), 128)
    outside = (np.asarray(m) == 128)[1:-1, 1:-1]
    holes = clear & ~outside
    not_bg = np.abs(rgb - bg).sum(axis=2) > tolerance
    fix = holes & not_bg
    if fix.any():
        a[fix] = 255
        out = np.asarray(cut).copy()
        out[..., :3][fix] = rgb[fix]
        out[..., 3] = a
        return Image.fromarray(out, "RGBA"), int(fix.sum())
    return cut, 0


session = new_session("isnet-general-use")
for f in files:
    im = Image.open(f).convert("RGBA")
    cut = remove(im, session=session, post_process_mask=True)
    cut, fixed = fill_holes(im, cut)
    box = cut.getbbox()
    if box:
        pad = 8
        cut = cut.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(cut.width, box[2] + pad), min(cut.height, box[3] + pad)))
    out = os.path.splitext(f)[0] + "-cut.png"
    cut.save(out)
    note = f", filled {fixed:,} hole pixels" if fixed else ""
    print(f"{os.path.basename(f)} -> {os.path.basename(out)} ({cut.width}x{cut.height}{note})")
