import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import type { Child } from '@/types';

export function useChildren() {
  const [children, setChildren] = useState<Child[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);

  const fetchChildren = useCallback(async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from('children')
      .select('*')
      .order('name');

    if (error) {
      console.error('Error fetching children:', error.message);
    } else {
      setChildren(data as Child[]);
      if (data && data.length > 0 && !selectedChildId) {
        setSelectedChildId(data[0].id);
      }
    }
    setLoading(false);
  }, [selectedChildId]);

  useEffect(() => {
    fetchChildren();
  }, [fetchChildren]);

  const selectedChild = children.find((c) => c.id === selectedChildId) ?? null;

  const addChild = async (
    name: string,
    ageGroup: string,
    interests: string
  ): Promise<{ error: string | null }> => {
    const { error } = await supabase
      .from('children')
      .insert({ name, age_group: ageGroup, interests });
    if (error) return { error: error.message };
    await fetchChildren();
    return { error: null };
  };

  const updateChild = async (
    id: string,
    updates: { name?: string; age_group?: string; interests?: string }
  ): Promise<{ error: string | null }> => {
    const { error } = await supabase.from('children').update(updates).eq('id', id);
    if (error) return { error: error.message };
    await fetchChildren();
    return { error: null };
  };

  const deleteChild = async (id: string): Promise<{ error: string | null }> => {
    const { error } = await supabase.from('children').delete().eq('id', id);
    if (error) return { error: error.message };
    if (selectedChildId === id) setSelectedChildId(null);
    await fetchChildren();
    return { error: null };
  };

  return {
    children,
    loading,
    selectedChild,
    selectedChildId,
    setSelectedChildId,
    addChild,
    updateChild,
    deleteChild,
    refresh: fetchChildren,
  };
}
