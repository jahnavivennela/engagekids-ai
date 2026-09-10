import { useState } from 'react';
import { Sparkles as SparklesIcon, Save, Loader2, Trash2, Wand2 } from 'lucide-react';
import { useChildren } from '@/hooks/useChildren';
import { generateAIContent } from '@/lib/ai';
import { supabase } from '@/lib/supabase';
import {
  Card,
  SectionHeader,
  Button,
  Select,
  TextArea,
  ErrorBanner,
  EmptyState,
  Badge,
} from '@/components/ui';
import type { MagicTrick } from '@/types';

export function MagicTrickPage() {
  const { children, selectedChildId, setSelectedChildId } = useChildren();
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiResult, setAiResult] = useState<{ trick_name: string; description: string } | null>(null);
  const [tricks, setTricks] = useState<(MagicTrick & { children: { name: string } | null })[]>([]);
  const [loadingList, setLoadingList] = useState(false);

  const fetchTricks = async () => {
    setLoadingList(true);
    const { data, error } = await supabase
      .from('magic_tricks')
      .select('*, children(name)')
      .order('created_at', { ascending: false })
      .limit(10);
    if (!error && data) setTricks(data as (MagicTrick & { children: { name: string } | null })[]);
    setLoadingList(false);
  };

  useState(() => { fetchTricks(); });

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const child = children.find((c) => c.id === selectedChildId);
      const result = await generateAIContent(
        'magic-trick',
        prompt || 'Create a fun magic trick activity for young children.',
        {
          child_name: child?.name ?? '',
          age_group: child?.age_group ?? '',
          interests: child?.interests ?? '',
          prompt: prompt,
        }
      );
      setAiResult({
        trick_name: result.trick_name ?? 'Magic Trick',
        description: result.description ?? '',
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
    const { error: saveError } = await supabase.from('magic_tricks').insert({
      child_id: selectedChildId || null,
      trick_name: aiResult.trick_name,
      description: aiResult.description,
    });
    if (saveError) {
      setError(saveError.message);
    } else {
      setAiResult(null);
      setPrompt('');
      fetchTricks();
    }
    setSaving(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this magic trick?')) return;
    const { error } = await supabase.from('magic_tricks').delete().eq('id', id);
    if (!error) fetchTricks();
  };

  return (
    <div>
      <SectionHeader
        icon={<Wand2 size={20} />}
        title="Magic Trick"
        subtitle="Spark wonder with a fun, surprising activity for children"
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
            <TextArea
              label="What kind of magic? (optional)"
              value={prompt}
              onChange={setPrompt}
              placeholder="e.g. Something with water, or a disappearing trick, or Based on dinosaurs"
              rows={2}
            />
            <Button variant="secondary" onClick={handleGenerate} disabled={generating}>
              {generating ? (
                <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Conjurating...</span>
              ) : (
                <span className="flex items-center gap-2"><SparklesIcon size={16} /> Generate Magic Trick</span>
              )}
            </Button>
          </div>
        </Card>

        {aiResult && (
          <Card className="border-[#E6A335]/30 animate-in fade-in duration-300">
            <div className="flex items-center gap-2 mb-2">
              <SparklesIcon size={18} className="text-[#E6A335]" />
              <h3 className="text-lg font-bold text-stone-800">{aiResult.trick_name}</h3>
            </div>
            <p className="text-sm text-stone-700 whitespace-pre-wrap leading-relaxed">{aiResult.description}</p>
            <div className="mt-4">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? (
                  <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Saving...</span>
                ) : (
                  <span className="flex items-center gap-2"><Save size={16} /> Save Magic Trick</span>
                )}
              </Button>
            </div>
          </Card>
        )}

        <div>
          <h3 className="font-bold text-stone-800 mb-3">Saved Magic Tricks</h3>
          {loadingList && <Card><p className="text-sm text-stone-400 text-center py-4">Loading...</p></Card>}
          {!loadingList && tricks.length === 0 && (
            <Card><EmptyState icon={<Wand2 size={40} />} message="No magic tricks saved yet." /></Card>
          )}
          {tricks.length > 0 && (
            <div className="space-y-3">
              {tricks.map((trick) => (
                <Card key={trick.id}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      {trick.children?.name && (
                        <div className="mb-1"><Badge color="#E6A335">{trick.children.name}</Badge></div>
                      )}
                      <h4 className="font-bold text-stone-800 mb-1">{trick.trick_name}</h4>
                      <p className="text-sm text-stone-600 line-clamp-2">{trick.description}</p>
                    </div>
                    <button
                      onClick={() => handleDelete(trick.id)}
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
