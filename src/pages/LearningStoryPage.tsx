import { useState } from 'react';
import { BookMarked, Sparkles, Save, Loader2, Trash2 } from 'lucide-react';
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
import type { LearningStory } from '@/types';

export function LearningStoryPage() {
  const { children, selectedChildId, setSelectedChildId } = useChildren();
  const [dateRange, setDateRange] = useState('');
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiResult, setAiResult] = useState<{ title: string; content: string } | null>(null);
  const [stories, setStories] = useState<(LearningStory & { children: { name: string } | null })[]>([]);
  const [loadingStories, setLoadingStories] = useState(false);

  const fetchStories = async () => {
    setLoadingStories(true);
    const { data, error } = await supabase
      .from('learning_stories')
      .select('*, children(name)')
      .order('created_at', { ascending: false })
      .limit(10);
    if (!error && data) setStories(data as (LearningStory & { children: { name: string } | null })[]);
    setLoadingStories(false);
  };

  // Load stories on mount
  useState(() => {
    fetchStories();
  });

  const handleGenerate = async () => {
    if (!selectedChildId) {
      setError('Please select a child first.');
      return;
    }
    setGenerating(true);
    setError(null);
    try {
      const child = children.find((c) => c.id === selectedChildId);
      const { data: obsData } = await supabase
        .from('observations')
        .select('observation_text, activity, skill_note, obs_date')
        .eq('child_id', selectedChildId)
        .order('obs_date', { ascending: false })
        .limit(10);

      const obsText = (obsData ?? [])
        .map((o) => `- ${o.obs_date}: ${o.observation_text ?? ''} (Activity: ${o.activity ?? 'N/A'})`)
        .join('\n');

      const result = await generateAIContent(
        'learning-story',
        `Create a learning story for ${child?.name ?? 'this child'}.`,
        {
          child_name: child?.name ?? '',
          age_group: child?.age_group ?? '',
          interests: child?.interests ?? '',
          date_range: dateRange,
          recent_observations: obsText || 'No recent observations recorded yet.',
        }
      );
      setAiResult({
        title: result.title ?? `${child?.name}'s Learning Story`,
        content: result.content ?? '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI generation failed');
    }
    setGenerating(false);
  };

  const handleSave = async () => {
    if (!selectedChildId || !aiResult) return;
    setSaving(true);
    setError(null);
    const { error: saveError } = await supabase.from('learning_stories').insert({
      child_id: selectedChildId,
      title: aiResult.title,
      story_text: aiResult.content,
      date_range: dateRange,
    });
    if (saveError) {
      setError(saveError.message);
    } else {
      setAiResult(null);
      setDateRange('');
      fetchStories();
    }
    setSaving(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this learning story?')) return;
    const { error } = await supabase.from('learning_stories').delete().eq('id', id);
    if (!error) fetchStories();
  };

  if (children.length === 0) {
    return (
      <div>
        <SectionHeader icon={<BookMarked size={20} />} title="Learning Story" subtitle="Generate narrative learning documentation" color="#4C8B6B" />
        <Card><EmptyState icon={<BookMarked size={48} />} message="Add a child first to create learning stories." /></Card>
      </div>
    );
  }

  return (
    <div>
      <SectionHeader
        icon={<BookMarked size={20} />}
        title="Learning Story"
        subtitle="Generate a warm, professional learning story from observations"
        color="#4C8B6B"
      />

      {error && <div className="mb-4"><ErrorBanner message={error} /></div>}

      <div className="space-y-4">
        <Card>
          <div className="space-y-4">
            <Select
              label="Select Child"
              value={selectedChildId ?? ''}
              onChange={setSelectedChildId}
              required
              placeholder="Choose a child"
              options={children.map((c) => ({ value: c.id, label: `${c.name} (${c.age_group ?? '—'})` }))}
            />
            <Input
              label="Date Range (optional)"
              value={dateRange}
              onChange={setDateRange}
              placeholder="e.g. March 2026 or Weeks 1-4"
            />
            <Button variant="secondary" onClick={handleGenerate} disabled={generating || !selectedChildId}>
              {generating ? (
                <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Generating Story...</span>
              ) : (
                <span className="flex items-center gap-2"><Sparkles size={16} /> Generate Learning Story</span>
              )}
            </Button>
          </div>
        </Card>

        {aiResult && (
          <Card className="border-[#4C8B6B]/30 animate-in fade-in duration-300">
            <h3 className="text-lg font-bold text-stone-800 mb-3">{aiResult.title}</h3>
            <div className="prose prose-sm max-w-none">
              <p className="text-sm text-stone-700 whitespace-pre-wrap leading-relaxed">{aiResult.content}</p>
            </div>
            <div className="mt-4">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? (
                  <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Saving...</span>
                ) : (
                  <span className="flex items-center gap-2"><Save size={16} /> Save Story</span>
                )}
              </Button>
            </div>
          </Card>
        )}

        {/* Saved stories */}
        <div>
          <h3 className="font-bold text-stone-800 mb-3">Saved Learning Stories</h3>
          {loadingStories && <Card><p className="text-sm text-stone-400 text-center py-4">Loading...</p></Card>}
          {!loadingStories && stories.length === 0 && (
            <Card><EmptyState icon={<BookMarked size={40} />} message="No learning stories saved yet." /></Card>
          )}
          {stories.length > 0 && (
            <div className="space-y-3">
              {stories.map((story) => (
                <Card key={story.id}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge color="#4C8B6B">{story.children?.name ?? '—'}</Badge>
                        {story.date_range && <Badge color="#2F5EA8">{story.date_range}</Badge>}
                      </div>
                      <h4 className="font-bold text-stone-800 mb-1">{story.title}</h4>
                      <p className="text-sm text-stone-600 line-clamp-3">{story.story_text}</p>
                    </div>
                    <button
                      onClick={() => handleDelete(story.id)}
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
