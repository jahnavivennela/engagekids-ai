"""
image_gen.py — cached AI illustrations for worksheet themes.

DESIGN: images are generated ONCE per (theme, item_name) combo and saved to
disk + logged in SQLite. Every future worksheet reuses the same file instead
of calling the image API again — so cost is bounded by the size of your
theme library, not by how many worksheets/weeks/centres use the app.

Falls back to None (caller should fall back to the existing SVG/generic
shapes) if:
- no API key is configured
- the API call fails
- this is the first time seeing this theme/item and you haven't pre-generated it

TWO TIERS:
1. Fixed themes (yoga, animals, space, ...) — pre-generate the whole set
   once with build_theme_image_library().
2. ANY typed theme — get_or_generate_dynamic_theme() handles a theme the
   fixed library doesn't know about: it asks the LLM for a small set of
   item names for that theme, then generates+caches an image per item.
   Cached by the theme text itself, so a second request for the same
   theme (even weeks later, even a different centre) is instant — no
   repeat LLM call, no repeat image call.

SETUP NEEDED BEFORE THIS WORKS:
1. pip install openai --break-system-packages   (or your chosen provider's SDK)
2. Set an API key as an environment variable (e.g. OPENAI_API_KEY) — never
   hardcode it in the file.
3. Pick and fill in the actual API call in `_call_image_api()` below — left
   as a stub since the exact call depends on which provider/budget you choose.
"""

import os
import re
import json
import base64
import hashlib
from pathlib import Path

IMAGE_CACHE_DIR = Path(__file__).parent / "generated_images"
IMAGE_CACHE_DIR.mkdir(exist_ok=True)

DYNAMIC_THEME_CACHE_FILE = IMAGE_CACHE_DIR / "_dynamic_theme_items.json"


def _cache_key(theme_key: str, item_name: str) -> str:
    raw = f"{theme_key}:{item_name}".lower()
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _cache_path(theme_key: str, item_name: str) -> Path:
    return IMAGE_CACHE_DIR / f"{_cache_key(theme_key, item_name)}.png"


def get_theme_image_path(theme_key: str, item_name: str) -> str | None:
    """Returns a local file path to the cached illustration, or None if it
    doesn't exist yet (caller should fall back to the SVG version)."""
    path = _cache_path(theme_key, item_name)
    return str(path) if path.exists() else None


def image_path_to_data_uri(path: str) -> str:
    """Reads a cached PNG and returns a data: URI so it can be embedded
    directly in the worksheet's HTML (no separate file server needed —
    matches how the rest of the app produces one self-contained HTML string)."""
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _call_image_api(prompt: str) -> bytes:
    """Calls OpenAI's image API and returns raw PNG bytes.
    Requires OPENAI_API_KEY set in .streamlit/secrets.toml (same place
    GROQ_API_KEY already lives) — read it via streamlit's st.secrets when
    running inside the app, falling back to the OS environment variable for
    any one-off script runs (e.g. build_theme_image_library.py) outside
    Streamlit."""
    try:
        import streamlit as st
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in st.secrets or environment variables.")

    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    result = client.images.generate(
        model="gpt-image-1-mini",  # cheapest current tier — plenty for simple flat-illustration worksheet art
        prompt=prompt,
        size="1024x1024",
    )
    return base64.b64decode(result.data[0].b64_json)


def generate_and_cache_theme_image(theme_key: str, item_name: str, age_group: str = "3-5 years") -> str | None:
    """Generates ONE illustration for this theme+item combo and saves it to
    disk permanently. NOT called during normal worksheet generation for the
    FIXED themes (call it once ahead of time via build_theme_image_library) —
    but IS called live, the first time only, for dynamic/typed themes, since
    there's no way to pre-generate something you don't know a user will type."""
    path = _cache_path(theme_key, item_name)
    if path.exists():
        return str(path)

    prompt = (
        f"A simple, friendly, flat-illustration style children's book image of "
        f"a young child ({age_group}) doing or interacting with '{item_name}', "
        f"themed around '{theme_key}'. Bold outlines, bright but soft colors, "
        f"plain white background, centered, no text, no logos, suitable for a "
        f"printed early-childhood worksheet."
    )
    try:
        png_bytes = _call_image_api(prompt)
        path.write_bytes(png_bytes)
        return str(path)
    except Exception as e:
        print(f"[image_gen] failed for {theme_key}/{item_name}: {e}")
        return None


def build_theme_image_library(theme_library: dict, age_group: str = "3-5 years"):
    """Run this ONCE (e.g. a one-off script, not on every app start) to
    pre-generate every theme+item combo you currently have in THEME_LIBRARY.
    After this runs, get_theme_image_path() will find everything instantly —
    no live API calls during normal app use."""
    results = {}
    for theme_key, items in theme_library.items():
        for item_name in items:
            results[(theme_key, item_name)] = generate_and_cache_theme_image(theme_key, item_name, age_group)
    return results


def grow_theme_pool(client, theme_key: str, theme_display_name: str, existing_item_names: list, extra_count: int = 6, age_group: str = "3-5 years") -> list[str]:
    """Fixes the '4 items forever, same pictures on repeat' problem for a
    FIXED theme (yoga, animals, etc.) — the hardcoded THEME_LIBRARY entries
    were never meant to be the ceiling, just a free starting point before
    image generation existed. This asks the LLM for `extra_count` MORE item
    names for the theme (avoiding existing_item_names — pass in
    THEME_LIBRARY[theme_key].keys() from worksheet_generator.py), generates
    and caches a real image for each, and returns the new names.

    Run this once per theme you want more variety in — not on every
    worksheet generation — same one-time-cost-then-reuse-forever pattern as
    everything else in this file. After running it, add the returned names
    to THEME_LIBRARY[theme_key] (with any placeholder SVG, since
    get_visual_for_item will find the real cached image and use that
    instead) so pick_themed_items/pick_icons include them in rotation."""
    prompt = (
        f"List exactly {extra_count} simple, concrete objects, characters, or poses "
        f"that fit the theme '{theme_display_name}' and would work as a coloring-page "
        f"picture for a {age_group} early childhood worksheet. "
        f"Do NOT repeat any of these already-used ones: {', '.join(existing_item_names)}. "
        f"One per line, 1-3 words each, no numbering, no extra text."
    )
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
    )
    lines = resp.choices[0].message.content.strip().split("\n")
    new_names = [l.strip("-•* ").strip() for l in lines if l.strip()]
    new_names = [n for n in new_names if n.lower() not in {e.lower() for e in existing_item_names}][:extra_count]

    for name in new_names:
        generate_and_cache_theme_image(theme_key, name, age_group)  # cached — safe, one-time cost per name
    return new_names


# ---------------------------------------------------------------------------
# DYNAMIC (any typed theme) support
# ---------------------------------------------------------------------------

def _normalize_theme_text(theme_text: str) -> str:
    return re.sub(r"\s+", " ", theme_text.strip().lower())


def _load_dynamic_theme_cache() -> dict:
    if DYNAMIC_THEME_CACHE_FILE.exists():
        return json.loads(DYNAMIC_THEME_CACHE_FILE.read_text())
    return {}


def _save_dynamic_theme_cache(cache: dict):
    DYNAMIC_THEME_CACHE_FILE.write_text(json.dumps(cache, indent=2))


def _suggest_theme_items(client, theme_text: str, age_group: str, n: int = 5) -> list[str]:
    """Asks the LLM (same Groq client used elsewhere in the app) for a short
    list of concrete, drawable item names for a theme it doesn't have a fixed
    library for. Kept deliberately small (n) since each name becomes one
    generated+cached image."""
    prompt = (
        f"List exactly {n} simple, concrete, single objects or characters "
        f"that fit the theme '{theme_text}' and would work as a coloring-page "
        f"picture for a {age_group} early childhood worksheet. "
        f"One per line, 1-3 words each, no numbering, no extra text."
    )
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
    )
    lines = resp.choices[0].message.content.strip().split("\n")
    items = [l.strip("-•* ").strip() for l in lines if l.strip()]
    return items[:n]


def get_or_generate_dynamic_theme(client, theme_text: str, age_group: str, n: int = 5) -> list[tuple[str, str | None]]:
    """Main entry point for a typed theme that isn't in the fixed
    THEME_LIBRARY. Returns a list of (item_name, image_path_or_None).

    Caches the ITEM NAMES per normalized theme text in a small JSON file
    (so 'construction', 'Construction ', 'CONSTRUCTION' all hit the same
    cache) and caches each IMAGE the same way the fixed themes do — so the
    very first person who ever types a given theme pays the (one-time)
    generation cost, and every request after that, for anyone, is instant."""
    norm = _normalize_theme_text(theme_text)
    cache = _load_dynamic_theme_cache()

    if norm in cache:
        item_names = cache[norm]
    else:
        item_names = _suggest_theme_items(client, theme_text, age_group, n=n)
        cache[norm] = item_names
        _save_dynamic_theme_cache(cache)

    results = []
    for name in item_names:
        path = generate_and_cache_theme_image(norm, name, age_group)  # cached by (norm, name) — safe to call every time
        results.append((name, path))
    return results


if __name__ == "__main__":
    # Example one-off run — uncomment once _call_image_api is wired up:
    # from worksheet_generator import THEME_LIBRARY
    # build_theme_image_library(THEME_LIBRARY)
    print("Fill in _call_image_api(), then run build_theme_image_library() once to pre-generate the fixed set.")