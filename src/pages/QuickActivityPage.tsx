import { useState } from 'react';
import { Zap, Sparkles, Save, Loader2, Trash2 } from 'lucide-react';
import { useChildren } from '@/hooks/useChildren';
import { generateAIContent } from '@/lib/ai';
import { supabase } from '@/lib/supabase';
import { AGE_GROUPS } from '@/lib/theme';
import {
  Card,
  SectionHeader,
  Button,
  Select,
  TextArea,
  Input,
  ErrorBanner,
  EmptyState,
  Badge,
} from '@/components/ui';
import type { QuickActivity } from '@/types';

export function QuickActivityPage() {
  const { children, selectedChildId, setSelectedChildId } = useChildren();
  const [ageGroup, setAgeGroup] = useState('');
  const [situation, setSituation] = useState('');
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiResult, setAiResult] = useState<{
    activity_name: string;
    description: string;
    materials: string;
  } | null>(null);
  const [activities, setActivities] = useState<(QuickActivity & { children: { name: string } | null })[]>([]);
  const [loadingList, setLoadingList] = useState(false);

  const fetchActivities = async () => {
    setLoadingList(true);
    const { data, error } = await supabase
      .from('quick_activities')
      .select('*, children(name)')
      .order('created_at', { ascending: false })
      .limit(10);
    if (!error && data) setActivities(data as (QuickActivity & { children: { name: string } | null })[]);
    setLoadingList(false);
  };

  useState(() => { fetchActivities(); });

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const child = children.find((c) => c.id === selectedChildId);
      const result = await generateAIContent(
        'quick-activity',
        situation || 'Generate a quick 5-minute engaging activity for young children.',
        {
          child_name: child?.name ?? '',
          age_group: ageGroup || child?.age_group || '',
          interests: child?.interests ?? '',
          situation: situation,
        }
      );
      setAiResult({
        activity_name: result.activity_name ?? 'Quick Activity',
        description: result.description ?? '',
        materials: result.materials ?? '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI generation failed');
    }
    setGenerating(false);
  };

  const handleSave = async () => {
    if (!aiResult) return;
    setSaving(true);
    setError(null);
    const { error: saveError } = await supabase.from('quick_activities').insert({
      child_id: selectedChildId || null,
      activity_name: aiResult.activity_name,
      description: aiResult.description,
      materials: aiResult.materials,
      age_group: ageGroup,
    });
    if (saveError) {
      setError(saveError.message);
    } else {
      setAiResult(null);
      setSituation('');
      fetchActivities();
    }
    setSaving(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this activity?')) return;
    const { error } = await supabase.from('quick_activities').delete().eq('id', id);
    if (!error) fetchActivities();
  };

  return (
    <div>
      <SectionHeader
        icon={<Zap size={20} />}
        title="Quick Activity"
        subtitle="Generate a 5-minute engaging activity for any moment"
        color="#E6A335"
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
            <Select
              label="Age Group (optional)"
              value={ageGroup}
              onChange={setAgeGroup}
              placeholder="Select age group"
              options={AGE_GROUPS.map((g) => ({ value: g, label: g }))}
            />
            <TextArea
              label="Situation (optional)"
              value={situation}
              onChange={setSituation}
              placeholder="e.g. Need something calming before nap time, or The kids have lots of energy today"
              rows={2}
            />
            <Button variant="secondary" onClick={handleGenerate} disabled={generating}>
              {generating ? (
                <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Generating Activity...</span>
              ) : (
                <span className="flex items-center gap-2"><Sparkles size={16} /> Generate Activity</span>
              )}
            </Button>
          </div>
        </Card>

        {aiResult && (
          <Card className="border-[#E6A335]/30 animate-in fade-in duration-300">
            <h3 className="text-lg font-bold text-stone-800 mb-2">{aiResult.activity_name}</h3>
            {aiResult.materials && (
              <div className="mb-3">
                <Badge color="#2F5EA8">Materials: {aiResult.materials}</Badge>
              </div>
            )}
            <p className="text-sm text-stone-700 whitespace-pre-wrap leading-relaxed">{aiResult.description}</p>
            <div className="mt-4">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? (
                  <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Saving...</span>
                ) : (
                  <span className="flex items-center gap-2"><Save size={16} /> Save Activity</span>
                )}
              </Button>
            </div>
          </Card>
        )}

        <div>
          <h3 className="font-bold text-stone-800 mb-3">Saved Activities</h3>
          {loadingList && <Card><p className="text-sm text-stone-400 text-center py-4">Loading...</p></Card>}
          {!loadingList && activities.length === 0 && (
            <Card><EmptyState icon={<Zap size={40} />} message="No activities saved yet." /></Card>
          )}
          {activities.length > 0 && (
            <div className="space-y-3">
              {activities.map((act) => (
                <Card key={act.id}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {act.children?.name && <Badge color="#E6A335">{act.children.name}</Badge>}
                        {act.age_group && <Badge color="#2F5EA8">{act.age_group}</Badge>}
                      </div>
                      <h4 className="font-bold text-stone-800 mb-1">{act.activity_name}</h4>
                      <p className="text-sm text-stone-600 line-clamp-2">{act.description}</p>
                      {act.materials && (
                        <p className="text-xs text-stone-400 mt-1">Materials: {act.materials}</p>
                      )}
                    </div>
                    <button
                      onClick={() => handleDelete(act.id)}
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
