import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import type { Observation, Child, QuickActivity, LearningStory, Story } from '@/types';

export interface DashboardStats {
  childCount: number;
  observationCount: number;
  activityCount: number;
  storyCount: number;
  recentObservations: (Observation & { children: Pick<Child, 'name'> })[];
  recentStories: (Story & { children: Pick<Child, 'name'> | null })[];
}

export function useDashboardStats() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [childrenRes, obsRes, actRes, storiesRes] = await Promise.all([
        supabase.from('children').select('id', { count: 'exact', head: true }),
        supabase.from('observations').select('id', { count: 'exact', head: true }),
        supabase.from('quick_activities').select('id', { count: 'exact', head: true }),
        supabase.from('stories').select('id', { count: 'exact', head: true }),
      ]);

      const { data: recentObs } = await supabase
        .from('observations')
        .select('*, children(name)')
        .order('created_at', { ascending: false })
        .limit(5);

      const { data: recentStories } = await supabase
        .from('stories')
        .select('*, children(name)')
        .order('created_at', { ascending: false })
        .limit(3);

      setStats({
        childCount: childrenRes.count ?? 0,
        observationCount: obsRes.count ?? 0,
        activityCount: actRes.count ?? 0,
        storyCount: storiesRes.count ?? 0,
        recentObservations: (recentObs ?? []) as (Observation & { children: Pick<Child, 'name'> })[],
        recentStories: (recentStories ?? []) as (Story & { children: Pick<Child, 'name'> | null })[],
      });
      setLoading(false);
    }
    load();
  }, []);

  return { stats, loading };
}
