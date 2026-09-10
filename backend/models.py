from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from datetime import datetime, date as date_type
from database import Base


class Educator(Base):
    __tablename__ = "educators"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Child(Base):
    __tablename__ = "children"
    id = Column(Integer, primary_key=True, index=True)
    educator_id = Column(Integer, ForeignKey("educators.id"))
    name = Column(String, nullable=False)
    age_group = Column(String)
    interests = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Observation(Base):
    __tablename__ = "observations"
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"))
    obs_date = Column(Date)
    observation_text = Column(String)
    activity = Column(String)
    skill_note = Column(String)
    parent_note = Column(String)
    home_suggestion = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class QuickActivity(Base):
    __tablename__ = "quick_activities"
    id = Column(Integer, primary_key=True, index=True)
    age_group = Column(String, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class WeeklyExperience(Base):
    __tablename__ = "weekly_experiences"
    id = Column(Integer, primary_key=True, index=True)
    age_group = Column(String, nullable=False)
    week_key = Column(String, nullable=False)
    theme = Column(String)
    experience_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class HomeIdea(Base):
    __tablename__ = "home_ideas"
    id = Column(Integer, primary_key=True, index=True)
    idea_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class MagicTrick(Base):
    __tablename__ = "magic_tricks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age_group = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class IndependenceSkill(Base):
    __tablename__ = "independence_skills"
    id = Column(Integer, primary_key=True, index=True)
    age_group = Column(String, nullable=False)
    skill = Column(String, nullable=False)
    situation_description = Column(String)
    adapted_task = Column(String)
    related_game = Column(String)
    sensory_preskill = Column(String)
    try_duration = Column(String)
    outcome = Column(String)
    parent_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
