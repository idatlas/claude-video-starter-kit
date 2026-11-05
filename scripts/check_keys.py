"""Check that the API keys in .env work, without ever showing them.

    python scripts/check_keys.py
"""
import os, sys
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit

kit.load_env()
ok = True


def show(name, good, msg):
    global ok
    ok &= good
    print(f"{'OK  ' if good else 'FIX '} {name}: {msg}")


k = os.environ.get("PEXELS_API_KEY", "")
if not k or k.startswith("paste"):
    show("Pexels", False, "no key in .env yet")
else:
    r = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": k}, params={"query": "test", "per_page": 1}, timeout=20)
    show("Pexels", r.status_code == 200, "key works" if r.status_code == 200 else f"Pexels said {r.status_code}; copy the key again")

k = os.environ.get("ELEVENLABS_API_KEY", "")
if not k or k.startswith("paste"):
    show("ElevenLabs", False, "no key in .env yet")
else:
    r = requests.get("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": k}, timeout=20)
    if r.status_code == 200:
        s = r.json()
        left = s.get("character_limit", 0) - s.get("character_count", 0)
        show("ElevenLabs", True, f"key works; {s.get('tier', '?')} plan, about {left:,} credits left this month")
    else:
        r2 = requests.get("https://api.elevenlabs.io/v2/voices", headers={"xi-api-key": k}, params={"page_size": 1}, timeout=20)
        if r2.status_code == 200:
            show("ElevenLabs", True, "key works (it can't read your plan; that's fine)")
        else:
            show("ElevenLabs", False, f"ElevenLabs said {r.status_code}; check the key and its permissions (Text to Speech, Voices: Read)")

print("\nAll set." if ok else "\nFix the lines marked FIX, then run this again.")
