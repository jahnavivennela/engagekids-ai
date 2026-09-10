import { useState } from 'react';
import { BookText, Sparkles, Save, Loader2, Trash2 } from 'lucide-react';
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
import type { Story } from '@/types';

export function StoryTimePage() {
  const { children, selectedChildId, setSelectedChildId } = useChildren();
  const [theme, setTheme] = useState('');
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiResult, setAiResult] = useState<{ title: string; content: string } | null>(null);
  const [stories, setStories] = useState<(Story & { children: { name: string } | null })[]>([]);
  const [loadingList, setLoadingList] = useState(false);

  const fetchStories = async () => {
    setLoadingList(true);
    const { data, error } = await supabase
      .from('stories')
      .select('*, children(name)')
      .order('created_at', { ascending: false })
      .limit(10);
    if (!error && data) setStories(data as (Story & { children: { name: string } | null })[]);
    setLoadingList(false);
  };

  useState(() => { fetchStories(); });

  const handleGenerate = async () => {
    if (!theme.trim()) {
      setError('Please enter a story theme.');
      return;
    }
    setGenerating(true);
    setError(null);
    try {
      const child = children.find((c) => c.id === selectedChildId);
      const result = await generateAIContent('story', `Write a children's story about: ${theme}`, {
        child_name: child?.name ?? '',
        age_group: child?.age_group ?? '',
        interests: child?.interests ?? '',
        theme: theme,
      });
      setAiResult({
        title: result.title ?? 'A Wonderful Story',
        content: result.content ?? '',
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
    const { error: saveError } = await supabase.from('stories').insert({
      child_id: selectedChildId || null,
      title: aiResult.title,
      story_text: aiResult.content,
      theme: theme,
    });
    if (saveError) {
      setError(saveError.message);
    } else {
      setAiResult(null);
      setTheme('');
      fetchStories();
    }
    setSaving(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this story?')) return;
    const { error } = await supabase.from('stories').delete().eq('id', id);
    if (!error) fetchStories();
  };

  return (
    <div>
      <SectionHeader
        icon={<BookText size={20} />}
        title="Story Time"
        subtitle="Generate engaging, age-appropriate stories for children"
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
            <Input
              label="Story Theme"
              value={theme}
              onChange={setTheme}
              placeholder="e.g. A brave little star, or A dinosaur's first day at school"
              required
            />
            <Button variant="secondary" onClick={handleGenerate} disabled={generating || !theme.trim()}>
              {generating ? (
                <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Writing Story...</span>
              ) : (
                <span className="flex items-center gap-2"><Sparkles size={16} /> Generate Story</span>
              )}
            </Button>
          </div>
        </Card>

        {aiResult && (
          <Card className="border-[#E6A335]/30 animate-in fade-in duration-300">
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

        <div>
          <h3 className="font-bold text-stone-800 mb-3">Saved Stories</h3>
          {loadingList && <Card><p className="text-sm text-stone-400 text-center py-4">Loading...</p></Card>}
          {!loadingList && stories.length === 0 && (
            <Card><EmptyState icon={<BookText size={40} />} message="No stories saved yet." /></Card>
          )}
          {stories.length > 0 && (
            <div className="space-y-3">
              {stories.map((story) => (
                <Card key={story.id}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {story.children?.name && <Badge color="#E6A335">{story.children.name}</Badge>}
                        {story.theme && <Badge color="#6B5B95">{story.theme}</Badge>}
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
