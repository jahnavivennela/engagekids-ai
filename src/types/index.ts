export interface Child {
  id: string;
  user_id: string;
  name: string;
  age_group: string | null;
  interests: string | null;
  created_at: string;
}

export interface Observation {
  id: string;
  user_id: string;
  child_id: string;
  obs_date: string;
  observation_text: string | null;
  activity: string | null;
  skill_note: string | null;
  parent_note: string | null;
  home_suggestion: string | null;
  created_at: string;
}

export interface LearningStory {
  id: string;
  user_id: string;
  child_id: string;
  title: string | null;
  story_text: string | null;
  date_range: string | null;
  created_at: string;
}

export interface QuickActivity {
  id: string;
  user_id: string;
  child_id: string | null;
  activity_name: string;
  description: string | null;
  materials: string | null;
  age_group: string | null;
  created_at: string;
}

export interface MagicTrick {
  id: string;
  user_id: string;
  child_id: string | null;
  trick_name: string;
  description: string | null;
  created_at: string;
}

export interface WeeklyPlan {
  id: string;
  user_id: string;
  child_id: string | null;
  week_key: string;
  theme: string | null;
  experiences: ExperienceItem[];
  created_at: string;
}

export interface ExperienceItem {
  day: string;
  experience: string;
}

export interface Worksheet {
  id: string;
  user_id: string;
  theme: string;
  age_group: string | null;
  content: string | null;
  created_at: string;
}

export interface HomeMessage {
  id: string;
  user_id: string;
  child_id: string;
  message_text: string | null;
  message_date: string;
  created_at: string;
}

export interface Story {
  id: string;
  user_id: string;
  child_id: string | null;
  title: string | null;
  story_text: string | null;
  theme: string | null;
  created_at: string;
}

export interface IndependenceSkill {
  id: string;
  user_id: string;
  child_id: string;
  skill_name: string;
  age_band: string | null;
  status: string;
  notes: string | null;
  observed_date: string;
  created_at: string;
}

export type PageId =
  | 'dashboard'
  | 'children'
  | 'observation'
  | 'history'
  | 'learning-story'
  | 'quick-activity'
  | 'magic-trick'
  | 'weekly-planner'
  | 'worksheets'
  | 'home-message'
  | 'story-time'
  | 'independence-skills';

export interface AIGenerationResult {
  content: string;
  [key: string]: string;
}
