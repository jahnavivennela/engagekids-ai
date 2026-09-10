import { useState } from 'react';
import { PenTool, Sparkles, Save, Loader2, Trash2 } from 'lucide-react';
import { generateAIContent } from '@/lib/ai';
import { supabase } from '@/lib/supabase';
import { AGE_GROUPS } from '@/lib/theme';
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
import type { Worksheet } from '@/types';

export function WorksheetsPage() {
  const [theme, setTheme] = useState('');
  const [ageGroup, setAgeGroup] = useState('');
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiResult, setAiResult] = useState<string | null>(null);
  const [worksheets, setWorksheets] = useState<Worksheet[]>([]);
  const [loadingList, setLoadingList] = useState(false);

  const fetchWorksheets = async () => {
    setLoadingList(true);
    const { data, error } = await supabase
      .from('worksheets')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(10);
    if (!error && data) setWorksheets(data as Worksheet[]);
    setLoadingList(false);
  };

  useState(() => { fetchWorksheets(); });

  const handleGenerate = async () => {
    if (!theme.trim()) {
      setError('Please enter a theme for the worksheet.');
      return;
    }
    setGenerating(true);
    setError(null);
    try {
      const result = await generateAIContent('worksheet', `Create a worksheet about: ${theme}`, {
        theme: theme,
        age_group: ageGroup,
      });
      setAiResult(result.content ?? '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI generation failed');
    }
    setGenerating(false);
  };

  const handleSave = async () => {
    if (!aiResult || !theme.trim()) return;
    setSaving(true);
    setError(null);
    const { error: saveError } = await supabase.from('worksheets').insert({
      theme: theme.trim(),
      age_group: ageGroup,
      content: aiResult,
    });
    if (saveError) {
      setError(saveError.message);
    } else {
      setAiResult(null);
      setTheme('');
      fetchWorksheets();
    }
    setSaving(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this worksheet?')) return;
    const { error } = await supabase.from('worksheets').delete().eq('id', id);
    if (!error) fetchWorksheets();
  };

  return (
    <div>
      <SectionHeader
        icon={<PenTool size={20} />}
        title="Worksheets"
        subtitle="Generate printable, age-appropriate worksheet activities"
        color="#2F5EA8"
      />

      {error && <div className="mb-4"><ErrorBanner message={error} /></div>}

      <div className="space-y-4">
        <Card>
          <div className="space-y-4">
            <Input
              label="Theme"
              value={theme}
              onChange={setTheme}
              placeholder="e.g. Ocean Animals, Counting 1-5, Shapes"
              required
            />
            <Select
              label="Age Group (optional)"
              value={ageGroup}
              onChange={setAgeGroup}
              placeholder="Select age group"
              options={AGE_GROUPS.map((g) => ({ value: g, label: g }))}
            />
            <Button onClick={handleGenerate} disabled={generating || !theme.trim()}>
              {generating ? (
                <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Generating Worksheet...</span>
              ) : (
                <span className="flex items-center gap-2"><Sparkles size={16} /> Generate Worksheet</span>
              )}
            </Button>
          </div>
        </Card>

        {aiResult && (
          <Card className="border-[#2F5EA8]/30 animate-in fade-in duration-300">
            <h3 className="font-bold text-stone-800 mb-3">{theme}</h3>
            <div className="bg-stone-50 rounded-xl p-4">
              <p className="text-sm text-stone-700 whitespace-pre-wrap leading-relaxed">{aiResult}</p>
            </div>
            <div className="mt-4">
              <Button onClick={handleSave} disabled={saving}>
                {saving ? (
                  <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Saving...</span>
                ) : (
                  <span className="flex items-center gap-2"><Save size={16} /> Save Worksheet</span>
                )}
              </Button>
            </div>
          </Card>
        )}

        <div>
          <h3 className="font-bold text-stone-800 mb-3">Saved Worksheets</h3>
          {loadingList && <Card><p className="text-sm text-stone-400 text-center py-4">Loading...</p></Card>}
          {!loadingList && worksheets.length === 0 && (
            <Card><EmptyState icon={<PenTool size={40} />} message="No worksheets saved yet." /></Card>
          )}
          {worksheets.length > 0 && (
            <div className="space-y-3">
              {worksheets.map((ws) => (
                <Card key={ws.id}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge color="#2F5EA8">{ws.theme}</Badge>
                        {ws.age_group && <Badge color="#E6A335">{ws.age_group}</Badge>}
                      </div>
                      <p className="text-sm text-stone-600 line-clamp-3">{ws.content}</p>
                    </div>
                    <button
                      onClick={() => handleDelete(ws.id)}
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
