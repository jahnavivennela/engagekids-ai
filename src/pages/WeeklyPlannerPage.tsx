import { useState } from 'react';
import { Calendar, Sparkles, Save, Loader2, Trash2 } from 'lucide-react';
import { useChildren } from '@/hooks/useChildren';
import { generateAIContent } from '@/lib/ai';
import { supabase } from '@/lib/supabase';
import {
  Card,
  SectionHeader,
  Button,
  Select,
  Input,
  ErrorBanner,
  EmptyState,
  Badge,
} from '@/components/ui';
import type { WeeklyPlan, ExperienceItem } from '@/types';

export function WeeklyPlannerPage() {
  const { children, selectedChildId, setSelectedChildId } = useChildren();
  const [theme, setTheme] = useState('');
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [experiences, setExperiences] = useState<ExperienceItem[]>([]);
  const [plans, setPlans] = useState<(WeeklyPlan & { children: { name: string } | null })[]>([]);
  const [loadingList, setLoadingList] = useState(false);

  const fetchPlans = async () => {
    setLoadingList(true);
    const { data, error } = await supabase
      .from('weekly_plans')
      .select('*, children(name)')
      .order('created_at', { ascending: false })
      .limit(10);
    if (!error && data) setPlans(data as (WeeklyPlan & { children: { name: string } | null })[]);
    setLoadingList(false);
  };

  useState(() => { fetchPlans(); });

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const child = children.find((c) => c.id === selectedChildId);
      const result = await generateAIContent(
        'weekly-planner',
        theme
          ? `Create a weekly plan with the theme: ${theme}`
          : 'Create a weekly experience plan for young children.',
        {
          child_name: child?.name ?? '',
          age_group: child?.age_group ?? '',
          interests: child?.interests ?? '',
          theme: theme,
        }
      );
      const generatedTheme = result.theme ?? theme ?? 'Weekly Theme';
      let parsedExperiences: ExperienceItem[] = [];
      try {
        const raw = result.experiences;
        if (typeof raw === 'string') {
          parsedExperiences = JSON.parse(raw) as ExperienceItem[];
        } else if (Array.isArray(raw)) {
          parsedExperiences = raw as ExperienceItem[];
        }
      } catch {
        parsedExperiences = [];
      }
      setTheme(generatedTheme);
      setExperiences(parsedExperiences);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI generation failed');
    }
    setGenerating(false);
  };

  const handleSave = async () => {
    if (experiences.length === 0) return;
    setSaving(true);
    setError(null);
    const weekKey = new Date().toISOString().slice(0, 10);
    const { error: saveError } = await supabase.from('weekly_plans').insert({
      child_id: selectedChildId || null,
      week_key: weekKey,
      theme: theme,
      experiences: experiences,
    });
    if (saveError) {
      setError(saveError.message);
    } else {
      setExperiences([]);
      setTheme('');
      fetchPlans();
    }
    setSaving(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this weekly plan?')) return;
    const { error } = await supabase.from('weekly_plans').delete().eq('id', id);
    if (!error) fetchPlans();
  };

  const updateExperience = (index: number, value: string) => {
    setExperiences((prev) =>
      prev.map((e, i) => (i === index ? { ...e, experience: value } : e))
    );
  };

  return (
    <div>
      <SectionHeader
        icon={<Calendar size={20} />}
        title="Weekly Planner"
        subtitle="Plan a week of engaging, play-based experiences"
        color="#2F5EA8"
      />

      {error && <div className="mb-4"><ErrorBanner message={error} /></div>}

      <div className="space-y-4">
        <Card>
          <div className="space-y-4">
            <Select
              label="Child (optional)"
              value={selectedChildId ?? ''}
              onChange={setSelectedChildId}
              placeholder="No specific child"
              options={children.map((c) => ({ value: c.id, label: `${c.name} (${c.age_group ?? '—'})` }))}
            />
            <Input
              label="Theme (optional)"
              value={theme}
              onChange={setTheme}
              placeholder="e.g. Colors All Around, or leave blank for AI to choose"
            />
            <Button onClick={handleGenerate} disabled={generating}>
              {generating ? (
                <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Planning Week...</span>
              ) : (
                <span className="flex items-center gap-2"><Sparkles size={16} /> Generate Weekly Plan</span>
              )}
            </Button>
          </div>
        </Card>

        {experiences.length > 0 && (
          <Card className="border-[#2F5EA8]/30 animate-in fade-in duration-300">
            <div className="flex items-center gap-2 mb-4">
              <Badge color="#2F5EA8">Theme: {theme}</Badge>
            </div>
            <div className="space-y-3">
              {experiences.map((exp, i) => (
                <div key={i} className="flex gap-3 items-start">
                  <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-[#2F5EA8]/10 text-[#2F5EA8] font-bold text-xs flex-shrink-0">
                    {exp.day?.slice(0, 3) ?? `Day ${i + 1}`}
                  </div>
                  <textarea
                    value={exp.experience}
                    onChange={(e) => updateExperience(i, e.target.value)}
                    rows={2}
                    className="flex-1 px-3 py-2 rounded-lg border border-stone-300 bg-white text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-[#2F5EA8]/30 resize-y"
                  />
                </div>
              ))}
            </div>
            <div className="mt-4">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? (
                  <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Saving...</span>
                ) : (
                  <span className="flex items-center gap-2"><Save size={16} /> Save Weekly Plan</span>
                )}
              </Button>
            </div>
          </Card>
        )}

        <div>
          <h3 className="font-bold text-stone-800 mb-3">Saved Weekly Plans</h3>
          {loadingList && <Card><p className="text-sm text-stone-400 text-center py-4">Loading...</p></Card>}
          {!loadingList && plans.length === 0 && (
            <Card><EmptyState icon={<Calendar size={40} />} message="No weekly plans saved yet." /></Card>
          )}
          {plans.length > 0 && (
            <div className="space-y-3">
              {plans.map((plan) => (
                <Card key={plan.id}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge color="#2F5EA8">{plan.theme ?? 'No theme'}</Badge>
                        {plan.children?.name && <Badge color="#E6A335">{plan.children.name}</Badge>}
                        <Badge color="#4C8B6B">{plan.week_key}</Badge>
                      </div>
                      <div className="space-y-1">
                        {(plan.experiences ?? []).slice(0, 3).map((exp, i) => (
                          <p key={i} className="text-sm text-stone-600">
                            <span className="font-medium text-stone-700">{exp.day}:</span> {exp.experience}
                          </p>
                        ))}
                        {(plan.experiences ?? []).length > 3 && (
                          <p className="text-xs text-stone-400">+ {(plan.experiences ?? []).length - 3} more days</p>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(plan.id)}
                      className="p-1.5 rounded-lg hover:bg-red-50 text-stone-400 hover:text-red-500 transition-colors flex-shrink-0"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
