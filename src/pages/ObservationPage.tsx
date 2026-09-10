import { useState } from 'react';
import { Eye, Sparkles, Save, Loader2 } from 'lucide-react';
import { useChildren } from '@/hooks/useChildren';
import { generateAIContent } from '@/lib/ai';
import { supabase } from '@/lib/supabase';
import {
  Card,
  SectionHeader,
  Button,
  TextArea,
  Select,
  ErrorBanner,
  EmptyState,
} from '@/components/ui';

export function ObservationPage() {
  const { children, selectedChildId, setSelectedChildId } = useChildren();
  const [observationText, setObservationText] = useState('');
  const [activity, setActivity] = useState('');
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiResult, setAiResult] = useState<{
    skill_note: string;
    parent_note: string;
    home_suggestion: string;
  } | null>(null);

  const handleGenerate = async () => {
    if (!observationText.trim()) {
      setError('Please describe what you observed first.');
      return;
    }
    if (!selectedChildId) {
      setError('Please select a child first.');
      return;
    }

    setGenerating(true);
    setError(null);
    try {
      const child = children.find((c) => c.id === selectedChildId);
      const result = await generateAIContent('observation', observationText, {
        child_name: child?.name ?? '',
        age_group: child?.age_group ?? '',
        interests: child?.interests ?? '',
        activity: activity,
      });
      setAiResult({
        skill_note: result.skill_note ?? '',
        parent_note: result.parent_note ?? '',
        home_suggestion: result.home_suggestion ?? '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI generation failed');
    }
    setGenerating(false);
  };

  const handleSave = async () => {
    if (!selectedChildId || !observationText.trim()) return;
    setSaving(true);
    setError(null);
    const { error: saveError } = await supabase.from('observations').insert({
      child_id: selectedChildId,
      observation_text: observationText.trim(),
      activity: activity.trim(),
      skill_note: aiResult?.skill_note ?? null,
      parent_note: aiResult?.parent_note ?? null,
      home_suggestion: aiResult?.home_suggestion ?? null,
    });
    if (saveError) {
      setError(saveError.message);
    } else {
      setObservationText('');
      setActivity('');
      setAiResult(null);
    }
    setSaving(false);
  };

  if (children.length === 0) {
    return (
      <div>
        <SectionHeader icon={<Eye size={20} />} title="Situation Support" subtitle="Capture and analyze classroom observations" color="#E6A335" />
        <Card>
          <EmptyState icon={<Eye size={48} />} message="Add a child first to start creating observations." />
        </Card>
      </div>
    );
  }

  return (
    <div>
      <SectionHeader
        icon={<Eye size={20} />}
        title="Situation Support"
        subtitle="Describe what you observed — AI will help you analyze the learning"
        color="#E6A335"
      />

      {error && <div className="mb-4"><ErrorBanner message={error} /></div>}

      <div className="space-y-4">
        <Card>
          <Select
            label="Select Child"
            value={selectedChildId ?? ''}
            onChange={setSelectedChildId}
            required
            placeholder="Choose a child"
            options={children.map((c) => ({ value: c.id, label: `${c.name} (${c.age_group ?? '—'})` }))}
          />
        </Card>

        <Card>
          <div className="space-y-4">
            <TextArea
              label="What did you observe?"
              value={observationText}
              onChange={setObservationText}
              placeholder="e.g. Built a tall tower and named each block a dinosaur. Showed great focus and hand control."
              rows={4}
            />
            <TextArea
              label="What activity was happening? (optional)"
              value={activity}
              onChange={setActivity}
              placeholder="e.g. Block building with dinosaur figures"
              rows={2}
            />
            <Button variant="secondary" onClick={handleGenerate} disabled={generating || !observationText.trim()}>
              {generating ? (
                <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Generating AI Insights...</span>
              ) : (
                <span className="flex items-center gap-2"><Sparkles size={16} /> Generate AI Insights</span>
              )}
            </Button>
          </div>
        </Card>

        {aiResult && (
          <div className="space-y-4 animate-in fade-in duration-300">
            <Card className="border-[#E6A335]/30">
              <h4 className="text-sm font-bold text-[#E6A335] mb-2">Skill Being Developed</h4>
              <p className="text-sm text-stone-700">{aiResult.skill_note}</p>
            </Card>
            <Card className="border-[#4C8B6B]/30">
              <h4 className="text-sm font-bold text-[#4C8B6B] mb-2">Parent Note</h4>
              <p className="text-sm text-stone-700">{aiResult.parent_note}</p>
            </Card>
            <Card className="border-[#2F5EA8]/30">
              <h4 className="text-sm font-bold text-[#2F5EA8] mb-2">Home Suggestion</h4>
              <p className="text-sm text-stone-700">{aiResult.home_suggestion}</p>
            </Card>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? (
                <span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin" /> Saving...</span>
              ) : (
                <span className="flex items-center gap-2"><Save size={16} /> Save Observation</span>
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
