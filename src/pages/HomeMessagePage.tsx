import { useState } from 'react';
import { Home, Sparkles, Save, Loader2, Trash2 } from 'lucide-react';
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
import type { HomeMessage } from '@/types';

export function HomeMessagePage() {
  const { children, selectedChildId, setSelectedChildId } = useChildren();
  const [context, setContext] = useState('');
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiResult, setAiResult] = useState<string | null>(null);
  const [messages, setMessages] = useState<(HomeMessage & { children: { name: string } })[]>([]);
  const [loadingList, setLoadingList] = useState(false);

  const fetchMessages = async () => {
    setLoadingList(true);
    const { data, error } = await supabase
      .from('home_messages')
      .select('*, children(name)')
      .order('created_at', { ascending: false })
      .limit(10);
    if (!error && data) setMessages(data as (HomeMessage & { children: { name: string } })[]);
    setLoadingList(false);
  };

  useState(() => { fetchMessages(); });

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
        .select('observation_text, activity, obs_date')
        .eq('child_id', selectedChildId)
        .order('obs_date', { ascending: false })
        .limit(3);

      const obsText = (obsData ?? [])
        .map((o) => `- ${o.obs_date}: ${o.observation_text ?? ''}`)
        .join('\n');

      const result = await generateAIContent(
        'home-message',
        `Write a warm message home about ${child?.name ?? 'this child'}'s day.`,
        {
          child_name: child?.name ?? '',
          age_group: child?.age_group ?? '',
          context: context,
          recent_observations: obsText || 'No recent observations.',
        }
      );
      setAiResult(result.message ?? '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI generation failed');
    }
    setGenerating(false);
  };

  const handleSave = async () => {
    if (!selectedChildId || !aiResult) return;
    setSaving(true);
    setError(null);
    const { error: saveError } = await supabase.from('home_messages').insert({
      child_id: selectedChildId,
      message_text: aiResult,
    });
    if (saveError) {
      setError(saveError.message);
    } else {
      setAiResult(null);
      setContext('');
      fetchMessages();
    }
    setSaving(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this message?')) return;
    const { error } = await supabase.from('home_messages').delete().eq('id', id);
    if (!error) fetchMessages();
  };

  if (children.length === 0) {
    return (
      <div>
        <SectionHeader icon={<Home size={20} />} title="Home Message" subtitle="Write warm messages to send home to families" color="#4C8B6B" />
        <Card><EmptyState icon={<Home size={48} />} message="Add a child first to create home messages." /></Card>
      </div>
    );
  }

  return (
    <div>
      <SectionHeader
        icon={<Home size={20} />}
        title="Home Message"
        subtitle="Generate a warm, professional message to send home to families"
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
            <TextArea
              label="Additional context (optional)"
              value={context}
              onChange={setContext}
              placeholder="e.g. Had a great day with friends, or Struggled a bit at drop-off"
              rows={2}
            />
            <Button variant="secondary" onClick={handleGenerate} disabled={generating || !selectedChildId}>
              {generating ? (
                <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Writing Message...</span>
              ) : (
                <span className="flex items-center gap-2"><Sparkles size={16} /> Generate Message</span>
              )}
            </Button>
          </div>
        </Card>

        {aiResult && (
          <Card className="border-[#4C8B6B]/30 animate-in fade-in duration-300">
            <div className="bg-stone-50 rounded-xl p-4">
              <p className="text-sm text-stone-700 whitespace-pre-wrap leading-relaxed">{aiResult}</p>
            </div>
            <div className="mt-4">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? (
                  <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Saving...</span>
                ) : (
                  <span className="flex items-center gap-2"><Save size={16} /> Save Message</span>
                )}
              </Button>
            </div>
          </Card>
        )}

        <div>
          <h3 className="font-bold text-stone-800 mb-3">Saved Messages</h3>
          {loadingList && <Card><p className="text-sm text-stone-400 text-center py-4">Loading...</p></Card>}
          {!loadingList && messages.length === 0 && (
            <Card><EmptyState icon={<Home size={40} />} message="No messages saved yet." /></Card>
          )}
          {messages.length > 0 && (
            <div className="space-y-3">
              {messages.map((msg) => (
                <Card key={msg.id}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge color="#4C8B6B">{msg.children?.name ?? '—'}</Badge>
                        <Badge color="#2F5EA8">{msg.message_date}</Badge>
                      </div>
                      <p className="text-sm text-stone-600 line-clamp-3">{msg.message_text}</p>
                    </div>
                    <button
                      onClick={() => handleDelete(msg.id)}
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
