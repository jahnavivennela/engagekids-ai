from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from datetime import date
from ai_client import client
from milestones_data import milestones_summary_text
import re as regex_module

from database import get_db

from auth import hash_password, verify_password, create_access_token
from fastapi.middleware.cors import CORSMiddleware
from models import Educator, Child, Observation, QuickActivity, WeeklyExperience, HomeIdea, MagicTrick


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------- Request models ----------

class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ChildRequest(BaseModel):
    educator_id: int
    name: str
    age_group: str = None
    interests: str = None

class ObservationRequest(BaseModel):
    child_id: int
    obs_date: date = None
    observation_text: str = ""
    activity: str = ""
    skill_note: str = ""
    parent_note: str = ""
    home_suggestion: str = ""

class QuickActivityGenerateRequest(BaseModel):
    age_group: str = None
    is_mixed: bool = False
    age_groups: list[str] = []
    mood: str
    materials: str = ""

class HomeMessageGenerateRequest(BaseModel):
    activity_or_theme: str
    languages: list[str] = []


# ---------- Basic / test routes ----------

@app.get("/")
def root():
    return {"message": "EngageKids AI backend is running"}

@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT COUNT(*) FROM children"))
    return {"children_count": result.scalar()}


# ---------- Auth ----------

@app.post("/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(Educator).filter(Educator.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_educator = Educator(email=data.email, hashed_password=hash_password(data.password))
    db.add(new_educator)
    db.commit()
    db.refresh(new_educator)
    return {"message": "Signup successful", "educator_id": new_educator.id}

@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    educator = db.query(Educator).filter(Educator.email == data.email).first()
    if not educator or not verify_password(data.password, educator.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": str(educator.id)})
    return {"access_token": token, "token_type": "bearer"}


# ---------- Children ----------

@app.post("/children")
def add_child(data: ChildRequest, db: Session = Depends(get_db)):
    new_child = Child(
        educator_id=data.educator_id,
        name=data.name,
        age_group=data.age_group,
        interests=data.interests
    )
    db.add(new_child)
    db.commit()
    db.refresh(new_child)
    return {"message": "Child added", "child_id": new_child.id}

@app.get("/children/{educator_id}")
def get_children(educator_id: int, db: Session = Depends(get_db)):
    return db.query(Child).filter(Child.educator_id == educator_id).all()

@app.get("/child/{child_id}")
def get_child(child_id: int, db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


# ---------- Observations ----------

@app.post("/observations")
def add_observation(data: ObservationRequest, db: Session = Depends(get_db)):
    new_obs = Observation(
        child_id=data.child_id,
        obs_date=data.obs_date or date.today(),
        observation_text=data.observation_text,
        activity=data.activity,
        skill_note=data.skill_note,
        parent_note=data.parent_note,
        home_suggestion=data.home_suggestion,
    )
    db.add(new_obs)
    db.commit()
    db.refresh(new_obs)
    return {"message": "Observation saved", "observation_id": new_obs.id}

@app.get("/observations/{child_id}")
def get_observations(child_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Observation)
        .filter(Observation.child_id == child_id)
        .order_by(Observation.obs_date.desc(), Observation.id.desc())
        .all()
    )

@app.get("/observations/{child_id}/latest")
def get_latest_observation(child_id: int, db: Session = Depends(get_db)):
    obs = (
        db.query(Observation)
        .filter(Observation.child_id == child_id)
        .order_by(Observation.obs_date.desc(), Observation.id.desc())
        .first()
    )
    if not obs:
        raise HTTPException(status_code=404, detail="No observations found")
    return obs


def extract_activity_name(result_text: str) -> str:
    if not result_text or not result_text.strip():
        return "Quick Activity"
    lines = result_text.splitlines()
    if not lines:
        return "Quick Activity"
    first_line = lines[0].strip()
    if first_line.upper().startswith("ACTIVITY:"):
        return first_line.split(":", 1)[1].strip()
    return first_line


@app.post("/generate-quick-activity")
def generate_quick_activity(data: QuickActivityGenerateRequest, db: Session = Depends(get_db)):
    materials_line = (
        f"Materials available — use ONLY these (or nothing): {data.materials.strip()}"
        if data.materials.strip()
        else "No specific materials on hand — keep it to 0-1 common items, or none at all."
    )

    if data.is_mixed:
        if not data.age_groups or len(data.age_groups) < 2:
            raise HTTPException(status_code=400, detail="Select at least two age groups for a mixed-age suggestion.")

        age_group_key = "MIXED:" + "+".join(sorted(data.age_groups))
        recent = (
            db.query(QuickActivity)
            .filter(QuickActivity.age_group == age_group_key)
            .order_by(QuickActivity.created_at.desc())
            .limit(60)
            .all()
        )
        avoid_names = [r.name for r in recent]

        # TODO: milestones_block needs milestones_data.py — placeholder for now
        milestones_block = "\n\n".join(f"{band}:\n{milestones_summary_text(band)}" for band in data.age_groups)

        system_prompt = (
            "You suggest VERY QUICK, dead-simple filler activities for a MIXED-AGE group of "
            "children (e.g. a before/after-care room combining several age bands) to re-engage them "
            "for a few minutes when an educator is busy, tired, or between planned activities. This is "
            "NOT a structured learning experience — no EYLF write-up, no elaborate setup. The SAME core "
            "activity must work for every age band listed, with only the level of challenge or the way "
            "each age group takes part changing. Do not invent skills beyond the milestones given. "
            "Flag a supervision/safety note whenever infants or young toddlers are being combined with "
            "older, more physically active children."
        )
        prompt = f"""Age groups present: {", ".join(data.age_groups)}
Developmental milestones for each age group (base the activity on these):
{milestones_block}

Mood right now: {data.mood}
{materials_line}
{"Activities already used recently for this exact combination of ages — do NOT repeat any of these: " + "; ".join(avoid_names) if avoid_names else ""}

Give ONE very quick activity that the whole mixed-age group can do together at the same time, genuinely different from the ones listed above. Reply in EXACTLY this format, nothing else:
ACTIVITY: <name>
HOW: <one plain sentence describing the shared core activity>
FOR EACH AGE: <one short line per age group, format "AGE_BAND — how they take part/what's adapted">
MATERIALS: <based on what's available, or 'None needed'>
SAFETY: <one line supervision/safety note if mixing very young and older children, otherwise 'None needed'>"""
    else:
        age_group_key = data.age_group
        recent = (
            db.query(QuickActivity)
            .filter(QuickActivity.age_group == age_group_key)
            .order_by(QuickActivity.created_at.desc())
            .limit(60)
            .all()
        )
        avoid_names = [r.name for r in recent]

        # TODO: milestones_data.py needed for the real milestones text
        milestones_text = milestones_summary_text(data.age_group)

        system_prompt = (
            "You suggest VERY QUICK, dead-simple filler activities to re-engage a group of children "
            "for a few minutes when an educator is busy, tired, or between planned activities. This is "
            "NOT a structured learning experience — no EYLF write-up, no elaborate setup. Base it only "
            "on what's realistic for this age using the milestones given — do not invent skills beyond "
            "them."
        )
        prompt = f"""Age group: {data.age_group}
Developmental milestones for this age (base the activity on these):
{milestones_text}

Mood right now: {data.mood}
{materials_line}
{"Activities already used recently for this age group — do NOT repeat any of these: " + "; ".join(avoid_names) if avoid_names else ""}

Give ONE very quick activity, genuinely different from the ones listed above. Reply in EXACTLY this format, nothing else:
ACTIVITY: <name>
HOW: <one plain sentence>
MATERIALS: <based on what's available, or 'None needed'>"""

    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        max_tokens=400,
        reasoning_effort="low",
    )
    result_text = resp.choices[0].message.content.strip()

    new_item = QuickActivity(age_group=age_group_key, name=extract_activity_name(result_text))
    db.add(new_item)
    db.commit()

    return {"result": result_text}


@app.post("/generate-home-message")
def generate_home_message(data: HomeMessageGenerateRequest, db: Session = Depends(get_db)):
    recent = db.query(HomeIdea).order_by(HomeIdea.created_at.desc()).limit(60).all()
    avoid_ideas = [r.idea_text for r in recent]
    avoid_text = (
        "Ideas already sent to families in the last ~2-3 months — do NOT repeat any of these, "
        "come up with genuinely different ones: " + "; ".join(avoid_ideas)
    ) if avoid_ideas else ""

    home_prompt = f"""Today's group activity/theme: {data.activity_or_theme}

Write a SHORT, GENERIC message for early childhood educators to copy-paste and send to ALL families in
the room — do not use any child's name or personalise it to one child. Format:

MESSAGE:
1-2 sentence intro about today's activity/theme, written generically for the whole group.

TRY AT HOME (3 ideas):
Three short, simple ideas any parent could do THAT SAME EVENING using ONLY things already in a typical
home — kitchen items (bowls, spoons, cups, pasta, rice), laundry items (socks, pegs, baskets), bathroom
items, or general household objects (cushions, blankets, boxes already lying around). Do NOT suggest
anything a parent would need to buy or source specially (no craft-store items, no printables). For each
idea, on the line right after it, add "Skill: <one short plain-language phrase>" naming the skill it
builds, so it reads like:
1. <idea>
   Skill: <skill>
2. <idea>
   Skill: <skill>
3. <idea>
   Skill: <skill>

{avoid_text}

{"Also translate the MESSAGE section into: " + ", ".join(data.languages) if data.languages else ""}
"""
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You write short, warm, generic educator-to-parent messages for early childhood centres. Never personalise to a specific child. 'Try at home' ideas must use only ordinary things already found around a home — never anything to purchase."},
            {"role": "user", "content": home_prompt},
        ],
    )
    result_text = resp.choices[0].message.content

    idea_lines = [
        regex_module.sub(r"^\s*\d+[\.\)]\s*", "", line).strip()
        for line in result_text.splitlines()
        if regex_module.match(r"^\s*\d+[\.\)]", line)
    ]
    for idea in idea_lines:
        if idea.strip():
            db.add(HomeIdea(idea_text=idea.strip()))
    db.commit()

    return {"result": result_text}