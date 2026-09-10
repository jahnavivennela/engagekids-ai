import { useState } from 'react';
import { BookOpen, Trash2, ChevronRight } from 'lucide-react';
import { useChildren } from '@/hooks/useChildren';
import { supabase } from '@/lib/supabase';
import { Card, SectionHeader, Select, EmptyState, Badge } from '@/components/ui';
import type { Observation } from '@/types';

export function HistoryPage() {
  const { children, selectedChildId, setSelectedChildId, loading } = useChildren();
  const [observations, setObservations] = useState<Observation[]>([]);
  const [loadingObs, setLoadingObs] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchObservations = async (childId: string) => {
    setLoadingObs(true);
    const { data, error } = await supabase
      .from('observations')
      .select('*')
      .eq('child_id', childId)
      .order('obs_date', { ascending: false })
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error loading observations:', error.message);
    } else {
      setObservations(data as Observation[]);
    }
    setLoadingObs(false);
  };

  const handleSelectChild = (childId: string) => {
    setSelectedChildId(childId);
    fetchObservations(childId);
  };

  const handleDelete = async (obsId: string) => {
    if (!confirm('Delete this observation?')) return;
    const { error } = await supabase.from('observations').delete().eq('id', obsId);
    if (error) {
      console.error('Delete error:', error.message);
    } else if (selectedChildId) {
      fetchObservations(selectedChildId);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-stone-400 text-sm">Loading...</p>
      </div>
    );
  }

  return (
    <div>
      <SectionHeader
        icon={<BookOpen size={20} />}
        title="Child History"
        subtitle="View and review past observations for each child"
        color="#4C8B6B"
      />

      {children.length === 0 ? (
        <Card>
          <EmptyState icon={<BookOpen size={48} />} message="No children yet. Add a child to start building their history." />
        </Card>
      ) : (
        <>
          <Card className="mb-6">
            <Select
              label="Select Child"
              value={selectedChildId ?? ''}
              onChange={handleSelectChild}
              placeholder="Choose a child to view their history"
              options={children.map((c) => ({
                value: c.id,
                label: `${c.name} (${c.age_group ?? '—'})`,
              }))}
            />
          </Card>

          {!selectedChildId && (
            <Card>
              <EmptyState icon={<BookOpen size={48} />} message="Select a child above to view their observation history." />
            </Card>
          )}

          {selectedChildId && loadingObs && (
            <Card><p className="text-sm text-stone-400 text-center py-4">Loading observations...</p></Card>
          )}

          {selectedChildId && !loadingObs && observations.length === 0 && (
            <Card>
              <EmptyState icon={<BookOpen size={48} />} message="No observations recorded for this child yet. Create one from the Situation Support page." />
            </Card>
          )}

          {selectedChildId && !loadingObs && observations.length > 0 && (
            <div className="space-y-3">
              {observations.map((obs) => (
                <Card key={obs.id}>
                  <div className="flex items-start justify-between gap-4">
                    <button
                      onClick={() => setExpandedId(expandedId === obs.id ? null : obs.id)}
                      className="flex-1 text-left"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Badge color="#2F5EA8">{obs.obs_date}</Badge>
                        {obs.activity && <Badge color="#E6A335">{obs.activity}</Badge>}
                      </div>
                      <p className="text-sm text-stone-700 line-clamp-2">
                        {obs.observation_text ?? 'No observation text'}
                      </p>
                    </button>
                    <div className="flex items-center gap-2">
                      <ChevronRight
                        size={18}
                        className={`text-stone-400 transition-transform ${
                          expandedId === obs.id ? 'rotate-90' : ''
                        }`}
                      />
                      <button
                        onClick={() => handleDelete(obs.id)}
                        className="p-1.5 rounded-lg hover:bg-red-50 text-stone-400 hover:text-red-500 transition-colors"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>

                  {expandedId === obs.id && (
                    <div className="mt-4 pt-4 border-t border-stone-100 space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
                      {obs.skill_note && (
                        <div>
                          <h5 className="text-xs font-bold text-[#E6A335] uppercase tracking-wide mb-1">Skill</h5>
                          <p className="text-sm text-stone-700">{obs.skill_note}</p>
                        </div>
                      )}
                      {obs.parent_note && (
                        <div>
                          <h5 className="text-xs font-bold text-[#4C8B6B] uppercase tracking-wide mb-1">Parent Note</h5>
                          <p className="text-sm text-stone-700">{obs.parent_note}</p>
                        </div>
                      )}
                      {obs.home_suggestion && (
                        <div>
                          <h5 className="text-xs font-bold text-[#2F5EA8] uppercase tracking-wide mb-1">Home Suggestion</h5>
                          <p className="text-sm text-stone-700">{obs.home_suggestion}</p>
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
