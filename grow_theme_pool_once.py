import os
from pathlib import Path
import tomllib

from openai import OpenAI
from worksheet_generator import THEME_LIBRARY
from image_gen import grow_theme_pool


# Load local Streamlit secrets
with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomllib.load(f)

groq_api_key = secrets["GROQ_API_KEY"]
openai_api_key = secrets["OPENAI_API_KEY"]

os.environ["GROQ_API_KEY"] = groq_api_key
os.environ["OPENAI_API_KEY"] = openai_api_key

client = OpenAI(
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)

theme_key = "yoga"
existing = list(THEME_LIBRARY[theme_key].keys())

prompt = (
    "List exactly 6 simple, concrete poses that fit the theme "
    "'Yoga / Movement poses for young children' and would work as "
    "a coloring-page picture for a 4-5 years early childhood worksheet. "
    f"Do NOT repeat any of these already-used ones: {', '.join(existing)}. "
    "One per line, 1-3 words each, no numbering, no extra text."
)

print("Existing yoga items:")
print(existing)
print("\nCalling Groq...\n")

resp = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=120,
)

print("RAW MODEL RESPONSE:")
print(repr(resp.choices[0].message.content))