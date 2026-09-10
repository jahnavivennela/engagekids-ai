import { useState, type FormEvent } from 'react';
import { Users, Plus, Pencil, Trash2, X, Loader2 } from 'lucide-react';
import { useChildren } from '@/hooks/useChildren';
import { AGE_GROUPS } from '@/lib/theme';
import {
  Card,
  SectionHeader,
  Button,
  Input,
  Select,
  TextArea,
  EmptyState,
  ErrorBanner,
  Badge,
} from '@/components/ui';
import type { Child } from '@/types';

export function ChildrenPage() {
  const { children, loading, addChild, updateChild, deleteChild, selectedChildId, setSelectedChildId } = useChildren();
  const [showForm, setShowForm] = useState(false);
  const [editingChild, setEditingChild] = useState<Child | null>(null);
  const [name, setName] = useState('');
  const [ageGroup, setAgeGroup] = useState('');
  const [interests, setInterests] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const resetForm = () => {
    setName('');
    setAgeGroup('');
    setInterests('');
    setError(null);
    setEditingChild(null);
    setShowForm(false);
  };

  const startEdit = (child: Child) => {
    setEditingChild(child);
    setName(child.name);
    setAgeGroup(child.age_group ?? '');
    setInterests(child.interests ?? '');
    setShowForm(true);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    setSaving(true);
    setError(null);

    const result = editingChild
      ? await updateChild(editingChild.id, {
          name: name.trim(),
          age_group: ageGroup,
          interests: interests.trim(),
        })
      : await addChild(name.trim(), ageGroup, interests.trim());

    if (result.error) {
      setError(result.error);
    } else {
      resetForm();
    }
    setSaving(false);
  };

  const handleDelete = async (id: string, childName: string) => {
    if (!confirm(`Delete ${childName}? This will also delete all their observations and stories.`)) return;
    await deleteChild(id);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 size={28} className="animate-spin text-[#2F5EA8]" />
      </div>
    );
  }

  return (
    <div>
      <SectionHeader
        icon={<Users size={20} />}
        title="Children"
        subtitle="Manage child profiles in your classroom"
        color="#E6A335"
      />

      {error && <div className="mb-4"><ErrorBanner message={error} /></div>}

      {showForm ? (
        <Card className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-stone-800">
              {editingChild ? 'Edit Child' : 'Add New Child'}
            </h3>
            <button onClick={resetForm} className="p-1.5 rounded-lg hover:bg-stone-100">
              <X size={18} className="text-stone-500" />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input label="Name" value={name} onChange={setName} placeholder="e.g. Raden" required />
            <Select
              label="Age Group"
              value={ageGroup}
              onChange={setAgeGroup}
              placeholder="Select age group"
              options={AGE_GROUPS.map((g) => ({ value: g, label: g }))}
            />
            <TextArea
              label="Interests"
              value={interests}
              onChange={setInterests}
              placeholder="e.g. dinosaurs, drawing, running"
              rows={2}
            />
            <div className="flex gap-3">
              <Button type="submit" disabled={saving}>
                {saving ? <Loader2 size={16} className="animate-spin" /> : editingChild ? 'Save Changes' : 'Add Child'}
              </Button>
              <Button variant="ghost" onClick={resetForm}>Cancel</Button>
            </div>
          </form>
        </Card>
      ) : (
        <div className="mb-6">
          <Button variant="secondary" onClick={() => setShowForm(true)}>
            <span className="flex items-center gap-2"><Plus size={16} /> Add Child</span>
          </Button>
        </div>
      )}

      {children.length === 0 ? (
        <Card>
          <EmptyState
            icon={<Users size={48} />}
            message="No children yet. Add your first child profile to start tracking observations, activities, and learning stories."
          />
        </Card>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {children.map((child) => (
            <Card key={child.id} className="hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div
                  className="flex items-center justify-center w-10 h-10 rounded-xl text-white font-bold text-sm"
                  style={{ backgroundColor: '#E6A335' }}
                >
                  {child.name.charAt(0).toUpperCase()}
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => startEdit(child)}
                    className="p-1.5 rounded-lg hover:bg-stone-100 text-stone-400 hover:text-stone-600 transition-colors"
                  >
                    <Pencil size={15} />
                  </button>
                  <button
                    onClick={() => handleDelete(child.id, child.name)}
                    className="p-1.5 rounded-lg hover:bg-red-50 text-stone-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
              <h3 className="font-bold text-stone-800 mb-1">{child.name}</h3>
              {child.age_group && (
                <div className="mb-2">
                  <Badge color="#2F5EA8">{child.age_group}</Badge>
                </div>
              )}
              {child.interests && (
                <p className="text-sm text-stone-500 line-clamp-2">{child.interests}</p>
              )}
              <button
                onClick={() => setSelectedChildId(child.id)}
                className={`mt-3 text-xs font-medium transition-colors ${
                  selectedChildId === child.id
                    ? 'text-[#2F5EA8]'
                    : 'text-stone-400 hover:text-stone-600'
                }`}
              >
                {selectedChildId === child.id ? '✓ Selected' : 'Set as active child'}
              </button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
