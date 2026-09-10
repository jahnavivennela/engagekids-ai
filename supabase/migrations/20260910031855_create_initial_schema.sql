/*
# EngageKids AI — Initial Schema

## Overview
Creates the complete database schema for EngageKids AI, an early childhood
education platform. Supports educator accounts with multi-user data isolation.

## Tables Created
1. `children` — Educator's child profiles (name, age group, interests)
2. `observations` — Classroom observations linked to a child, with AI-generated skill notes, parent notes, and home suggestions
3. `learning_stories` — Narrative learning documentation per child
4. `quick_activities` — Saved quick activity suggestions
5. `magic_tricks` — Saved "magic trick" engagement ideas
6. `weekly_plans` — Weekly experience plans with experiences stored as JSON array
7. `worksheets` — Generated worksheets with theme, age group, and content
8. `home_messages` — Messages sent home to parents
9. `stories` — AI-generated stories for children
10. `independence_skills` — Independence skill milestones and tracking

## Security
- RLS enabled on ALL tables
- Owner-scoped CRUD: each authenticated educator can only access rows they own
- `user_id` columns default to `auth.uid()` so inserts work without explicit user_id
*/

-- 1. children
CREATE TABLE IF NOT EXISTS children (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  name text NOT NULL,
  age_group text,
  interests text,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE children ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_children" ON children;
CREATE POLICY "select_own_children" ON children FOR SELECT
  TO authenticated USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "insert_own_children" ON children;
CREATE POLICY "insert_own_children" ON children FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "update_own_children" ON children;
CREATE POLICY "update_own_children" ON children FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "delete_own_children" ON children;
CREATE POLICY "delete_own_children" ON children FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- 2. observations
CREATE TABLE IF NOT EXISTS observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  child_id uuid NOT NULL REFERENCES children(id) ON DELETE CASCADE,
  obs_date date DEFAULT CURRENT_DATE,
  observation_text text,
  activity text,
  skill_note text,
  parent_note text,
  home_suggestion text,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE observations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_observations" ON observations;
CREATE POLICY "select_own_observations" ON observations FOR SELECT
  TO authenticated USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "insert_own_observations" ON observations;
CREATE POLICY "insert_own_observations" ON observations FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "update_own_observations" ON observations;
CREATE POLICY "update_own_observations" ON observations FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "delete_own_observations" ON observations;
CREATE POLICY "delete_own_observations" ON observations FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- 3. learning_stories
CREATE TABLE IF NOT EXISTS learning_stories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  child_id uuid NOT NULL REFERENCES children(id) ON DELETE CASCADE,
  title text,
  story_text text,
  date_range text,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE learning_stories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_learning_stories" ON learning_stories;
CREATE POLICY "select_own_learning_stories" ON learning_stories FOR SELECT
  TO authenticated USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "insert_own_learning_stories" ON learning_stories;
CREATE POLICY "insert_own_learning_stories" ON learning_stories FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "update_own_learning_stories" ON learning_stories;
CREATE POLICY "update_own_learning_stories" ON learning_stories FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "delete_own_learning_stories" ON learning_stories;
CREATE POLICY "delete_own_learning_stories" ON learning_stories FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- 4. quick_activities
CREATE TABLE IF NOT EXISTS quick_activities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  child_id uuid REFERENCES children(id) ON DELETE SET NULL,
  activity_name text NOT NULL,
  description text,
  materials text,
  age_group text,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE quick_activities ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_quick_activities" ON quick_activities;
CREATE POLICY "select_own_quick_activities" ON quick_activities FOR SELECT
  TO authenticated USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "insert_own_quick_activities" ON quick_activities;
CREATE POLICY "insert_own_quick_activities" ON quick_activities FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "update_own_quick_activities" ON quick_activities;
CREATE POLICY "update_own_quick_activities" ON quick_activities FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "delete_own_quick_activities" ON quick_activities;
CREATE POLICY "delete_own_quick_activities" ON quick_activities FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- 5. magic_tricks
CREATE TABLE IF NOT EXISTS magic_tricks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  child_id uuid REFERENCES children(id) ON DELETE SET NULL,
  trick_name text NOT NULL,
  description text,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE magic_tricks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_magic_tricks" ON magic_tricks;
CREATE POLICY "select_own_magic_tricks" ON magic_tricks FOR SELECT
  TO authenticated USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "insert_own_magic_tricks" ON magic_tricks;
CREATE POLICY "insert_own_magic_tricks" ON magic_tricks FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "update_own_magic_tricks" ON magic_tricks;
CREATE POLICY "update_own_magic_tricks" ON magic_tricks FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "delete_own_magic_tricks" ON magic_tricks;
CREATE POLICY "delete_own_magic_tricks" ON magic_tricks FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- 6. weekly_plans
CREATE TABLE IF NOT EXISTS weekly_plans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  child_id uuid REFERENCES children(id) ON DELETE SET NULL,
  week_key text NOT NULL,
  theme text,
  experiences jsonb DEFAULT '[]'::jsonb,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE weekly_plans ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_weekly_plans" ON weekly_plans;
CREATE POLICY "select_own_weekly_plans" ON weekly_plans FOR SELECT
  TO authenticated USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "insert_own_weekly_plans" ON weekly_plans;
CREATE POLICY "insert_own_weekly_plans" ON weekly_plans FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "update_own_weekly_plans" ON weekly_plans;
CREATE POLICY "update_own_weekly_plans" ON weekly_plans FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "delete_own_weekly_plans" ON weekly_plans;
CREATE POLICY "delete_own_weekly_plans" ON weekly_plans FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- 7. worksheets
CREATE TABLE IF NOT EXISTS worksheets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  theme text NOT NULL,
  age_group text,
  content text,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE worksheets ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_worksheets" ON worksheets;
CREATE POLICY "select_own_worksheets" ON worksheets FOR SELECT
  TO authenticated USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "insert_own_worksheets" ON worksheets;
CREATE POLICY "insert_own_worksheets" ON worksheets FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "update_own_worksheets" ON worksheets;
CREATE POLICY "update_own_worksheets" ON worksheets FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "delete_own_worksheets" ON worksheets;
CREATE POLICY "delete_own_worksheets" ON worksheets FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- 8. home_messages
CREATE TABLE IF NOT EXISTS home_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  child_id uuid NOT NULL REFERENCES children(id) ON DELETE CASCADE,
  message_text text,
  message_date date DEFAULT CURRENT_DATE,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE home_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_home_messages" ON home_messages;
CREATE POLICY "select_own_home_messages" ON home_messages FOR SELECT
  TO authenticated USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "insert_own_home_messages" ON home_messages;
CREATE POLICY "insert_own_home_messages" ON home_messages FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "update_own_home_messages" ON home_messages;
CREATE POLICY "update_own_home_messages" ON home_messages FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "delete_own_home_messages" ON home_messages;
CREATE POLICY "delete_own_home_messages" ON home_messages FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- 9. stories
CREATE TABLE IF NOT EXISTS stories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  child_id uuid REFERENCES children(id) ON DELETE SET NULL,
  title text,
  story_text text,
  theme text,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE stories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_stories" ON stories;
CREATE POLICY "select_own_stories" ON stories FOR SELECT
  TO authenticated USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "insert_own_stories" ON stories;
CREATE POLICY "insert_own_stories" ON stories FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "update_own_stories" ON stories;
CREATE POLICY "update_own_stories" ON stories FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "delete_own_stories" ON stories;
CREATE POLICY "delete_own_stories" ON stories FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- 10. independence_skills
CREATE TABLE IF NOT EXISTS independence_skills (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  child_id uuid NOT NULL REFERENCES children(id) ON DELETE CASCADE,
  skill_name text NOT NULL,
  age_band text,
  status text DEFAULT 'emerging',
  notes text,
  observed_date date DEFAULT CURRENT_DATE,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE independence_skills ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "select_own_independence_skills" ON independence_skills;
CREATE POLICY "select_own_independence_skills" ON independence_skills FOR SELECT
  TO authenticated USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "insert_own_independence_skills" ON independence_skills;
CREATE POLICY "insert_own_independence_skills" ON independence_skills FOR INSERT
  TO authenticated WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "update_own_independence_skills" ON independence_skills;
CREATE POLICY "update_own_independence_skills" ON independence_skills FOR UPDATE
  TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "delete_own_independence_skills" ON independence_skills;
CREATE POLICY "delete_own_independence_skills" ON independence_skills FOR DELETE
  TO authenticated USING (auth.uid() = user_id);

-- Indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_children_user_id ON children(user_id);
CREATE INDEX IF NOT EXISTS idx_observations_child_id ON observations(child_id);
CREATE INDEX IF NOT EXISTS idx_observations_user_id ON observations(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_stories_child_id ON learning_stories(child_id);
CREATE INDEX IF NOT EXISTS idx_quick_activities_user_id ON quick_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_magic_tricks_user_id ON magic_tricks(user_id);
CREATE INDEX IF NOT EXISTS idx_weekly_plans_user_id ON weekly_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_worksheets_user_id ON worksheets(user_id);
CREATE INDEX IF NOT EXISTS idx_home_messages_child_id ON home_messages(child_id);
CREATE INDEX IF NOT EXISTS idx_stories_user_id ON stories(user_id);
CREATE INDEX IF NOT EXISTS idx_independence_skills_child_id ON independence_skills(child_id);