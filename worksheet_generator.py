"""
worksheet_generator.py

Weekly worksheet generator for EngageKids AI — VISUAL worksheets, built to
match developmental milestones per the EYLF Practice Based Resources
(Developmental Milestones and the EYLF/NQS).

Key age-appropriateness rules baked in here (from that reference):
- Babies 0-1: no purposeful pencil grip yet (reflexive grasp only). These
  aren't "worksheets" a baby completes — they're high-contrast visual cards
  and sensory prompt cards FOR THE EDUCATOR to use with the baby.
- Toddlers 1-3: can scribble in loose circles/lines (fine, big coloring
  works) and can POINT to named objects/body parts, but can't draw a
  controlled line between two points and don't recognize written numbers/
  letters yet. So: big coloring, point-and-match (not draw-a-line),
  pointing games. No dot-to-dot, no letter tracing, no "write the number".
- Preschool 3-5: milestones show recognition is ahead of writing at this
  age (4-5 year olds are only just starting to copy/write some letters and
  numbers). So tracing (copying a printed guide) is fine, "write the number
  from memory" is not — that becomes circle-the-correct-number instead.
  Line-matching (body parts, dot-to-dot) fits since pencil control and
  scissor use are developing in this range.

Every worksheet body is built directly in code as SVG/HTML — never written
as prose by the AI. The AI (Groq) is only ever asked for a short title, and
if that call fails for any reason, a deterministic title is used instead.
"""

import datetime
import random
import streamlit as st

from milestones_data import AGE_BANDS
from worksheet_db import (
    init_worksheet_tables,
    save_worksheet,
    get_worksheets_for_week,
    get_recent_titles,
    save_feedback,
    get_latest_feedback,
    get_worksheet_history,
)

# ---------------------------------------------------------------------------
# Age-appropriate category pools
# ---------------------------------------------------------------------------

AGE_CATEGORIES = {
    # Gated to what the milestones doc says is realistic per band.
    # 0-1: no purposeful pencil grip -> visual/sensory prompt cards only.
    "0-1 years": [
        "Visual Tracking Card",
        "Sensory Play Prompt (for educator)",
    ],
    # 1-2: scribbles with pencil/crayon held in FIST; points to body parts in a game.
    "1-2 years": [
        "Big Scribble & Coloring",
        "Point & Match Shapes",
        "Body Parts Pointing Game",
        "Sensory Play Prompt (for educator)",
    ],
    # 2-3: holds crayon with FINGERS, draws circles/lines; begins to count;
    # recognises similarities/differences -> same/different becomes feasible.
    "2-3 years": [
        "Big Scribble & Coloring",
        "Point & Match Shapes",
        "Body Parts Pointing Game",
        "Count Together",
        "Shape Matching (Same/Different)",
    ],
    # 3-4 (from the combined 3-5 source): pencil held between thumb + 2 fingers,
    # imitates shapes e.g. circles, cuts with scissors -> fine motor control
    # improving, but writing/letter tracing and dot-to-dot held back to 4-5.
    "3-4 years": [
        "Coloring Page",
        "Shape Matching (Same/Different)",
        "Shapes & Patterns",
        "Odd One Out",
        "Body Parts Matching",
        "Sensory Play Prompt (for educator)",
    ],
    # 4-5 (same combined 3-5 source): "may write some numbers and letters",
    # "copies letters", "counts five to ten things" -> full set including
    # tracing and dot-to-dot.
    "4-5 years": [
        "Letter Tracing",
        "Numeracy - Count & Circle",
        "Coloring Page",
        "Shape Matching (Same/Different)",
        "Shapes & Patterns",
        "Odd One Out",
        "Dot to Dot",
        "Body Parts Matching",
    ],
}

# ---------------------------------------------------------------------------
# Shape + color building blocks
# ---------------------------------------------------------------------------

COLORS = ["#FF6B6B", "#4D96FF", "#FFD93D", "#6BCB77", "#B983FF", "#FF9F45", "#3DDBD9"]
SIMPLE_SHAPES = ["circle", "square", "triangle", "star", "heart"]  # toddler-safe: bold, few sides
ALL_SHAPES = ["circle", "square", "triangle", "rectangle", "star", "hexagon", "heart"]

SHAPE_PATHS = {
    "circle": '<circle cx="60" cy="60" r="50" fill="{c}" stroke="#333" stroke-width="5"/>',
    "square": '<rect x="15" y="15" width="90" height="90" fill="{c}" stroke="#333" stroke-width="5"/>',
    "triangle": '<polygon points="60,10 112,108 8,108" fill="{c}" stroke="#333" stroke-width="5" stroke-linejoin="round"/>',
    "rectangle": '<rect x="8" y="30" width="104" height="60" fill="{c}" stroke="#333" stroke-width="5"/>',
    "star": '<polygon points="60,5 73,43 115,43 81,66 93,105 60,82 27,105 39,66 5,43 47,43" fill="{c}" stroke="#333" stroke-width="5" stroke-linejoin="round"/>',
    "hexagon": '<polygon points="30,10 90,10 115,60 90,110 30,110 5,60" fill="{c}" stroke="#333" stroke-width="5" stroke-linejoin="round"/>',
    "heart": '<path d="M60 105 C10 65,10 25,40 15 C55 10,60 30,60 35 C60 30,65 10,80 15 C110 25,110 65,60 105 Z" fill="{c}" stroke="#333" stroke-width="5"/>',
}

OUTLINE_EXTRAS = {
    "flower": '<circle cx="60" cy="60" r="16" fill="none" stroke="#333" stroke-width="5"/><circle cx="60" cy="30" r="20" fill="none" stroke="#333" stroke-width="5"/><circle cx="60" cy="90" r="20" fill="none" stroke="#333" stroke-width="5"/><circle cx="30" cy="60" r="20" fill="none" stroke="#333" stroke-width="5"/><circle cx="90" cy="60" r="20" fill="none" stroke="#333" stroke-width="5"/>',
    "butterfly": '<path d="M60 25 C35 5,10 25,18 55 C25 85,50 78,60 60 C70 78,95 85,102 55 C110 25,85 5,60 25 Z" fill="none" stroke="#333" stroke-width="5"/><line x1="60" y1="25" x2="60" y2="105" stroke="#333" stroke-width="5"/>',
    "tree": '<rect x="52" y="80" width="16" height="35" fill="none" stroke="#333" stroke-width="5"/><circle cx="60" cy="50" r="42" fill="none" stroke="#333" stroke-width="5"/>',
}

LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

DOT_SHAPES = {
    "star": [(150, 10), (180, 90), (270, 90), (200, 140), (225, 220), (150, 175), (75, 220), (100, 140), (30, 90), (120, 90)],
    "house": [(150, 20), (260, 100), (230, 100), (230, 230), (70, 230), (70, 100), (40, 100)],
    "fish": [(30, 130), (90, 90), (160, 90), (220, 60), (270, 130), (220, 200), (160, 170), (90, 170)],
}

BODY_PARTS = [
    ("Eyes", (60, 38)),
    ("Ears", (28, 45)),
    ("Nose", (60, 52)),
    ("Hands", (0, 140)),
    ("Feet", (40, 230)),
]

SENSORY_ITEMS = [
    ("Grass / leaves", "Outdoor texture — crunchy, prickly"),
    ("Dry rice or pasta", "Pour, scoop, listen to the sound"),
    ("Play dough", "Squeeze, roll, poke"),
    ("Cotton wool / wool", "Soft, fluffy texture"),
    ("Smooth stones", "Cool, heavy, smooth"),
    ("Water play", "Splash, pour between containers"),
    ("Bubble wrap", "Pop, press, texture under fingers"),
    ("Sand", "Dig, sift through fingers"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def shape_svg(name, color, size=90):
    path = SHAPE_PATHS.get(name, SHAPE_PATHS["circle"]).format(c=color)
    return f'<svg viewBox="0 0 120 120" width="{size}" height="{size}">{path}</svg>'


def pick_shapes(avoid_titles, n, pool):
    avoid_text = " ".join(avoid_titles).lower()
    choices = [s for s in pool if s not in avoid_text] or pool
    random.shuffle(choices)
    return (choices * ((n // len(choices)) + 1))[:n]


def difficulty_from_feedback(feedback_text: str) -> str:
    if not feedback_text:
        return "medium"
    t = feedback_text.lower()
    if "too easy" in t or "harder" in t or "more difficult" in t or "more challenging" in t:
        return "hard"
    if "too hard" in t or "too difficult" in t or "easier" in t or "simplify" in t:
        return "easy"
    return "medium"


# ---------------------------------------------------------------------------
# Renderers — every function takes (avoid_titles, difficulty, age_group)
# ---------------------------------------------------------------------------

def render_visual_tracking(avoid_titles, difficulty, age_group):
    """Babies: bold black/white/red bullseye pattern — classic newborn visual
    stimulation, NOT a task for the baby to complete."""
    rings = ""
    ring_colors = ["#000000", "#FFFFFF", "#000000", "#FF0000", "#FFFFFF"]
    for i, c in enumerate(ring_colors):
        r = 100 - i * 18
        rings += f'<circle cx="150" cy="150" r="{r}" fill="{c}" stroke="#000" stroke-width="2"/>'
    svg = f'<svg viewBox="0 0 300 300" width="280" height="280">{rings}</svg>'
    instructions = "For the educator: hold this card 20–30cm from the baby's face and slowly move it side to side. High-contrast patterns support early visual tracking."
    return instructions, f'<div class="coloring-box">{svg}</div>'


def render_sensory_prompt(avoid_titles, difficulty, age_group):
    """Not a worksheet — a reference card of sensory materials to offer.
    Sensory exploration itself can't happen on paper, so this stays an
    educator prompt card rather than a fill-in task."""
    avoid_text = " ".join(avoid_titles).lower()
    choices = [s for s in SENSORY_ITEMS if s[0].lower() not in avoid_text] or SENSORY_ITEMS
    picks = random.sample(choices, min(4, len(choices)))
    rows = "".join(
        f'<div class="sensory-row"><div class="sensory-dot" style="background:{COLORS[i % len(COLORS)]}"></div>'
        f'<div><b>{name}</b><br><span class="sensory-note">{note}</span></div></div>'
        for i, (name, note) in enumerate(picks)
    )
    instructions = "For the educator: offer one item at a time and observe/note the child's reaction and exploration."
    return instructions, f'<div class="sensory-list">{rows}</div>'


def render_coloring(avoid_titles, difficulty, age_group):
    if age_group in ("0-1 years", "1-2 years", "2-3 years"):
        pool = {k: SHAPE_PATHS[k].format(c="none") for k in SIMPLE_SHAPES}
    else:
        pool = {**{k: SHAPE_PATHS[k].format(c="none") for k in ALL_SHAPES}, **OUTLINE_EXTRAS}
    avoid_text = " ".join(avoid_titles).lower()
    choices = [k for k in pool if k not in avoid_text] or list(pool.keys())
    name = random.choice(choices)
    big = f'<svg viewBox="0 0 120 120" width="320" height="320">{pool[name]}</svg>'
    instructions = "Color me in! Use as many colors as you like."
    return instructions, f'<div class="coloring-box">{big}</div>'


def render_point_match(avoid_titles, difficulty, age_group):
    """Toddlers: point to the matching shape — no line-drawing required."""
    rows = 2 if difficulty == "easy" else 3
    shapes = pick_shapes(avoid_titles, rows, SIMPLE_SHAPES)
    row_html = ""
    for shape in shapes:
        color = random.choice(COLORS)
        options = [color, color, random.choice([c for c in COLORS if c != color])]
        random.shuffle(options)
        cells = "".join(f'<div class="cell">{shape_svg(shape, c, size=100)}</div>' for c in options)
        row_html += f'<div class="match-row big-row">{cells}</div>'
    instructions = "Point to the two shapes in each row that are the SAME color."
    return instructions, f'<div class="grid">{row_html}</div>'


def render_shape_match(avoid_titles, difficulty, age_group):
    """Preschool: circle SAME or DIFFERENT — a mark-making task, appropriate
    once pencil grip is developing."""
    rows = {"easy": 3, "medium": 4, "hard": 5}[difficulty]
    shapes = pick_shapes(avoid_titles, rows, ALL_SHAPES)
    row_html = ""
    for shape in shapes:
        color_a = random.choice(COLORS)
        color_b = color_a if random.random() > 0.5 else random.choice([c for c in COLORS if c != color_a])
        cells = f'<div class="cell">{shape_svg(shape, color_a)}</div><div class="cell">{shape_svg(shape, color_b)}</div>'
        row_html += f'<div class="match-row">{cells}<div class="answer-circle">SAME&nbsp;&nbsp;&nbsp;DIFFERENT</div></div>'
    instructions = "Look at each pair. Circle SAME if they match, or DIFFERENT if they don't."
    return instructions, f'<div class="grid">{row_html}</div>'


def render_count_together(avoid_titles, difficulty, age_group):
    """Toddlers: a verbal/pointing counting activity, not a writing task."""
    rows = 3
    shapes = pick_shapes(avoid_titles, rows, SIMPLE_SHAPES)
    row_html = ""
    for shape in shapes:
        count = random.randint(1, 3)
        color = random.choice(COLORS)
        icons = "".join(shape_svg(shape, color, size=55) for _ in range(count))
        row_html += f'<div class="count-row"><div class="icons">{icons}</div></div>'
    instructions = "For the educator: count out loud together with the child, pointing to each shape as you count."
    return instructions, f'<div class="grid">{row_html}</div>'


def render_counting_circle(avoid_titles, difficulty, age_group):
    """Preschool: circle the correct number rather than write it from memory."""
    max_count = {"easy": 5, "medium": 8, "hard": 10}[difficulty]
    rows = 4
    shapes = pick_shapes(avoid_titles, rows, ALL_SHAPES)
    row_html = ""
    for shape in shapes:
        count = random.randint(2, max_count)
        color = random.choice(COLORS)
        icons = "".join(shape_svg(shape, color, size=42) for _ in range(count))
        distractors = sorted({count, max(1, count - 1), min(max_count + 2, count + 2)})
        while len(distractors) < 3:
            distractors.add(random.randint(1, max_count + 2))
        options = sorted(distractors)
        options_html = "".join(f'<div class="number-bubble">{n}</div>' for n in options)
        row_html += f'<div class="count-row"><div class="icons">{icons}</div><div class="number-options">{options_html}</div></div>'
    instructions = "Count the shapes in each row, then circle the correct number."
    return instructions, f'<div class="grid">{row_html}</div>'


def render_pattern_complete(avoid_titles, difficulty, age_group):
    length = {"easy": 4, "medium": 6, "hard": 8}[difficulty]
    shape_a, shape_b = pick_shapes(avoid_titles, 2, ALL_SHAPES)
    color_a, color_b = random.sample(COLORS, 2)
    sequence = [(shape_a, color_a) if i % 2 == 0 else (shape_b, color_b) for i in range(length)]
    icons = "".join(shape_svg(s, c, size=70) for s, c in sequence)
    blank = '<div class="blank-box">?</div>'
    instructions = "What comes next? Draw and color the missing shape in the empty box."
    return instructions, f'<div class="pattern-row">{icons}{blank}</div>'


def render_odd_one_out(avoid_titles, difficulty, age_group):
    rows = {"easy": 2, "medium": 3, "hard": 4}[difficulty]
    shapes = pick_shapes(avoid_titles, rows, ALL_SHAPES)
    row_html = ""
    for shape in shapes:
        base_color = random.choice(COLORS)
        odd_color = random.choice([c for c in COLORS if c != base_color])
        positions = [base_color] * 4
        positions[random.randint(0, 3)] = odd_color
        icons = "".join(f'<div class="cell">{shape_svg(shape, c)}</div>' for c in positions)
        row_html += f'<div class="match-row">{icons}</div>'
    instructions = "Circle the shape in each row that is different from the others."
    return instructions, f'<div class="grid">{row_html}</div>'


def render_tracing_letters(avoid_titles, difficulty, age_group):
    reps = {"easy": 2, "medium": 3, "hard": 4}[difficulty]
    avoid_text = " ".join(avoid_titles).upper()
    choices = [l for l in LETTERS if l not in avoid_text] or LETTERS
    letters = random.sample(choices, min(3, len(choices)))
    row_html = "".join(
        f'<div class="trace-row">{"".join(f"<span class=\'trace-letter\'>{letter}</span>" for _ in range(reps))}</div>'
        for letter in letters
    )
    instructions = "Trace over each letter with your finger, then with a pencil or crayon."
    return instructions, f'<div class="grid">{row_html}</div>'


def render_dot_to_dot(avoid_titles, difficulty, age_group):
    avoid_text = " ".join(avoid_titles).lower()
    choices = [k for k in DOT_SHAPES if k not in avoid_text] or list(DOT_SHAPES.keys())
    name = random.choice(choices)
    points = DOT_SHAPES[name]
    if difficulty == "easy":
        points = points[:max(4, len(points) // 2)]
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="6" fill="#333"/><text x="{x+10}" y="{y+5}" font-size="16" font-weight="bold" fill="#333">{i}</text>'
        for i, (x, y) in enumerate(points, start=1)
    )
    svg = f'<svg viewBox="0 0 300 260" width="320" height="280">{dots}</svg>'
    instructions = "Join the dots in order from 1 to the end to reveal a picture, then color it in!"
    return instructions, f'<div class="coloring-box">{svg}</div>'


def _body_figure_svg(dot_color_by_part, show_numbers):
    dots = ""
    for i, (name, (x, y)) in enumerate(BODY_PARTS, start=1):
        color = dot_color_by_part[name]
        label = str(i) if show_numbers else ""
        dots += f'<circle cx="{x+90}" cy="{y}" r="10" fill="{color}" stroke="#333" stroke-width="2"/>'
        if label:
            dots += f'<text x="{x+90}" y="{y+5}" font-size="12" font-weight="bold" text-anchor="middle" fill="#fff">{label}</text>'
    figure = """
    <circle cx="150" cy="40" r="30" fill="#FFE0B2" stroke="#333" stroke-width="4"/>
    <rect x="120" y="70" width="60" height="90" rx="20" fill="#FFE0B2" stroke="#333" stroke-width="4"/>
    <line x1="120" y1="90" x2="90" y2="140" stroke="#FFE0B2" stroke-width="14" stroke-linecap="round"/>
    <line x1="180" y1="90" x2="210" y2="140" stroke="#FFE0B2" stroke-width="14" stroke-linecap="round"/>
    <line x1="135" y1="160" x2="130" y2="230" stroke="#FFE0B2" stroke-width="16" stroke-linecap="round"/>
    <line x1="165" y1="160" x2="170" y2="230" stroke="#FFE0B2" stroke-width="16" stroke-linecap="round"/>
    """
    return f'<svg viewBox="0 0 300 260" width="260" height="230">{figure}{dots}</svg>'


def render_body_parts(avoid_titles, difficulty, age_group):
    is_preschool = age_group in ("3-4 years", "4-5 years")
    colors = random.sample(COLORS, len(BODY_PARTS))
    dot_color_by_part = {name: colors[i] for i, (name, _) in enumerate(BODY_PARTS)}
    figure_svg = _body_figure_svg(dot_color_by_part, show_numbers=is_preschool)

    if is_preschool:
        legend_rows = "".join(
            f'<div class="legend-row"><div class="legend-num">{i}</div><span>{name}</span></div>'
            for i, (name, _) in enumerate(BODY_PARTS, start=1)
        )
        instructions = "Draw a line from each body part name to the matching number on the picture."
    else:
        legend_rows = "".join(
            f'<div class="legend-row"><div class="legend-dot" style="background:{dot_color_by_part[name]}"></div><span>{name}</span></div>'
            for name, _ in BODY_PARTS
        )
        instructions = "For the educator: point to each colored dot on the picture and ask the child to point to that part on themselves — 'Where are YOUR eyes?'"

    body = f'<div class="body-parts-layout"><div>{figure_svg}</div><div class="legend">{legend_rows}</div></div>'
    return instructions, body


CATEGORY_RENDERERS = {
    "Visual Tracking Card": render_visual_tracking,
    "Sensory Play Prompt (for educator)": render_sensory_prompt,
    "Big Scribble & Coloring": render_coloring,
    "Point & Match Shapes": render_point_match,
    "Body Parts Pointing Game": render_body_parts,
    "Count Together": render_count_together,
    "Letter Tracing": render_tracing_letters,
    "Numeracy - Count & Circle": render_counting_circle,
    "Coloring Page": render_coloring,
    "Shape Matching (Same/Different)": render_shape_match,
    "Shapes & Patterns": render_pattern_complete,
    "Odd One Out": render_odd_one_out,
    "Dot to Dot": render_dot_to_dot,
    "Body Parts Matching": render_body_parts,
}

CATEGORY_TITLES = {
    "Visual Tracking Card": "Look and Track",
    "Sensory Play Prompt (for educator)": "Sensory Exploration Ideas",
    "Big Scribble & Coloring": "Scribble and Color!",
    "Point & Match Shapes": "Point to the Match",
    "Body Parts Pointing Game": "Where Is It?",
    "Count Together": "Let's Count Together",
    "Letter Tracing": "Letter Tracing",
    "Numeracy - Count & Circle": "Count and Circle",
    "Coloring Page": "Color Me In!",
    "Shape Matching (Same/Different)": "Same or Different?",
    "Shapes & Patterns": "What Comes Next?",
    "Odd One Out": "Spot the Difference",
    "Dot to Dot": "Dot to Dot",
    "Body Parts Matching": "Match the Body Parts",
}

# ---------------------------------------------------------------------------
# Rotation / generation
# ---------------------------------------------------------------------------

def get_week_key(d: datetime.date = None) -> str:
    d = d or datetime.date.today()
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def get_week_index(d: datetime.date = None) -> int:
    d = d or datetime.date.today()
    return (d - datetime.date(2020, 1, 6)).days // 7


def get_categories_for_week(week_index: int, age_group: str, n: int = 3) -> list:
    pool = AGE_CATEGORIES[age_group]
    pool_len = len(pool)
    n = min(n, pool_len)
    start = (week_index * n) % pool_len
    return [pool[(start + i) % pool_len] for i in range(n)]


def _maybe_get_ai_title(client, category, age_group, theme, fallback_title):
    try:
        prompt = (
            f"Give ONE fun, short (3-6 word) worksheet/activity title for a {age_group} '{category}' activity"
            + (f" themed around '{theme}'" if theme else "")
            + ". Reply with ONLY the title, nothing else."
        )
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
        )
        title = resp.choices[0].message.content.strip().strip('"')
        return title if 2 <= len(title) <= 60 else fallback_title
    except Exception:
        return fallback_title


def generate_worksheet(client, age_group: str, category: str, theme: str, avoid_topics: list, feedback_text: str) -> dict:
    renderer = CATEGORY_RENDERERS.get(category, render_coloring)
    difficulty = difficulty_from_feedback(feedback_text)
    instructions, body_html = renderer(avoid_topics, difficulty, age_group)

    fallback_title = CATEGORY_TITLES.get(category, "Activity")
    title = _maybe_get_ai_title(client, category, age_group, theme, fallback_title) if client else fallback_title

    html = _render_worksheet_html(title, category, age_group, instructions, body_html)
    return {"title": title, "html": html, "category": category}


WORKSHEET_CSS = """
body { font-family: 'Comic Sans MS', 'Trebuchet MS', sans-serif; background: #fffbe8; margin: 0; padding: 20px; }
.sheet { border: 10px solid transparent; border-image: linear-gradient(90deg, #FF6B6B, #FFD93D, #6BCB77, #4D96FF) 1; padding: 20px; background: white; border-radius: 16px; }
h1 { color: #FF6B6B; text-align: center; font-size: 28px; margin-bottom: 4px; }
.meta { text-align: center; color: #888; font-size: 13px; margin-bottom: 10px; }
.instructions { text-align: center; color: #444; font-size: 15px; margin-bottom: 18px; font-weight: bold; }
.grid { display: flex; flex-direction: column; gap: 14px; }
.match-row { display: flex; align-items: center; gap: 10px; border: 2px dashed #ccc; border-radius: 10px; padding: 8px; }
.big-row { justify-content: center; gap: 24px; }
.cell { display: flex; align-items: center; justify-content: center; }
.answer-circle { margin-left: auto; font-size: 13px; color: #666; border: 2px solid #ccc; border-radius: 20px; padding: 4px 10px; }
.count-row { display: flex; align-items: center; gap: 14px; border: 2px dashed #ccc; border-radius: 10px; padding: 8px; }
.icons { display: flex; flex-wrap: wrap; gap: 4px; flex: 1; }
.number-options { display: flex; gap: 8px; }
.number-bubble { width: 40px; height: 40px; border: 3px solid #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; color: #333; }
.coloring-box { display: flex; justify-content: center; margin: 20px 0; }
.pattern-row { display: flex; align-items: center; gap: 10px; justify-content: center; flex-wrap: wrap; }
.blank-box { width: 70px; height: 70px; border: 3px dashed #333; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 30px; color: #ccc; }
.trace-row { display: flex; gap: 20px; justify-content: center; }
.trace-letter { font-size: 70px; font-weight: bold; color: #ddd; -webkit-text-stroke: 1px #999; }
.sensory-list { display: flex; flex-direction: column; gap: 12px; }
.sensory-row { display: flex; align-items: center; gap: 14px; border: 2px dashed #ccc; border-radius: 10px; padding: 10px; }
.sensory-dot { width: 24px; height: 24px; border-radius: 50%; flex-shrink: 0; }
.sensory-note { color: #888; font-size: 13px; }
.body-parts-layout { display: flex; gap: 30px; align-items: center; justify-content: center; flex-wrap: wrap; }
.legend { display: flex; flex-direction: column; gap: 10px; }
.legend-row { display: flex; align-items: center; gap: 10px; font-size: 18px; }
.legend-num { width: 26px; height: 26px; border-radius: 50%; background: #333; color: white; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; }
.legend-dot { width: 22px; height: 22px; border-radius: 50%; }
@media print { body { background: white; } }
"""


def _render_worksheet_html(title, category, age_group, instructions, body_html):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{WORKSHEET_CSS}</style>
</head>
<body>
  <div class="sheet">
    <h1>🌟 {title} 🌟</h1>
    <div class="meta">{category} &middot; {age_group}</div>
    <div class="instructions">{instructions}</div>
    {body_html}
  </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Streamlit tab
# ---------------------------------------------------------------------------

def worksheet_tab(client):
    init_worksheet_tables()

    st.subheader("🖍️ Weekly Worksheet Generator")
    st.caption("Age-matched to developmental milestones: babies get visual/sensory prompt cards for "
               "the educator, toddlers get big coloring and pointing/matching games, and preschoolers "
               "get tracing, counting, and matching activities that fit where their pencil control "
               "and letter/number recognition actually are.")

    age_group = st.selectbox(
        "Which group are these worksheets for?",
        AGE_BANDS,
        key="worksheet_age_group",
    )
    if age_group == "0-1 years":
        st.info("Babies don't complete worksheets independently — these are visual/sensory prompt cards for you to use with them.")

    theme = st.text_input("This week's theme (optional — leave blank for variety)", key="worksheet_theme")

    week_key = get_week_key()
    week_index = get_week_index()
    existing = get_worksheets_for_week(week_key, age_group)
    existing_categories = {w["category"] for w in existing}
    target_categories = get_categories_for_week(week_index, age_group)
    missing_categories = [c for c in target_categories if c not in existing_categories]

    st.markdown(f"**Week: {week_key}** — {len(existing)}/{len(target_categories)} ready for {age_group}")

    if missing_categories:
        st.info("Not all of this week's activities exist yet: " + ", ".join(missing_categories))
        if st.button("✨ Auto-generate this week's remaining activities", type="primary"):
            feedback_text = get_latest_feedback(age_group)
            avoid_topics = get_recent_titles(age_group, lookback_weeks=8)
            with st.spinner("Generating..."):
                for cat in missing_categories:
                    ws = generate_worksheet(client, age_group, cat, theme, avoid_topics, feedback_text)
                    save_worksheet(week_key, age_group, cat, ws["title"], ws["html"], source="auto")
                    avoid_topics.append(ws["title"])
            st.success("This week's activities are ready.")
            st.rerun()
    else:
        st.success("All of this week's activities are ready. ✅")

    if existing:
        st.markdown("#### This week's activities")
        for w in existing:
            with st.expander(f"{w['category']} — {w['title']}"):
                st.components.v1.html(w["html_content"], height=650, scrolling=True)
                st.download_button(
                    "Download (HTML — open and print/save as PDF from your browser)",
                    data=w["html_content"],
                    file_name=f"{week_key}_{w['category'][:15]}.html",
                    mime="text/html",
                    key=f"dl_{w['id']}",
                )

    st.divider()
    st.markdown("#### Or request a specific activity")
    col1, col2 = st.columns(2)
    with col1:
        manual_category = st.selectbox("Category", AGE_CATEGORIES[age_group], key="manual_ws_category")
    with col2:
        manual_note = st.text_input("Theme hint (optional)", key="manual_ws_note")
    if st.button("Generate this activity"):
        feedback_text = get_latest_feedback(age_group)
        avoid_topics = get_recent_titles(age_group, lookback_weeks=8)
        with st.spinner("Generating..."):
            ws = generate_worksheet(client, age_group, manual_category, manual_note or theme, avoid_topics, feedback_text)
            save_worksheet(week_key, age_group, manual_category, ws["title"], ws["html"], source="manual")
        st.success("Generated!")
        st.components.v1.html(ws["html"], height=650, scrolling=True)
        st.rerun()

    st.divider()
    st.markdown("#### Feedback for next week's difficulty")
    st.caption("Tell it in your own words how this week's activities landed — it'll shape next week's difficulty automatically.")
    feedback_input = st.text_area("e.g. 'Counting was too easy, tracing was just right'", key="ws_feedback_input")
    if st.button("Save feedback"):
        save_feedback(age_group, week_key, feedback_input)
        st.success("Saved — next week will take this into account.")

    with st.expander("📚 Past activities (history / avoid-repeat log)"):
        history = get_worksheet_history(age_group)
        if not history:
            st.caption("No history yet.")
        for w in history:
            st.write(f"**{w['week_key']}** — {w['category']}: {w['title']} _(source: {w['source']})_")