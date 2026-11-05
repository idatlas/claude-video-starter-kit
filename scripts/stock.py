"""Find and download free stock video and photos from Pexels.

    python scripts/stock.py search projects/promo "person editing video on laptop" --type video
    python scripts/stock.py search projects/promo "notebook on desk morning light" --type photo --n 8
    python scripts/stock.py get projects/promo 3195394 --type video

'search' saves numbered thumbnails and one picture of them all (stock/candidates.png) so you and
Claude can pick by number. 'get' downloads the full file into stock/ and records the credit in
stock/credits.json. Pexels content is free to use; crediting the creator is appreciated.
"""
import argparse, json, os, sys
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit

kit.load_env()
KEY = os.environ.get("PEXELS_API_KEY")
if not KEY:
    sys.exit("No PEXELS_API_KEY in .env. Run scripts/keys.sh and paste it there.")
H = {"Authorization": KEY}

ap = argparse.ArgumentParser()
ap.add_argument("action", choices=["search", "get"])
ap.add_argument("project")
ap.add_argument("query")
ap.add_argument("--type", choices=["video", "photo"], default="video")
ap.add_argument("--n", type=int, default=8)
ap.add_argument("--orientation", default="landscape", help="landscape, portrait or square")
a = ap.parse_args()
stock = os.path.join(a.project, "stock")
os.makedirs(stock, exist_ok=True)


def api(path, **params):
    base = "https://api.pexels.com/videos/" if a.type == "video" else "https://api.pexels.com/v1/"
    r = requests.get(base + path, headers=H, params=params, timeout=30)
    if r.status_code == 401:
        sys.exit("Pexels refused the key. Check PEXELS_API_KEY in .env.")
    r.raise_for_status()
    return r.json()


def best_file(v, want_w=1920):
    files = [f for f in v["video_files"] if f.get("file_type") == "video/mp4" and f.get("width")]
    files.sort(key=lambda f: (abs(f["width"] - want_w), -f["width"]))
    return files[0]


if a.action == "search":
    j = api("search", query=a.query, per_page=a.n, orientation=a.orientation, **({"size": "medium"} if a.type == "video" else {}))
    items = j.get("videos" if a.type == "video" else "photos", [])
    if not items:
        sys.exit("No results. Try fewer, more concrete words (things you'd see, not ideas).")
    cdir = os.path.join(stock, "candidates")
    os.makedirs(cdir, exist_ok=True)
    rows, ims, labels = [], [], []
    for k, it in enumerate(items, 1):
        thumb = it["image"] if a.type == "video" else it["src"]["medium"]
        p = os.path.join(cdir, f"{k:02d}.jpg")
        open(p, "wb").write(requests.get(thumb, timeout=30).content)
        if a.type == "video":
            lab = f"#{k}  id {it['id']}  {it['duration']}s  {it['width']}x{it['height']}"
            who = it["user"]["name"]
        else:
            lab = f"#{k}  id {it['id']}  {it['width']}x{it['height']}"
            who = it["photographer"]
        rows.append({"n": k, "id": it["id"], "by": who, "url": it["url"], **({"duration": it["duration"]} if a.type == "video" else {})})
        ims.append(p); labels.append(lab)
    json.dump({"query": a.query, "type": a.type, "results": rows}, open(os.path.join(cdir, "results.json"), "w"), indent=1)
    out = kit.sheet(ims, labels, os.path.join(stock, "candidates.png"), cols=4, thumb_w=400)
    for r in rows:
        print(f"#{r['n']:<2} id {r['id']:<10} {str(r.get('duration', '')) + 's' if 'duration' in r else '':<5} by {r['by']}")
    print(f"Thumbnails: {out}")

else:
    it = api(f"videos/{a.query}" if a.type == "video" else f"photos/{a.query}")
    if a.type == "video":
        f = best_file(it)
        url, ext, who = f["link"], "mp4", it["user"]["name"]
        dims = f"{f['width']}x{f['height']}, {it['duration']}s"
    else:
        url, ext, who = it["src"]["original"], "jpg", it["photographer"]
        dims = f"{it['width']}x{it['height']}"
    path = os.path.join(stock, f"{a.type}-{it['id']}.{ext}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(path, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    cpath = os.path.join(stock, "credits.json")
    credits = json.load(open(cpath)) if os.path.exists(cpath) else []
    credits = [c for c in credits if c["file"] != os.path.basename(path)]
    credits.append({"file": os.path.basename(path), "by": who, "source": it["url"], "license": "Pexels License"})
    json.dump(credits, open(cpath, "w"), indent=1)
    print(f"Saved {path} ({dims}) by {who}")
