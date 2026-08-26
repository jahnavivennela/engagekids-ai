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

THEME HANDLING: a free-text theme (e.g. "yoga", "space", "farm animals") is
matched against a small set of theme categories (see THEME_KEYWORDS). When
it matches, coloring pages / dot-to-dots / pattern rows / odd-one-out pull
from a themed outline pool for that category instead of the generic shape
pool, so "yoga" actually gets a yoga pose to color in rather than a square.
Unmatched/blank themes fall back to the original generic shape pools.
Whatever item actually gets used (theme-matched or generic) is tracked per
age group + category so the same item doesn't repeat for several weeks.
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
    get_recent_used_items,
    save_feedback,
    get_latest_feedback,
    get_worksheet_history,
)

# ---------------------------------------------------------------------------
# Age-appropriate category pools
# ---------------------------------------------------------------------------

AGE_CATEGORIES = {
    # Gated to what the milestones doc says is realistic per band.
    # 0-6 months / 0-1: no purposeful pencil grip -> visual/sensory prompt cards only.
    "0-6 months": [
        "Visual Tracking Card",
        "Sensory Play Prompt (for educator)",
    ],
    "6-12 months": [
        "Visual Tracking Card",
        "Sensory Play Prompt (for educator)",
    ],
    # 1-2: scribbles with pencil/crayon held in FIST; points to body parts in a game.
    "1-2 years": [
        "Big Scribble & Coloring",
        "Point & Match Shapes",
        "Sensory Play Prompt (for educator)",
    ],
    # 2-3: holds crayon with FINGERS, draws circles/lines; begins to count;
    # recognises similarities/differences -> same/different becomes feasible.
    "2-3 years": [
        "Big Scribble & Coloring",
        "Point & Match Shapes",
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
        "Sensory Play Prompt (for educator)",
        "Count Together",
        "Point & Match Shapes",
        "Themed Story Worksheet",
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
        "Themed Story Worksheet",
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
    "rocket": [(150, 15), (175, 90), (175, 170), (190, 210), (150, 190), (110, 210), (125, 170), (125, 90)],
    "sun": [(150, 30), (170, 70), (215, 55), (195, 100), (240, 120), (195, 140), (215, 185), (170, 170), (150, 210), (130, 170), (85, 185), (105, 140), (60, 120), (105, 100), (85, 55), (130, 70)],
    "butterfly": [(150, 40), (110, 20), (70, 55), (95, 100), (150, 130), (205, 100), (230, 55), (190, 20)],
    "car": [(60, 160), (60, 120), (100, 90), (200, 90), (240, 120), (240, 160), (210, 160), (200, 175), (160, 175), (150, 160), (150, 175), (110, 175), (100, 160)],
}

# ---------------------------------------------------------------------------
# Themed outline library — inner markup assumes viewBox "0 0 120 120",
# fill:none, stroke:#333, stroke-width:5 (matching OUTLINE_EXTRAS style),
# so these behave exactly like the existing shape outlines for coloring.
# ---------------------------------------------------------------------------

THEME_LIBRARY = {
    "animals": {
        "Cat Face": '<circle cx="60" cy="65" r="38" fill="none" stroke="#333" stroke-width="5"/><polygon points="30,40 45,10 55,35" fill="none" stroke="#333" stroke-width="5" stroke-linejoin="round"/><polygon points="90,40 75,10 65,35" fill="none" stroke="#333" stroke-width="5" stroke-linejoin="round"/><circle cx="46" cy="60" r="4" fill="#333"/><circle cx="74" cy="60" r="4" fill="#333"/><path d="M55 78 Q60 84 65 78" fill="none" stroke="#333" stroke-width="4"/><line x1="15" y1="72" x2="42" y2="76" stroke="#333" stroke-width="3"/><line x1="15" y1="84" x2="42" y2="84" stroke="#333" stroke-width="3"/><line x1="105" y1="72" x2="78" y2="76" stroke="#333" stroke-width="3"/><line x1="105" y1="84" x2="78" y2="84" stroke="#333" stroke-width="3"/>',
        "Bunny": '<circle cx="60" cy="72" r="34" fill="none" stroke="#333" stroke-width="5"/><ellipse cx="42" cy="25" rx="10" ry="30" fill="none" stroke="#333" stroke-width="5"/><ellipse cx="78" cy="25" rx="10" ry="30" fill="none" stroke="#333" stroke-width="5"/><circle cx="48" cy="68" r="4" fill="#333"/><circle cx="72" cy="68" r="4" fill="#333"/><path d="M55 85 Q60 90 65 85" fill="none" stroke="#333" stroke-width="4"/>',
        "Puppy": '<ellipse cx="60" cy="68" rx="38" ry="34" fill="none" stroke="#333" stroke-width="5"/><ellipse cx="22" cy="55" rx="16" ry="26" fill="none" stroke="#333" stroke-width="5" transform="rotate(-20 22 55)"/><ellipse cx="98" cy="55" rx="16" ry="26" fill="none" stroke="#333" stroke-width="5" transform="rotate(20 98 55)"/><circle cx="48" cy="65" r="4" fill="#333"/><circle cx="72" cy="65" r="4" fill="#333"/><ellipse cx="60" cy="82" rx="8" ry="6" fill="none" stroke="#333" stroke-width="4"/>',
        "Elephant": '<circle cx="55" cy="55" r="32" fill="none" stroke="#333" stroke-width="5"/><circle cx="95" cy="45" r="18" fill="none" stroke="#333" stroke-width="4"/><path d="M40 78 Q30 100 45 112 Q52 100 44 82" fill="none" stroke="#333" stroke-width="5"/><circle cx="45" cy="50" r="4" fill="#333"/>',
    },
    "vehicles": {
        "Car": '<rect x="15" y="60" width="90" height="30" rx="6" fill="none" stroke="#333" stroke-width="5"/><path d="M28 60 L42 32 H78 L92 60" fill="none" stroke="#333" stroke-width="5"/><circle cx="38" cy="92" r="12" fill="none" stroke="#333" stroke-width="5"/><circle cx="82" cy="92" r="12" fill="none" stroke="#333" stroke-width="5"/>',
        "Fire Truck": '<rect x="10" y="55" width="70" height="32" fill="none" stroke="#333" stroke-width="5"/><rect x="80" y="70" width="30" height="17" fill="none" stroke="#333" stroke-width="5"/><rect x="20" y="35" width="35" height="20" fill="none" stroke="#333" stroke-width="5"/><circle cx="30" cy="92" r="11" fill="none" stroke="#333" stroke-width="5"/><circle cx="65" cy="92" r="11" fill="none" stroke="#333" stroke-width="5"/><circle cx="98" cy="92" r="11" fill="none" stroke="#333" stroke-width="5"/>',
        "Rocket": '<path d="M60 8 C80 30,80 70,70 95 H50 C40 70,40 30,60 8 Z" fill="none" stroke="#333" stroke-width="5"/><circle cx="60" cy="45" r="10" fill="none" stroke="#333" stroke-width="4"/><polygon points="42,80 25,110 50,95" fill="none" stroke="#333" stroke-width="4"/><polygon points="78,80 95,110 70,95" fill="none" stroke="#333" stroke-width="4"/>',
        "Airplane": '<ellipse cx="60" cy="60" rx="45" ry="12" fill="none" stroke="#333" stroke-width="5"/><polygon points="25,60 60,25 60,45" fill="none" stroke="#333" stroke-width="4"/><polygon points="25,60 60,95 60,75" fill="none" stroke="#333" stroke-width="4"/><polygon points="95,52 115,60 95,68" fill="none" stroke="#333" stroke-width="4"/>',
    },
    "space": {
        "Rocket": '<path d="M60 8 C80 30,80 70,70 95 H50 C40 70,40 30,60 8 Z" fill="none" stroke="#333" stroke-width="5"/><circle cx="60" cy="45" r="10" fill="none" stroke="#333" stroke-width="4"/><polygon points="42,80 25,110 50,95" fill="none" stroke="#333" stroke-width="4"/><polygon points="78,80 95,110 70,95" fill="none" stroke="#333" stroke-width="4"/>',
        "Planet": '<circle cx="60" cy="60" r="30" fill="none" stroke="#333" stroke-width="5"/><ellipse cx="60" cy="60" rx="52" ry="14" fill="none" stroke="#333" stroke-width="4"/>',
        "Moon": '<path d="M75 15 A45 45 0 1 0 75 105 A35 35 0 1 1 75 15 Z" fill="none" stroke="#333" stroke-width="5"/>',
        "Star": SHAPE_PATHS["star"].format(c="none"),
    },
    "ocean": {
        "Fish": '<path d="M20 60 Q45 25 85 45 L110 30 L100 60 L110 90 L85 75 Q45 95 20 60 Z" fill="none" stroke="#333" stroke-width="5"/><circle cx="70" cy="52" r="4" fill="#333"/>',
        "Octopus": '<circle cx="60" cy="45" r="30" fill="none" stroke="#333" stroke-width="5"/><path d="M32 60 Q20 90 30 105" fill="none" stroke="#333" stroke-width="5"/><path d="M48 68 Q42 100 50 112" fill="none" stroke="#333" stroke-width="5"/><path d="M72 68 Q78 100 70 112" fill="none" stroke="#333" stroke-width="5"/><path d="M88 60 Q100 90 90 105" fill="none" stroke="#333" stroke-width="5"/><circle cx="50" cy="42" r="4" fill="#333"/><circle cx="70" cy="42" r="4" fill="#333"/>',
        "Whale": '<path d="M10 60 Q30 25 75 35 Q105 25 112 45 Q100 45 95 55 Q108 60 112 70 Q100 68 90 65 Q60 90 20 75 Q8 70 10 60 Z" fill="none" stroke="#333" stroke-width="5"/><circle cx="35" cy="50" r="3" fill="#333"/>',
        "Seashell": '<path d="M60 20 C30 30,20 65,60 105 C100 65,90 30,60 20 Z" fill="none" stroke="#333" stroke-width="5"/><path d="M60 30 V100 M60 40 Q40 60 45 90 M60 40 Q80 60 75 90" fill="none" stroke="#333" stroke-width="3"/>',
    },
    "weather": {
        "Sun": '<circle cx="60" cy="60" r="26" fill="none" stroke="#333" stroke-width="5"/>' + "".join(
            f'<line x1="{60+38*__import__("math").cos(a)}" y1="{60+38*__import__("math").sin(a)}" x2="{60+52*__import__("math").cos(a)}" y2="{60+52*__import__("math").sin(a)}" stroke="#333" stroke-width="5"/>'
            for a in [i * 0.785398 for i in range(8)]
        ),
        "Cloud": '<path d="M30 80 Q10 80 10 62 Q10 45 30 47 Q32 25 58 25 Q85 25 88 48 Q108 48 108 68 Q108 80 88 80 Z" fill="none" stroke="#333" stroke-width="5"/>',
        "Rainbow": '<path d="M10 100 A50 50 0 0 1 110 100" fill="none" stroke="#333" stroke-width="4"/><path d="M25 100 A35 35 0 0 1 95 100" fill="none" stroke="#333" stroke-width="4"/><path d="M40 100 A20 20 0 0 1 80 100" fill="none" stroke="#333" stroke-width="4"/>',
        "Raindrop": '<path d="M60 10 C90 55,90 85,60 105 C30 85,30 55,60 10 Z" fill="none" stroke="#333" stroke-width="5"/>',
    },
    "nature": {
        "Flower": OUTLINE_EXTRAS["flower"],
        "Butterfly": OUTLINE_EXTRAS["butterfly"],
        "Tree": OUTLINE_EXTRAS["tree"],
        "Ladybug": '<ellipse cx="60" cy="65" rx="32" ry="36" fill="none" stroke="#333" stroke-width="5"/><line x1="60" y1="29" x2="60" y2="101" stroke="#333" stroke-width="4"/><circle cx="60" cy="20" r="12" fill="none" stroke="#333" stroke-width="4"/><circle cx="46" cy="55" r="4" fill="#333"/><circle cx="74" cy="55" r="4" fill="#333"/><circle cx="46" cy="82" r="4" fill="#333"/>',
    },
    "yoga": {
        "Tree Pose": '<circle cx="60" cy="20" r="13" fill="none" stroke="#333" stroke-width="5"/><ellipse cx="60" cy="55" rx="17" ry="24" fill="none" stroke="#333" stroke-width="5"/><line x1="60" y1="79" x2="60" y2="112" stroke="#333" stroke-width="9" stroke-linecap="round"/><path d="M60 79 Q34 82 34 65 Q34 60 40 60 Q44 68 60 68" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><path d="M47 42 Q30 20 30 5" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><path d="M73 42 Q90 20 90 5" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><circle cx="30" cy="5" r="6" fill="#333"/><circle cx="90" cy="5" r="6" fill="#333"/><circle cx="60" cy="112" r="7" fill="#333"/>',
        "Star Pose": '<circle cx="60" cy="22" r="13" fill="none" stroke="#333" stroke-width="5"/><ellipse cx="60" cy="55" rx="17" ry="22" fill="none" stroke="#333" stroke-width="5"/><path d="M60 42 L22 10" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><path d="M60 42 L98 10" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><path d="M60 76 L24 114" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><path d="M60 76 L96 114" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><circle cx="22" cy="10" r="6" fill="#333"/><circle cx="98" cy="10" r="6" fill="#333"/><circle cx="24" cy="114" r="6" fill="#333"/><circle cx="96" cy="114" r="6" fill="#333"/>',
        "Cat Pose": '<circle cx="18" cy="50" r="12" fill="none" stroke="#333" stroke-width="5"/><path d="M30 55 Q60 28 92 55" fill="none" stroke="#333" stroke-width="12" stroke-linecap="round"/><path d="M28 58 L20 95" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><path d="M28 58 L38 95" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><path d="M92 58 L84 95" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><path d="M92 58 L102 95" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><circle cx="20" cy="95" r="6" fill="#333"/><circle cx="38" cy="95" r="6" fill="#333"/><circle cx="84" cy="95" r="6" fill="#333"/><circle cx="102" cy="95" r="6" fill="#333"/>',
        "Butterfly Pose": '<circle cx="60" cy="22" r="13" fill="none" stroke="#333" stroke-width="5"/><ellipse cx="60" cy="55" rx="17" ry="22" fill="none" stroke="#333" stroke-width="5"/><path d="M60 74 Q30 78 22 60" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><path d="M60 74 Q90 78 98 60" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><circle cx="22" cy="60" r="7" fill="none" stroke="#333" stroke-width="4"/><circle cx="98" cy="60" r="7" fill="none" stroke="#333" stroke-width="4"/><path d="M47 45 L22 58" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/><path d="M73 45 L98 58" fill="none" stroke="#333" stroke-width="9" stroke-linecap="round"/>',
    },
    "dinosaurs": {
        "Dinosaur": '<path d="M20 95 Q15 60 45 50 Q45 30 65 25 Q75 30 68 42 Q90 42 100 60 L112 55 L108 72 Q100 92 70 92 Q68 100 55 100 Q52 92 45 92 Q25 100 20 95 Z" fill="none" stroke="#333" stroke-width="5"/><circle cx="72" cy="38" r="3" fill="#333"/>',
        "T-Rex": '<path d="M25 95 Q20 65 40 55 Q38 35 60 28 Q78 30 74 45 Q95 45 100 62 Q90 62 88 70 Q95 80 85 92 Q70 95 68 88 Q50 95 40 92 Q22 98 25 95 Z" fill="none" stroke="#333" stroke-width="5"/><circle cx="66" cy="40" r="3" fill="#333"/>',
        "Dino Egg": '<path d="M60 15 C90 15,100 60,80 90 C68 108,52 108,40 90 C20 60,30 15,60 15 Z" fill="none" stroke="#333" stroke-width="5"/><path d="M45 55 L55 65 L50 75 L62 90" fill="none" stroke="#333" stroke-width="3"/>',
        "Footprint": '<ellipse cx="60" cy="80" rx="24" ry="30" fill="none" stroke="#333" stroke-width="5"/><ellipse cx="35" cy="30" rx="9" ry="14" fill="none" stroke="#333" stroke-width="4" transform="rotate(-15 35 30)"/><ellipse cx="60" cy="20" rx="9" ry="14" fill="none" stroke="#333" stroke-width="4"/><ellipse cx="85" cy="30" rx="9" ry="14" fill="none" stroke="#333" stroke-width="4" transform="rotate(15 85 30)"/>',
    },
    "food": {
        "Apple": '<path d="M60 30 C40 20,20 35,20 60 C20 90,40 110,60 110 C80 110,100 90,100 60 C100 35,80 20,60 30 Z" fill="none" stroke="#333" stroke-width="5"/><path d="M60 30 Q55 15 65 8" fill="none" stroke="#333" stroke-width="4"/><path d="M65 12 Q80 8 85 20" fill="none" stroke="#333" stroke-width="3"/>',
        "Banana": '<path d="M30 90 Q20 40 55 20 Q90 5 100 25 Q75 15 55 35 Q30 55 40 95 Q35 100 30 90 Z" fill="none" stroke="#333" stroke-width="5"/>',
        "Carrot": '<path d="M60 30 L80 100 Q60 115 40 100 Z" fill="none" stroke="#333" stroke-width="5"/><path d="M55 30 Q50 10 40 5 M60 28 Q60 8 60 2 M65 30 Q70 10 80 5" fill="none" stroke="#333" stroke-width="3"/>',
        "Watermelon Slice": '<path d="M15 90 A55 55 0 0 1 105 90 Z" fill="none" stroke="#333" stroke-width="5"/><path d="M25 85 A45 45 0 0 1 95 85" fill="none" stroke="#333" stroke-width="3"/><circle cx="45" cy="75" r="3" fill="#333"/><circle cx="60" cy="65" r="3" fill="#333"/><circle cx="75" cy="75" r="3" fill="#333"/>',
    },
}

# Extra DOT_SHAPES keys usable per theme (falls back to any DOT_SHAPES key
# if the theme has none of its own dot-to-dot points defined).
THEME_DOT_SHAPES = {
    "animals": ["fish"],
    "vehicles": ["car", "rocket"],
    "space": ["rocket", "sun"],
    "ocean": ["fish"],
    "weather": ["sun"],
    "nature": ["butterfly"],
    "yoga": ["star"],  # Star Pose = literally a 5-point spread, so the existing
                        # "star" dot-to-dot shape is thematically on point.
    "dinosaurs": [],
    "food": [],
}

THEME_KEYWORDS = {
    "animals": ["animal", "farm", "zoo", "pet", "cat", "dog", "bunny", "rabbit", "elephant", "jungle", "safari"],
    "vehicles": ["vehicle", "car", "truck", "transport", "train", "plane", "airplane", "traffic", "road"],
    "space": ["space", "rocket", "planet", "star", "moon", "astronaut", "galaxy"],
    "ocean": ["ocean", "sea", "under the sea", "fish", "beach", "water", "whale", "octopus", "shell"],
    "weather": ["weather", "sun", "rain", "cloud", "rainbow", "season", "storm"],
    "nature": ["nature", "garden", "flower", "plant", "bug", "insect", "spring", "outdoor"],
    "yoga": ["yoga", "pose", "stretch", "movement", "exercise", "mindful"],
    "dinosaurs": ["dinosaur", "dino", "prehistoric", "jurassic"],
    "food": ["food", "fruit", "vegetable", "healthy eating", "kitchen", "apple", "banana"],
}

# Ordered, human-friendly labels for the theme picker — a dropdown instead of
# free text, so every option shown is guaranteed to actually change the
# worksheet content (no more typing a theme and getting generic shapes back).
THEME_DISPLAY = {
    "animals": "🐾 Animals",
    "food": "🍎 Fruits & Food",
    "nature": "🌼 Nature / Garden",
    "ocean": "🐠 Ocean / Under the Sea",
    "space": "🚀 Space",
    "vehicles": "🚗 Vehicles",
    "weather": "☀️ Weather",
    "yoga": "🧘 Yoga / Movement",
    "dinosaurs": "🦕 Dinosaurs",
}
NO_THEME_LABEL = "🎲 No specific theme (variety)"



def match_theme(theme_text: str):
    """Returns the matching THEME_LIBRARY key for free-text theme input, or
    None if it doesn't match any known category (generic pools are used then)."""
    if not theme_text:
        return None
    t = theme_text.lower()
    for key, words in THEME_KEYWORDS.items():
        if any(w in t for w in words):
            return key
    return None


def ensure_dynamic_theme(client, theme_text: str, age_group: str, n: int = 6):
    """The single place that makes an UNRECOGNIZED typed theme (e.g. 'trees')
    work exactly like a built-in one (e.g. 'yoga') for EVERY renderer, not
    just Coloring Page/Sensory.

    Every renderer — tracing, matching, counting, patterns, odd-one-out —
    decides what to show by checking `theme_key in THEME_LIBRARY`. So instead
    of teaching each renderer separately about "dynamic" themes (which is
    how Coloring Page/Sensory were first wired, and why they were the only
    ones that worked), this function asks the LLM for a handful of item
    names for the typed theme, generates+caches a real image for each
    (image_gen.py), and then ADDS a temporary entry to THEME_LIBRARY itself
    under the normalized theme text as the key.

    From that point on, every renderer sees this theme as if it had always
    been in THEME_LIBRARY — pick_themed_items/pick_icons/tracing all "just
    work" with no other code changes. get_visual_for_item finds the real
    cached image first; the fallback inner SVG (a plain circle) only shows
    if a specific image failed to generate.

    Returns the theme_key to use (the normalized text) so the caller can
    pass it into the renderer exactly like a built-in theme_key.
    Returns None if there's no client/theme text to work with (caller
    should fall back to generic shapes as before)."""
    if not theme_text or not client:
        return None
    from image_gen import _normalize_theme_text, get_or_generate_dynamic_theme
    norm_key = _normalize_theme_text(theme_text)
    if norm_key in THEME_LIBRARY:
        return norm_key  # already registered earlier this session/run

    dynamic_items = get_or_generate_dynamic_theme(client, theme_text, age_group, n=n)
    if not dynamic_items:
        return None

    fallback_inner = SHAPE_PATHS["circle"].format(c="none")
    THEME_LIBRARY[norm_key] = {name: fallback_inner for name, _ in dynamic_items}
    return norm_key


# ---------------------------------------------------------------------------
# Category domains — used to make sure the weekly picks span different kinds
# of learning (numeracy/literacy/cognitive/creative) instead of landing on
# whatever the rotation happens to hit next.
# ---------------------------------------------------------------------------

CATEGORY_DOMAINS = {
    "Visual Tracking Card": "Sensory",
    "Sensory Play Prompt (for educator)": "Sensory / Science",
    "Big Scribble & Coloring": "Creative / Fine Motor",
    "Point & Match Shapes": "Cognitive",
    "Body Parts Pointing Game": "Body Awareness",
    "Count Together": "Numeracy",
    "Letter Tracing": "Literacy",
    "Numeracy - Count & Circle": "Numeracy",
    "Coloring Page": "Creative / Fine Motor",
    "Shape Matching (Same/Different)": "Cognitive",
    "Shapes & Patterns": "Cognitive",
    "Odd One Out": "Cognitive",
    "Dot to Dot": "Fine Motor",
    "Body Parts Matching": "Body Awareness",
    "Themed Story Worksheet": "Multi-Skill",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def shape_svg(name, color, size=90):
    path = SHAPE_PATHS.get(name, SHAPE_PATHS["circle"]).format(c=color)
    return f'<svg viewBox="0 0 120 120" width="{size}" height="{size}">{path}</svg>'


def themed_outline_svg(inner_markup, size=320):
    return f'<svg viewBox="0 0 120 120" width="{size}" height="{size}">{inner_markup}</svg>'


def themed_icon_svg(inner_markup, color, size=90):
    """Same themed outline, but recolored (fill:none -> fill:color) so it can
    be used as a small solid icon in matching/counting/pattern activities,
    not just as a coloring-page outline."""
    colored = inner_markup.replace('fill="none"', f'fill="{color}"')
    return f'<svg viewBox="0 0 120 120" width="{size}" height="{size}">{colored}</svg>'


def get_visual_for_item(theme_key, item_name, fallback_svg_inner, size, colored=False, color="#333"):
    """Central place every renderer goes through to get a picture for one
    themed item. Prefers a real cached AI illustration (see image_gen.py) if
    one exists for this (theme_key, item_name) pair — falls back to the
    hand-drawn SVG outline otherwise. This means: pre-generate images for a
    theme once (build_theme_image_library / get_or_generate_dynamic_theme),
    and EVERY activity type (coloring, tracing, matching, counting, pattern,
    odd-one-out) that uses this item automatically upgrades to the real
    picture — no other code changes needed."""
    if theme_key and item_name:
        try:
            from image_gen import get_theme_image_path, image_path_to_data_uri
            path = get_theme_image_path(theme_key, item_name)
            if path:
                return f'<img src="{image_path_to_data_uri(path)}" width="{size}" height="{size}" style="object-fit:contain;">'
        except Exception:
            pass  # image_gen not set up yet, or no cached image — fall back below
    if colored:
        return themed_icon_svg(fallback_svg_inner, color, size)
    return themed_outline_svg(fallback_svg_inner, size)


def icon_svg(name, theme_key, color, size=90):
    """Renders one icon by name — a real cached picture or themed SVG if
    `name` belongs to the current theme's pool, otherwise a generic shape."""
    if theme_key and name in THEME_LIBRARY.get(theme_key, {}):
        return get_visual_for_item(theme_key, name, THEME_LIBRARY[theme_key][name], size, colored=True, color=color)
    return shape_svg(name, color, size)


def pick_icons(theme_key, avoid, n, generic_pool):
    """Picks `n` icon names — from the theme's pool when one is set and it
    has enough not-recently-used items, otherwise from the generic shape
    pool (so matching/counting/pattern activities go thematic too, not just
    coloring pages and dot-to-dots)."""
    avoid_lower = {a.lower() for a in avoid}
    if theme_key:
        theme_pool = list(THEME_LIBRARY.get(theme_key, {}).keys())
        choices = [x for x in theme_pool if x.lower() not in avoid_lower] or theme_pool
        if choices:
            random.shuffle(choices)
            return (choices * ((n // len(choices)) + 1))[:n]
    avoid_text = " ".join(avoid).lower()
    choices = [s for s in generic_pool if s not in avoid_text] or generic_pool
    random.shuffle(choices)
    return (choices * ((n // len(choices)) + 1))[:n]


def pick_shapes(avoid_titles, n, pool):
    avoid_text = " ".join(avoid_titles).lower()
    choices = [s for s in pool if s not in avoid_text] or pool
    random.shuffle(choices)
    return (choices * ((n // len(choices)) + 1))[:n]


def pick_themed_item(theme_key, avoid_items):
    """Picks one (name, inner_svg) from a theme's outline pool, skipping
    anything used recently for this age group + category. Returns None if
    the theme has no items available (caller should fall back to generic)."""
    if not theme_key:
        return None
    pool = THEME_LIBRARY.get(theme_key, {})
    if not pool:
        return None
    avoid_lower = {a.lower() for a in avoid_items}
    choices = [(name, svg) for name, svg in pool.items() if name.lower() not in avoid_lower]
    if not choices:
        choices = list(pool.items())  # exhausted the theme pool — recycle rather than block
    return random.choice(choices)


def pick_themed_items(theme_key, avoid_items, n):
    """Like pick_themed_item, but returns up to n DISTINCT (name, inner_svg)
    pairs so a coloring page can show several themed items instead of one —
    fills the sheet and gives the educator a proper page's worth of content.
    Returns fewer than n (even []) if the theme pool doesn't have that many
    or no theme is set; caller fills the rest from the generic shape pool."""
    if not theme_key:
        return []
    pool = list(THEME_LIBRARY.get(theme_key, {}).items())
    if not pool:
        return []
    avoid_lower = {a.lower() for a in avoid_items}
    fresh = [(name, svg) for name, svg in pool if name.lower() not in avoid_lower]
    random.shuffle(fresh)
    picked, seen = [], set()
    for name, svg in fresh:
        picked.append((name, svg))
        seen.add(name)
        if len(picked) >= n:
            return picked
    # Theme pool exhausted before reaching n — recycle remaining items rather
    # than leaving the sheet sparse.
    leftovers = [(name, svg) for name, svg in pool if name not in seen]
    random.shuffle(leftovers)
    for name, svg in leftovers:
        picked.append((name, svg))
        if len(picked) >= n:
            break
    return picked


def pick_generic_shapes(avoid_titles, avoid_items, n, pool_dict):
    """Picks up to n DISTINCT shape names from pool_dict (a name -> svg-inner
    mapping), preferring ones not recently used, so multiple generic shapes
    can fill a coloring page when the theme pool runs short."""
    if not pool_dict:
        return []
    avoid_text = (" ".join(avoid_titles) + " " + " ".join(avoid_items)).lower()
    names = list(pool_dict.keys())
    fresh = [k for k in names if k not in avoid_text]
    random.shuffle(fresh)
    random.shuffle(names)
    picked = []
    for k in fresh:
        if k not in picked:
            picked.append(k)
        if len(picked) >= n:
            return picked
    for k in names:
        if k in picked:
            continue
        picked.append(k)
        if len(picked) >= n:
            break
    return picked


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
# Renderers — every function takes (avoid_titles, difficulty, age_group,
# theme_key, avoid_items) and returns (instructions, body_html, used_items)
# where used_items is a list of the specific item names used, for repeat
# tracking. Most renderers ignore theme_key/avoid_items (no themed content
# fits them) and just pass avoid_titles through as before.
# ---------------------------------------------------------------------------

def render_visual_tracking(avoid_titles, difficulty, age_group, theme_key, avoid_items):
    """Babies: bold black/white/red bullseye pattern — classic newborn visual
    stimulation, NOT a task for the baby to complete."""
    rings = ""
    ring_colors = ["#000000", "#FFFFFF", "#000000", "#FF0000", "#FFFFFF"]
    for i, c in enumerate(ring_colors):
        r = 100 - i * 18
        rings += f'<circle cx="150" cy="150" r="{r}" fill="{c}" stroke="#000" stroke-width="2"/>'
    svg = f'<svg viewBox="0 0 300 300" width="360" height="360">{rings}</svg>'
    instructions = "For the educator: hold this card 20–30cm from the baby's face and slowly move it side to side. High-contrast patterns support early visual tracking."
    return instructions, f'<div class="coloring-box">{svg}</div>', ["Bullseye Card"]


def render_sensory_prompt(avoid_titles, difficulty, age_group, theme_key, avoid_items, client=None, raw_theme_text=None):
    """Not a worksheet — a reference card of sensory materials to offer.
    Sensory exploration itself can't happen on paper, so this stays an
    educator prompt card rather than a fill-in task.

    Tries a real picture of each material via the cached image path (same
    idea as every other renderer) — falls back to the plain colored dot if
    no image is cached/available. Sensory materials aren't naturally
    theme-shaped the way an animal or pose is, so the theme just flavors
    the image prompt (e.g. 'sand, ocean theme') rather than picking which
    materials appear."""
    avoid_text = (" ".join(avoid_titles) + " " + " ".join(avoid_items)).lower()
    choices = [s for s in SENSORY_ITEMS if s[0].lower() not in avoid_text] or SENSORY_ITEMS
    picks = random.sample(choices, min(4, len(choices)))

    lookup_theme_key = theme_key
    if not lookup_theme_key and raw_theme_text:
        from image_gen import _normalize_theme_text
        lookup_theme_key = _normalize_theme_text(raw_theme_text)

    def _row(i, name, note):
        visual = None
        if lookup_theme_key and client:
            try:
                from image_gen import generate_and_cache_theme_image, get_theme_image_path, image_path_to_data_uri
                path = get_theme_image_path(lookup_theme_key, name) or generate_and_cache_theme_image(lookup_theme_key, name, age_group)
                if path:
                    visual = f'<img src="{image_path_to_data_uri(path)}" width="70" height="70" style="border-radius:10px;object-fit:cover;">'
            except Exception:
                pass
        icon = visual or f'<div class="sensory-dot" style="background:{COLORS[i % len(COLORS)]}"></div>'
        return f'<div class="sensory-row">{icon}<div><b>{name}</b><br><span class="sensory-note">{note}</span></div></div>'

    rows = "".join(_row(i, name, note) for i, (name, note) in enumerate(picks))
    instructions = "For the educator: offer one item at a time and observe/note the child's reaction and exploration."
    return instructions, f'<div class="sensory-list">{rows}</div>', [name for name, _ in picks]


def _warn_theme_fallback(raw_theme_text, theme_key, resolved_any):
    """Shows a warning IN THE APP (not just the terminal) when a typed theme
    couldn't produce real pictures and the sheet fell back to generic
    shapes/hearts/hexagons. This is almost always because OPENAI_API_KEY
    isn't set in .streamlit/secrets.toml — see image_gen.py's
    _call_image_api, which needs that key for the actual image generation
    (the Groq key alone only gets you the item NAMES, e.g. "river", "boat",
    "fish" — not pictures of them)."""
    if theme_key is None and raw_theme_text and not resolved_any:
        st.warning(
            f"Couldn't generate real pictures for the theme \"{raw_theme_text}\" — showing "
            "generic shapes instead. This usually means OPENAI_API_KEY is missing or invalid "
            "in .streamlit/secrets.toml (needed by image_gen.py's image generation call). "
            "Check your terminal for the exact error printed just above this."
        )


def render_coloring(avoid_titles, difficulty, age_group, theme_key, avoid_items, client=None, raw_theme_text=None):
    """Fills the sheet with SEVERAL items to color instead of one small
    centered outline — count and size scale by age so younger children get
    fewer, bigger shapes and older children get more, smaller ones. Each
    item is labeled underneath with its name.

    If theme_key is None but raw_theme_text was typed (an unrecognized
    theme) and a client is available, tries the dynamic AI-image path from
    image_gen.py before falling back to plain generic shapes — so "allow
    any theme" actually gets themed pictures, not just a fallback square."""
    ITEM_COUNT_BY_AGE = {
        "1-2 years": 2,
        "2-3 years": 3,
        "3-4 years": 4,
        "4-5 years": 6,
    }
    ITEM_SIZE_BY_AGE = {
        "1-2 years": 380,
        "2-3 years": 330,
        "3-4 years": 280,
        "4-5 years": 250,
    }
    n = ITEM_COUNT_BY_AGE.get(age_group, 4)
    size = ITEM_SIZE_BY_AGE.get(age_group, 200)

    items = []  # list of (name, svg_or_img_html)

    themed = pick_themed_items(theme_key, avoid_items, n) if age_group not in ("0-6 months", "6-12 months", "1-2 years") else []
    for name, inner in themed:
        items.append((name, get_visual_for_item(theme_key, name, inner, size)))

    # Dynamic AI-image path — only tried when the fixed library didn't match
    # but the educator actually typed a theme, and only for ages where a
    # themed picture activity is age-appropriate at all.
    if not items and raw_theme_text and client and age_group not in ("0-6 months", "6-12 months", "1-2 years"):
        try:
            from image_gen import get_or_generate_dynamic_theme, image_path_to_data_uri
            dynamic_items = get_or_generate_dynamic_theme(client, raw_theme_text, age_group, n=n)
            for name, path in dynamic_items:
                if path:
                    img_html = f'<img src="{image_path_to_data_uri(path)}" width="{size}" height="{size}" style="object-fit:contain;">'
                    items.append((name, img_html))
        except Exception as e:
            print(f"[render_coloring] dynamic theme image path failed: {e}")
            # falls through to generic shapes below, as before

    _warn_theme_fallback(raw_theme_text, theme_key, bool(items))

    if len(items) < n:
        remaining = n - len(items)
        if age_group in ("0-6 months", "6-12 months", "1-2 years", "2-3 years"):
            pool = {k: SHAPE_PATHS[k].format(c="none") for k in SIMPLE_SHAPES}
        else:
            pool = {**{k: SHAPE_PATHS[k].format(c="none") for k in ALL_SHAPES}, **OUTLINE_EXTRAS}
        used_names = {name for name, _ in items}
        pool = {k: v for k, v in pool.items() if k not in used_names}
        picks = pick_generic_shapes(avoid_titles, avoid_items, remaining, pool)
        for name in picks:
            svg = f'<svg viewBox="0 0 120 120" width="{size}" height="{size}">{pool[name]}</svg>'
            items.append((name, svg))

    cells = "".join(
        f'<div class="coloring-cell"><div class="coloring-cell-svg">{svg}</div>'
        f'<div class="coloring-cell-label">{name}</div></div>'
        for name, svg in items
    )
    instructions = "Color me in! Use as many colors as you like."
    used_item_names = [name for name, _ in items]
    return instructions, f'<div class="coloring-grid">{cells}</div>', used_item_names


def render_theme_story_sheet(avoid_titles, difficulty, age_group, theme_key, avoid_items, client=None, raw_theme_text=None):
    """A single worksheet with several short, picture-only sections instead
    of one activity type — count, match, color, draw. No reading/writing
    required, so it works for children who can't yet write the theme word.
    Works for ANY theme (built-in or freely typed) because every picture
    comes through get_visual_for_item / pick_themed_items, same as
    render_coloring — no per-theme content is hardcoded here."""
    SIZE_BY_AGE = {"1-2 years": 90, "2-3 years": 80, "3-4 years": 70, "4-5 years": 60}
    size = SIZE_BY_AGE.get(age_group, 70)
    used_all = []

    # gather enough distinct themed items for count + match + color sections
    # (3 for counting, 2 for matching pairs, 3 for coloring) — falls back to
    # the dynamic AI-image theme path, then generic shapes, exactly like
    # render_coloring does, so an unrecognized typed theme still works.
    items = pick_themed_items(theme_key, avoid_items, 8)
    if len(items) < 8 and raw_theme_text and client and age_group not in ("0-6 months", "6-12 months", "1-2 years"):
        try:
            from image_gen import get_or_generate_dynamic_theme
            dynamic_items = get_or_generate_dynamic_theme(client, raw_theme_text, age_group, n=8)
            for name, path in dynamic_items:
                if path and name not in {n for n, _ in items}:
                    items.append((name, None))  # image comes from cache via get_visual_for_item below
        except Exception as e:
            print(f"[render_theme_story_sheet] dynamic theme image path failed: {e}")

    _warn_theme_fallback(raw_theme_text, theme_key, bool(items))

    if len(items) < 8:
        pool = {k: SHAPE_PATHS[k].format(c="none") for k in ALL_SHAPES}
        used_names = {name for name, _ in items}
        pool = {k: v for k, v in pool.items() if k not in used_names}
        picks = pick_generic_shapes(avoid_titles, avoid_items, 8 - len(items), pool)
        items.extend((name, pool[name]) for name in picks)

    def pic(idx, colored=False):
        name, inner = items[idx % len(items)]
        return name, get_visual_for_item(theme_key, name, inner or "", size, colored=colored, color=random.choice(COLORS))

    sections = []

    # 1. Count section
    count_rows = []
    for i in range(2):
        name, visual = pic(i, colored=True)
        count = random.randint(2, 4)
        icons = "".join(get_visual_for_item(theme_key, name, items[i % len(items)][1] or "", size, colored=True, color=random.choice(COLORS)) for _ in range(count))
        options = sorted({count, max(1, count - 1), count + 1})
        options_html = "".join(f'<div class="number-bubble">{n}</div>' for n in options)
        count_rows.append(f'<div class="count-row"><div class="icons">{icons}</div><div class="number-options">{options_html}</div></div>')
    sections.append(('1. Count and Circle', '<div class="grid">' + "".join(count_rows) + '</div>', 'Count the pictures in each row, then circle the correct number.'))
    used_all.extend([items[0][0], items[1][0]])

    # 2. Match section (same/different pairs)
    match_rows = []
    for i in range(2, 4):
        name, visual_a = pic(i, colored=True)
        same = random.random() > 0.5
        _, visual_b = pic(i, colored=True) if same else pic(i + 4, colored=True)
        match_rows.append(f'<div class="match-row"><div class="cell">{visual_a}</div><div class="cell">{visual_b}</div><div class="answer-circle">SAME&nbsp;&nbsp;&nbsp;DIFFERENT</div></div>')
    sections.append(('2. Same or Different?', '<div class="grid">' + "".join(match_rows) + '</div>', 'Look at each pair. Circle SAME if they match, or DIFFERENT if they don\u2019t.'))
    used_all.extend([items[2][0], items[3][0]])

    # 3. Color section
    color_cells = ""
    for i in range(4, 7):
        name, visual = pic(i)
        color_cells += f'<div class="coloring-cell"><div class="coloring-cell-svg">{visual}</div><div class="coloring-cell-label">{name}</div></div>'
    sections.append(('3. Color the Pictures', f'<div class="coloring-grid">{color_cells}</div>', 'Color each picture in.'))
    used_all.extend([items[4][0], items[5][0], items[6][0]])

    # 4. Draw-your-own section
    sections.append(('4. Draw Your Own', '<div class="coloring-box"><div class="blank-box" style="width:220px;height:220px;font-size:60px;">?</div></div>', 'Draw and color your own picture in the box.'))

    body = "".join(
        f'<div class="section"><div class="section-title">{title}</div>'
        f'<div class="instructions" style="font-size:16px;margin-bottom:14px;">{instr}</div>{html}</div>'
        for title, html, instr in sections
    )
    instructions = "Work through each part below with your grown-up or educator."
    return instructions, body, used_all


def render_point_match(avoid_titles, difficulty, age_group, theme_key, avoid_items):
    """Toddlers: point to the matching shape — no line-drawing required."""
    rows = 2 if difficulty == "easy" else 3
    shapes = pick_icons(theme_key, avoid_titles + avoid_items, rows, SIMPLE_SHAPES)
    row_html = ""
    for shape in shapes:
        color = random.choice(COLORS)
        options = [color, color, random.choice([c for c in COLORS if c != color])]
        random.shuffle(options)
        cells = "".join(f'<div class="cell">{icon_svg(shape, theme_key, c, size=100)}</div>' for c in options)
        row_html += f'<div class="match-row big-row">{cells}</div>'
    instructions = "Point to the two shapes in each row that are the SAME color."
    return instructions, f'<div class="grid">{row_html}</div>', shapes


def render_shape_match(avoid_titles, difficulty, age_group, theme_key, avoid_items):
    """Preschool: circle SAME or DIFFERENT — a mark-making task, appropriate
    once pencil grip is developing."""
    rows = {"easy": 3, "medium": 4, "hard": 5}[difficulty]
    shapes = pick_icons(theme_key, avoid_titles + avoid_items, rows, ALL_SHAPES)
    row_html = ""
    for shape in shapes:
        color_a = random.choice(COLORS)
        color_b = color_a if random.random() > 0.5 else random.choice([c for c in COLORS if c != color_a])
        cells = f'<div class="cell">{icon_svg(shape, theme_key, color_a)}</div><div class="cell">{icon_svg(shape, theme_key, color_b)}</div>'
        row_html += f'<div class="match-row">{cells}<div class="answer-circle">SAME&nbsp;&nbsp;&nbsp;DIFFERENT</div></div>'
    instructions = "Look at each pair. Circle SAME if they match, or DIFFERENT if they don't."
    return instructions, f'<div class="grid">{row_html}</div>', shapes


def render_count_together(avoid_titles, difficulty, age_group, theme_key, avoid_items):
    """Toddlers: a verbal/pointing counting activity, not a writing task."""
    rows = 3
    shapes = pick_icons(theme_key, avoid_titles + avoid_items, rows, SIMPLE_SHAPES)
    row_html = ""
    for shape in shapes:
        count = random.randint(1, 3)
        color = random.choice(COLORS)
        icons = "".join(icon_svg(shape, theme_key, color, size=55) for _ in range(count))
        row_html += f'<div class="count-row"><div class="icons">{icons}</div></div>'
    instructions = "For the educator: count out loud together with the child, pointing to each shape as you count."
    return instructions, f'<div class="grid">{row_html}</div>', shapes


def render_counting_circle(avoid_titles, difficulty, age_group, theme_key, avoid_items):
    """Preschool: circle the correct number rather than write it from memory."""
    max_count = {"easy": 5, "medium": 8, "hard": 10}[difficulty]
    rows = 4
    shapes = pick_icons(theme_key, avoid_titles + avoid_items, rows, ALL_SHAPES)
    row_html = ""
    for shape in shapes:
        count = random.randint(2, max_count)
        color = random.choice(COLORS)
        icons = "".join(icon_svg(shape, theme_key, color, size=42) for _ in range(count))
        distractors = sorted({count, max(1, count - 1), min(max_count + 2, count + 2)})
        while len(distractors) < 3:
            distractors.add(random.randint(1, max_count + 2))
        options = sorted(distractors)
        options_html = "".join(f'<div class="number-bubble">{n}</div>' for n in options)
        row_html += f'<div class="count-row"><div class="icons">{icons}</div><div class="number-options">{options_html}</div></div>'
    instructions = "Count the shapes in each row, then circle the correct number."
    return instructions, f'<div class="grid">{row_html}</div>', shapes


def render_pattern_complete(avoid_titles, difficulty, age_group, theme_key, avoid_items):
    """Three separate pattern rows instead of one — a single row read as
    too thin a worksheet (just one line), so this now gives three genuinely
    different sequences (different shape pairs/colors each) stacked on one
    page, all still pulling from the theme via pick_icons/icon_svg."""
    length = {"easy": 4, "medium": 5, "hard": 6}[difficulty]
    used_shapes = []
    row_blocks = []
    for _ in range(3):
        shape_a, shape_b = pick_icons(theme_key, avoid_titles + avoid_items + used_shapes, 2, ALL_SHAPES)
        used_shapes.extend([shape_a, shape_b])
        color_a, color_b = random.sample(COLORS, 2)
        sequence = [(shape_a, color_a) if i % 2 == 0 else (shape_b, color_b) for i in range(length)]
        icons = "".join(icon_svg(s, theme_key, c, size=65) for s, c in sequence)
        blank = '<div class="blank-box">?</div>'
        row_blocks.append(f'<div class="pattern-row">{icons}{blank}</div>')
    instructions = "What comes next in each row? Draw and color the missing shape in each empty box."
    return instructions, '<div class="pattern-stack">' + "".join(row_blocks) + '</div>', used_shapes


def render_odd_one_out(avoid_titles, difficulty, age_group, theme_key, avoid_items):
    rows = {"easy": 2, "medium": 3, "hard": 4}[difficulty]
    shapes = pick_icons(theme_key, avoid_titles + avoid_items, rows, ALL_SHAPES)
    row_html = ""
    for shape in shapes:
        base_color = random.choice(COLORS)
        odd_color = random.choice([c for c in COLORS if c != base_color])
        positions = [base_color] * 4
        positions[random.randint(0, 3)] = odd_color
        icons = "".join(f'<div class="cell">{icon_svg(shape, theme_key, c)}</div>' for c in positions)
        row_html += f'<div class="match-row">{icons}</div>'
    instructions = "Circle the shape in each row that is different from the others."
    return instructions, f'<div class="grid">{row_html}</div>', shapes


def render_tracing_letters(avoid_titles, difficulty, age_group, theme_key, avoid_items):
    reps = {"easy": 2, "medium": 3, "hard": 4}[difficulty]
    avoid_text = (" ".join(avoid_titles) + " " + " ".join(avoid_items)).upper()

    # Map each letter to a theme item name starting with it, so the sheet can
    # show "T is for Tree Pose" with a small picture — otherwise tracing just
    # showed plain letters with no visible connection to the typed theme.
    letter_to_item = {}
    if theme_key:
        for name, svg in THEME_LIBRARY.get(theme_key, {}).items():
            first = name[0].upper()
            if first not in letter_to_item:
                letter_to_item[first] = (name, svg)
        base_pool = sorted(letter_to_item.keys()) or LETTERS
    else:
        base_pool = LETTERS

    choices = [l for l in base_pool if l not in avoid_text] or base_pool
    letters = random.sample(choices, min(3, len(choices)))

    def _row(letter):
        trace_spans = "".join(f"<span class='trace-letter'>{letter}</span>" for _ in range(reps))
        if letter in letter_to_item:
            item_name, item_svg = letter_to_item[letter]
            icon = get_visual_for_item(theme_key, item_name, item_svg, 90)
            return (
                f'<div class="trace-row-themed">'
                f'<div class="trace-row-icon">{icon}<div class="trace-row-caption">{letter} is for {item_name}</div></div>'
                f'<div class="trace-row">{trace_spans}</div>'
                f'</div>'
            )
        return f'<div class="trace-row">{trace_spans}</div>'

    row_html = "".join(_row(letter) for letter in letters)
    instructions = "Trace over each letter with your finger, then with a pencil or crayon."
    return instructions, f'<div class="grid">{row_html}</div>', letters


def render_dot_to_dot(avoid_titles, difficulty, age_group, theme_key, avoid_items):
    avoid_text = (" ".join(avoid_titles) + " " + " ".join(avoid_items)).lower()
    theme_options = THEME_DOT_SHAPES.get(theme_key, []) if theme_key else []
    candidate_keys = theme_options if theme_options else list(DOT_SHAPES.keys())
    choices = [k for k in candidate_keys if k not in avoid_text] or candidate_keys or list(DOT_SHAPES.keys())
    name = random.choice(choices)
    points = DOT_SHAPES[name]
    if difficulty == "easy":
        points = points[:max(4, len(points) // 2)]
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="6" fill="#333"/><text x="{x+10}" y="{y+5}" font-size="16" font-weight="bold" fill="#333">{i}</text>'
        for i, (x, y) in enumerate(points, start=1)
    )
    svg = f'<svg viewBox="0 0 300 260" width="420" height="365">{dots}</svg>'
    instructions = "Join the dots in order from 1 to the end to reveal a picture, then color it in!"
    return instructions, f'<div class="coloring-box">{svg}</div>', [name]


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
    return f'<svg viewBox="0 0 300 260" width="340" height="300">{figure}{dots}</svg>'


def render_body_parts(avoid_titles, difficulty, age_group, theme_key, avoid_items):
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
    return instructions, body, [name for name, _ in BODY_PARTS]


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
    "Themed Story Worksheet": render_theme_story_sheet,
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
    "Themed Story Worksheet": "Let's Explore Together",
}

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

BODY_PARTS = [
    ("Eyes", (60, 38)),
    ("Ears", (28, 45)),
    ("Nose", (60, 52)),
    ("Hands", (0, 140)),
    ("Feet", (40, 230)),
]

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


def get_categories_for_week(week_index: int, age_group: str, n: int = 2, seed_offset: int = 0) -> list:
    """Picks `n` categories for the week, spreading across different domains
    (numeracy/literacy vs. cognitive/creative/etc.) where the age group's
    pool has more than one domain available, so a week never lands on the
    same style of activity twice. `seed_offset` lets the caller ask for a
    different pick for the *same* week (used by the "get different ones"
    regenerate button)."""
    pool = AGE_CATEGORIES[age_group]
    n = min(n, len(pool))

    domains = {}
    for cat in pool:
        domains.setdefault(CATEGORY_DOMAINS.get(cat, "General"), []).append(cat)
    domain_names = sorted(domains.keys())

    rnd = random.Random((week_index * 97) + seed_offset)
    picked = []
    d_idx = (week_index + seed_offset) % max(1, len(domain_names))
    tries = 0
    while len(picked) < n and tries < len(domain_names) * 3:
        domain = domain_names[d_idx % len(domain_names)]
        choices = [c for c in domains[domain] if c not in picked]
        if choices:
            picked.append(rnd.choice(choices))
        d_idx += 1
        tries += 1
    # If the pool is small and ran out of fresh domains, fill from whatever's left.
    for cat in pool:
        if len(picked) >= n:
            break
        if cat not in picked:
            picked.append(cat)
    return picked[:n]


def _maybe_get_ai_title(client, category, age_group, theme, fallback_title):
    try:
        prompt = (
            f"Give ONE fun, short (3-6 word) worksheet/activity title for a {age_group} '{category}' activity"
            + (f" themed around '{theme}'" if theme else "")
            + ". Reply with ONLY the title, nothing else."
        )
        resp = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
        )
        title = resp.choices[0].message.content.strip().strip('"')
        return title if 2 <= len(title) <= 60 else fallback_title
    except Exception:
        return fallback_title


def generate_worksheet(client, age_group: str, category: str, theme: str, avoid_topics: list, feedback_text: str, avoid_items: list = None) -> dict:
    renderer = CATEGORY_RENDERERS.get(category, render_coloring)
    difficulty = difficulty_from_feedback(feedback_text)
    theme_key = match_theme(theme)
    if theme_key is None and theme and client:
        # Not a built-in theme (e.g. "trees") — register it dynamically so
        # EVERY renderer (tracing, matching, counting, patterns, not just
        # Coloring Page) treats it exactly like a built-in one from here on.
        theme_key = ensure_dynamic_theme(client, theme, age_group)

    # render_coloring and render_sensory_prompt also accept client/raw theme
    # text directly, as a second path — harmless if theme_key is already
    # resolved above (ensure_dynamic_theme is cached, so this is a no-op).
    if renderer in (render_coloring, render_sensory_prompt, render_theme_story_sheet):
        instructions, body_html, used_items = renderer(
            avoid_topics, difficulty, age_group, theme_key, avoid_items or [],
            client=client, raw_theme_text=theme,
        )
    else:
        instructions, body_html, used_items = renderer(avoid_topics, difficulty, age_group, theme_key, avoid_items or [])

    fallback_title = CATEGORY_TITLES.get(category, "Activity")
    title = _maybe_get_ai_title(client, category, age_group, theme, fallback_title) if client else fallback_title

    html = _render_worksheet_html(title, category, age_group, instructions, body_html)
    return {"title": title, "html": html, "category": category, "used_items": used_items}


WORKSHEET_CSS = """
@page { size: A4; margin: 8mm; }
body { font-family: 'Comic Sans MS', 'Trebuchet MS', sans-serif; background: #fffbe8; margin: 0; padding: 20px; }
/* .sheet is sized to the full A4 printable area (210mm wide, 8mm page margin
   each side = 194mm usable) so worksheets fill one whole printed page instead
   of a small centered box. On screen it's capped so it still previews nicely
   inside the Streamlit iframe. */
.sheet { border: 10px solid transparent; border-image: linear-gradient(90deg, #FF6B6B, #FFD93D, #6BCB77, #4D96FF) 1; padding: 28px; background: white; border-radius: 16px; width: 194mm; min-height: 273mm; box-sizing: border-box; margin: 0 auto; page-break-inside: avoid; overflow: hidden; }
h1 { color: #FF6B6B; text-align: center; font-size: 38px; margin-bottom: 6px; }
.meta { text-align: center; color: #888; font-size: 15px; margin-bottom: 12px; }
.instructions { text-align: center; color: #444; font-size: 19px; margin-bottom: 22px; font-weight: bold; }
.grid { display: flex; flex-direction: column; gap: 14px; }
.match-row { display: flex; align-items: center; gap: 10px; border: 2px dashed #ccc; border-radius: 10px; padding: 8px; }
.big-row { justify-content: center; gap: 24px; }
.cell { display: flex; align-items: center; justify-content: center; }
.answer-circle { margin-left: auto; font-size: 13px; color: #666; border: 2px solid #ccc; border-radius: 20px; padding: 4px 10px; }
.count-row { display: flex; align-items: center; gap: 14px; border: 2px dashed #ccc; border-radius: 10px; padding: 8px; }
.icons { display: flex; flex-wrap: wrap; gap: 4px; flex: 1; }
.number-options { display: flex; gap: 8px; }
.number-bubble { width: 52px; height: 52px; border: 3px solid #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: bold; color: #333; }
.coloring-box { display: flex; justify-content: center; margin: 24px 0; }
.coloring-grid { display: flex; flex-wrap: wrap; justify-content: center; align-content: flex-start; gap: 40px; margin: 24px 0; }
.coloring-cell { display: flex; flex-direction: column; align-items: center; }
.coloring-cell-svg { display: flex; align-items: center; justify-content: center; }
.coloring-cell-label { margin-top: 10px; font-size: 18px; font-weight: bold; color: #444; text-transform: capitalize; }
.pattern-row { display: flex; align-items: center; gap: 14px; justify-content: center; flex-wrap: wrap; }
.pattern-stack { display: flex; flex-direction: column; gap: 32px; margin: 24px 0; }
.blank-box { width: 90px; height: 90px; border: 3px dashed #333; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 38px; color: #ccc; }
.trace-row { display: flex; gap: 20px; justify-content: center; }
.trace-letter { font-size: 110px; font-weight: bold; color: #ddd; -webkit-text-stroke: 1px #999; }
.trace-row-themed { display: flex; align-items: center; gap: 20px; margin-bottom: 10px; }
.trace-row-icon { display: flex; flex-direction: column; align-items: center; }
.trace-row-caption { font-size: 15px; font-weight: bold; color: #444; margin-top: 4px; text-align: center; max-width: 120px; }
.sensory-list { display: flex; flex-direction: column; gap: 12px; }
.sensory-row { display: flex; align-items: center; gap: 14px; border: 2px dashed #ccc; border-radius: 10px; padding: 10px; }
.sensory-dot { width: 24px; height: 24px; border-radius: 50%; flex-shrink: 0; }
.sensory-note { color: #888; font-size: 13px; }
.body-parts-layout { display: flex; gap: 30px; align-items: center; justify-content: center; flex-wrap: wrap; }
.legend { display: flex; flex-direction: column; gap: 10px; }
.legend-row { display: flex; align-items: center; gap: 10px; font-size: 18px; }
.legend-num { width: 26px; height: 26px; border-radius: 50%; background: #333; color: white; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; }
.legend-dot { width: 22px; height: 22px; border-radius: 50%; }
.section { margin-bottom: 28px; padding-bottom: 20px; border-bottom: 2px dashed #eee; }
.section:last-child { border-bottom: none; }
.section-title { font-size: 22px; font-weight: bold; color: #4D96FF; margin-bottom: 4px; }
@media print { body { background: white; } .sheet { width: auto; } }
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
               "and letter/number recognition actually are. Each week's pair covers two different kinds "
               "of learning (e.g. one numeracy/literacy + one creative/cognitive) so it's never the same "
               "style twice in a row.")

    age_group = st.selectbox(
        "Which group are these worksheets for?",
        AGE_BANDS,
        key="worksheet_age_group",
    )
    if age_group in ("0-6 months", "6-12 months"):
        st.info("Babies don't complete worksheets independently — these are visual/sensory prompt cards for you to use with them.")

    theme_input = st.text_input(
        "This week's theme (type anything, e.g. 'yoga', 'space', 'farm animals')",
        key="worksheet_theme_text",
    )
    theme_key = match_theme(theme_input) if theme_input else None
    if theme_input and not theme_key:
        st.caption(
            "This isn't one of the pre-built themes — every activity will try to "
            "generate real pictures for it on the fly (first request for a new "
            "theme takes a little longer while it generates; after that it's "
            "cached and instant for everyone). "
            "Pre-built themes: " + ", ".join(THEME_DISPLAY[k] for k in THEME_DISPLAY)
        )
    elif theme_key:
        st.caption(f"Matched to: {THEME_DISPLAY[theme_key]}")

    week_key = get_week_key()
    week_index = get_week_index()

    # Keep only the latest worksheet per category for this week — a regenerate
    # replaces what's shown without losing older ones from the repeat-avoidance history.
    all_rows = get_worksheets_for_week(week_key, age_group)
    existing_by_cat = {}
    for w in all_rows:
        existing_by_cat[w["category"]] = w  # rows come oldest->newest, so last write wins

    regen_key = f"ws_regen_seed_{age_group}_{week_key}"
    seed_offset = st.session_state.get(regen_key, 0)
    target_categories = get_categories_for_week(week_index, age_group, n=2, seed_offset=seed_offset)
    # Guaranteed weekly inclusion — not left to compete for one of the 2
    # rotation slots above, since the whole point is it shows up every
    # single week (just with a different theme each time), not "some weeks".
    if "Themed Story Worksheet" in AGE_CATEGORIES[age_group] and "Themed Story Worksheet" not in target_categories:
        target_categories = target_categories + ["Themed Story Worksheet"]
    existing = [existing_by_cat[c] for c in target_categories if c in existing_by_cat]
    missing_categories = [c for c in target_categories if c not in existing_by_cat]

    st.markdown(f"**Week: {week_key}** — {len(existing)}/{len(target_categories)} ready for {age_group}")

    if not theme_input:
        st.warning("Type a theme above first — worksheets won't generate until you enter one.")
        return

    def _generate_categories(categories):
        feedback_text = get_latest_feedback(age_group)
        avoid_topics = get_recent_titles(age_group, lookback_weeks=8)
        for cat in categories:
            # Themed Story Worksheet uses the same manually-typed theme as
            # every other category now — no separate auto-rotation.
            theme_arg = theme_input
            avoid_items = get_recent_used_items(age_group, cat, lookback_weeks=8)
            ws = generate_worksheet(client, age_group, cat, theme_arg, avoid_topics, feedback_text, avoid_items)
            save_worksheet(week_key, age_group, cat, ws["title"], ws["html"], source="auto", used_items=ws["used_items"])
            avoid_topics.append(ws["title"])

    if missing_categories:
        st.info("Not all of this week's activities exist yet: " + ", ".join(missing_categories))
        if st.button("✨ Generate this week's worksheets", type="primary"):
            with st.spinner("Generating..."):
                _generate_categories(missing_categories)
            st.success("This week's activities are ready.")
            st.rerun()
    else:
        st.success("All of this week's activities are ready. ✅")
        if st.button("🔄 Get different ones for this week"):
            st.session_state[regen_key] = seed_offset + 1
            with st.spinner("Generating something different..."):
                new_targets = get_categories_for_week(week_index, age_group, n=2, seed_offset=seed_offset + 1)
                if "Themed Story Worksheet" in AGE_CATEGORIES[age_group] and "Themed Story Worksheet" not in new_targets:
                    new_targets = new_targets + ["Themed Story Worksheet"]
                _generate_categories(new_targets)
            st.rerun()

    if existing:
        st.markdown("#### This week's activities")
        for w in existing:
            with st.expander(f"{w['category']} — {w['title']}"):
                st.components.v1.html(w["html_content"], height=1000, scrolling=True)
                st.download_button(
                    "Download (HTML — open and print/save as PDF from your browser)",
                    data=w["html_content"],
                    file_name=f"{week_key}_{w['category'][:15]}.html",
                    mime="text/html",
                    key=f"dl_{w['id']}",
                )

    st.divider()
    st.markdown("#### Or request a specific activity")
    st.caption("Uses the theme entered above.")
    category_pool = AGE_CATEGORIES[age_group]
    # Default to a random category instead of always the first one in the list
    # (which used to mean it silently defaulted to "Letter Tracing" every time
    # unless you manually changed it) — picked once per age group per session,
    # not re-randomized on every rerun/click.
    default_key = f"manual_ws_default_{age_group}"
    if default_key not in st.session_state:
        st.session_state[default_key] = random.choice(category_pool)
    default_index = category_pool.index(st.session_state[default_key]) if st.session_state[default_key] in category_pool else 0
    manual_category = st.selectbox("Category", category_pool, index=default_index, key="manual_ws_category")
    if st.button("Generate this activity"):
        feedback_text = get_latest_feedback(age_group)
        avoid_topics = get_recent_titles(age_group, lookback_weeks=8)
        avoid_items = get_recent_used_items(age_group, manual_category, lookback_weeks=8)
        theme_arg = THEME_DISPLAY.get(theme_key, "") if theme_key else ""
        with st.spinner("Generating..."):
            ws = generate_worksheet(client, age_group, manual_category, theme_arg, avoid_topics, feedback_text, avoid_items)
            save_worksheet(week_key, age_group, manual_category, ws["title"], ws["html"], source="manual", used_items=ws["used_items"])
        st.session_state["manual_ws_result"] = ws

    if st.session_state.get("manual_ws_result"):
        ws = st.session_state["manual_ws_result"]
        st.success(f"Generated: {ws['title']}")
        st.components.v1.html(ws["html"], height=1000, scrolling=True)
        st.download_button(
            "Download (HTML — open and print/save as PDF from your browser)",
            data=ws["html"],
            file_name=f"{week_key}_{ws['category'][:15]}_manual.html",
            mime="text/html",
            key="dl_manual_ws",
        )

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