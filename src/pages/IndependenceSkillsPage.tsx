import { useState } from 'react';
import { GraduationCap, Plus, Trash2, Check, Loader2 } from 'lucide-react';
import { useChildren } from '@/hooks/useChildren';
import { supabase } from '@/lib/supabase';
import { AGE_BANDS, SKILL_STATUSES, MILESTONES_SUMMARY } from '@/lib/theme';
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
import type { IndependenceSkill } from '@/types';

const STATUS_COLORS: Record<string, string> = {
  emerging: '#E6A335',
  developing: '#2F5EA8',
  achieved: '#4C8B6B',
};

export function IndependenceSkillsPage() {
  const { children, selectedChildId, setSelectedChildId, loading } = useChildren();
  const [skills, setSkills] = useState<IndependenceSkill[]>([]);
  const [loadingSkills, setLoadingSkills] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [skillName, setSkillName] = useState('');
  const [ageBand, setAgeBand] = useState('');
  const [status, setStatus] = useState('emerging');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSkills = async (childId: string) => {
    setLoadingSkills(true);
    const { data, error } = await supabase
      .from('independence_skills')
      .select('*')
      .eq('child_id', childId)
      .order('observed_date', { ascending: false });
    if (!error && data) setSkills(data as IndependenceSkill[]);
    setLoadingSkills(false);
  };

  const handleSelectChild = (childId: string) => {
    setSelectedChildId(childId);
    fetchSkills(childId);
  };

  const handleAddSkill = async () => {
    if (!selectedChildId || !skillName.trim()) {
      setError('Please enter a skill name.');
      return;
    }
    setSaving(true);
    setError(null);
    const { error: saveError } = await supabase.from('independence_skills').insert({
      child_id: selectedChildId,
      skill_name: skillName.trim(),
      age_band: ageBand,
      status: status,
      notes: notes.trim(),
    });
    if (saveError) {
      setError(saveError.message);
    } else {
      setSkillName('');
      setAgeBand('');
      setStatus('emerging');
      setNotes('');
      setShowAddForm(false);
      fetchSkills(selectedChildId);
    }
    setSaving(false);
  };

  const handleStatusChange = async (skillId: string, newStatus: string) => {
    const { error } = await supabase
      .from('independence_skills')
      .update({ status: newStatus })
      .eq('id', skillId);
    if (error) {
      setError(error.message);
    } else if (selectedChildId) {
      fetchSkills(selectedChildId);
    }
  };

  const handleDelete = async (skillId: string) => {
    if (!confirm('Delete this skill record?')) return;
    const { error } = await supabase.from('independence_skills').delete().eq('id', skillId);
    if (!error && selectedChildId) fetchSkills(selectedChildId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 size={28} className="animate-spin text-[#6B5B95]" />
      </div>
    );
  }

  return (
    <div>
      <SectionHeader
        icon={<GraduationCap size={20} />}
        title="Independence Skills"
        subtitle="Track self-help and independence milestones for each child"
        color="#6B5B95"
      />

      {error && <div className="mb-4"><ErrorBanner message={error} /></div>}

      {children.length === 0 ? (
        <Card>
          <EmptyState icon={<GraduationCap size={48} />} message="Add a child first to track their independence skills." />
        </Card>
      ) : (
        <>
          <Card className="mb-6">
            <Select
              label="Select Child"
              value={selectedChildId ?? ''}
              onChange={handleSelectChild}
              placeholder="Choose a child"
              options={children.map((c) => ({
                value: c.id,
                label: `${c.name} (${c.age_group ?? '—'})`,
              }))}
            />
            {selectedChildId && children.find((c) => c.id === selectedChildId)?.age_group && (
              <div className="mt-4 p-3 rounded-xl bg-[#6B5B95]/5 border border-[#6B5B95]/10">
                <h4 className="text-xs font-bold text-[#6B5B95] uppercase tracking-wide mb-2">
                  Milestones Guide
                </h4>
                <p className="text-sm text-stone-600 mb-2">
                  {MILESTONES_SUMMARY[children.find((c) => c.id === selectedChildId)?.age_group ?? ''] ?? ''}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {(AGE_BANDS[children.find((c) => c.id === selectedChildId)?.age_group ?? ''] ?? []).map((milestone) => (
                    <button
                      key={milestone}
                      onClick={() => {
                        setSkillName(milestone);
                        setAgeBand(children.find((c) => c.id === selectedChildId)?.age_group ?? '');
                        setShowAddForm(true);
                      }}
                      className="text-xs px-2.5 py-1 rounded-full bg-white border border-stone-200 text-stone-600 hover:border-[#6B5B95] hover:text-[#6B5B95] transition-colors"
                    >
                      + {milestone}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {!selectedChildId && (
            <Card>
              <EmptyState icon={<GraduationCap size={48} />} message="Select a child above to track their independence skills." />
            </Card>
          )}

          {selectedChildId && (
            <>
              <div className="mb-4">
                <Button variant="secondary" onClick={() => setShowAddForm(!showAddForm)}>
                  <span className="flex items-center gap-2"><Plus size={16} /> Add Skill</span>
                </Button>
              </div>

              {showAddForm && (
                <Card className="mb-6 animate-in fade-in slide-in-from-top-2 duration-200">
                  <div className="space-y-4">
                    <Input
                      label="Skill Name"
                      value={skillName}
                      onChange={setSkillName}
                      placeholder="e.g. Puts on shoes independently"
                      required
                    />
                    <Select
                      label="Age Band"
                      value={ageBand}
                      onChange={setAgeBand}
                      placeholder="Select age band"
                      options={Object.keys(AGE_BANDS).map((b) => ({ value: b, label: b }))}
                    />
                    <Select
                      label="Status"
                      value={status}
                      onChange={setStatus}
                      options={SKILL_STATUSES.map((s) => ({ value: s, label: s.charAt(0).toUpperCase() + s.slice(1) }))}
                    />
                    <Input
                      label="Notes (optional)"
                      value={notes}
                      onChange={setNotes}
                      placeholder="Any observations about this skill"
                    />
                    <div className="flex gap-3">
                      <Button onClick={handleAddSkill} disabled={saving || !skillName.trim()}>
                        {saving ? <Loader2 size={16} className="animate-spin" /> : 'Save Skill'}
                      </Button>
                      <Button variant="ghost" onClick={() => setShowAddForm(false)}>Cancel</Button>
                    </div>
                  </div>
                </Card>
              )}

              {loadingSkills && <Card><p className="text-sm text-stone-400 text-center py-4">Loading skills...</p></Card>}

              {!loadingSkills && skills.length === 0 && (
                <Card>
                  <EmptyState icon={<GraduationCap size={40} />} message="No skills tracked yet. Add a skill or click a milestone above to get started." />
                </Card>
              )}

              {!loadingSkills && skills.length > 0 && (
                <div className="space-y-3">
                  {skills.map((skill) => (
                    <Card key={skill.id}>
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <h4 className="font-bold text-stone-800 mb-1">{skill.skill_name}</h4>
                          <div className="flex items-center gap-2 mb-2">
                            {skill.age_band && <Badge color="#6B5B95">{skill.age_band}</Badge>}
                            <Badge color={STATUS_COLORS[skill.status] ?? '#6B7280'}>
                              {skill.status}
                            </Badge>
                          </div>
                          {skill.notes && <p className="text-sm text-stone-500">{skill.notes}</p>}
                          <p className="text-xs text-stone-400 mt-1">Observed: {skill.observed_date}</p>
                        </div>
                        <div className="flex flex-col items-end gap-2 flex-shrink-0">
                          <div className="flex gap-1">
                            {SKILL_STATUSES.map((s) => (
                              <button
                                key={s}
                                onClick={() => handleStatusChange(skill.id, s)}
                                className="p-1.5 rounded-lg transition-all"
                                style={{
                                  backgroundColor: skill.status === s ? STATUS_COLORS[s] : 'transparent',
                                  color: skill.status === s ? '#fff' : STATUS_COLORS[s],
                                  border: `1px solid ${STATUS_COLORS[s]}40`,
                                }}
                                title={s}
                              >
                                {s === 'achieved' ? <Check size={14} /> : <span className="text-xs font-bold capitalize">{s[0]}</span>}
                              </button>
                            ))}
                          </div>
                          <button
                            onClick={() => handleDelete(skill.id)}
                            className="p-1.5 rounded-lg hover:bg-red-50 text-stone-400 hover:text-red-500 transition-colors"
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
