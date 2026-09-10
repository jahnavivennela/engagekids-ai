import { Users, Eye, Zap, BookText, TrendingUp, ArrowRight } from 'lucide-react';
import { useDashboardStats } from '@/hooks/useDashboard';
import type { PageId } from '@/types';
import { Card, LoadingSpinner, EmptyState } from '@/components/ui';

export function DashboardPage({ onNavigate }: { onNavigate: (page: PageId) => void }) {
  const { stats, loading } = useDashboardStats();

  if (loading) return <LoadingSpinner />;

  if (!stats || stats.childCount === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-stone-800 mb-2">Welcome to EngageKids AI</h1>
        <p className="text-stone-500 mb-8">Let's get started by adding your first child profile.</p>
        <Card>
          <EmptyState
            icon={<Users size={48} />}
            message="You haven't added any children yet. Add a child to start creating observations, activities, and learning stories."
            action={
              <button
                onClick={() => onNavigate('children')}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#2F5EA8] text-white text-sm font-medium hover:bg-[#285595] transition-all"
              >
                Add a Child
                <ArrowRight size={16} />
              </button>
            }
          />
        </Card>
      </div>
    );
  }

  const statCards = [
    { label: 'Children', value: stats.childCount, icon: <Users size={20} />, color: '#E6A335', page: 'children' as PageId },
    { label: 'Observations', value: stats.observationCount, icon: <Eye size={20} />, color: '#D98E4A', page: 'observation' as PageId },
    { label: 'Quick Activities', value: stats.activityCount, icon: <Zap size={20} />, color: '#4C8B6B', page: 'quick-activity' as PageId },
    { label: 'Stories Created', value: stats.storyCount, icon: <BookText size={20} />, color: '#6B5B95', page: 'story-time' as PageId },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-stone-800 mb-1">Dashboard</h1>
      <p className="text-stone-500 text-sm mb-8">An overview of your classroom activity</p>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((card) => (
          <button
            key={card.label}
            onClick={() => onNavigate(card.page)}
            className="bg-white rounded-2xl border border-stone-200/60 p-5 text-left hover:shadow-md transition-all duration-200 group"
          >
            <div
              className="flex items-center justify-center w-10 h-10 rounded-xl mb-3"
              style={{ backgroundColor: `${card.color}15` }}
            >
              <span style={{ color: card.color }}>{card.icon}</span>
            </div>
            <div className="text-2xl font-bold text-stone-800">{card.value}</div>
            <div className="text-sm text-stone-500 flex items-center gap-1 mt-0.5">
              {card.label}
              <ArrowRight size={12} className="opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </button>
        ))}
      </div>

      {/* Recent activity */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={18} className="text-[#2F5EA8]" />
            <h3 className="font-bold text-stone-800">Recent Observations</h3>
          </div>
          {stats.recentObservations.length === 0 ? (
            <p className="text-sm text-stone-400 py-4">No observations yet.</p>
          ) : (
            <div className="space-y-3">
              {stats.recentObservations.map((obs) => (
                <button
                  key={obs.id}
                  onClick={() => onNavigate('history')}
                  className="w-full text-left p-3 rounded-xl hover:bg-stone-50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-stone-700">
                      {obs.children?.name ?? 'Unknown'}
                    </span>
                    <span className="text-xs text-stone-400">{obs.obs_date}</span>
                  </div>
                  <p className="text-sm text-stone-500 line-clamp-2">
                    {obs.observation_text ?? 'No observation text'}
                  </p>
                </button>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-4">
            <BookText size={18} className="text-[#6B5B95]" />
            <h3 className="font-bold text-stone-800">Recent Stories</h3>
          </div>
          {stats.recentStories.length === 0 ? (
            <p className="text-sm text-stone-400 py-4">No stories yet.</p>
          ) : (
            <div className="space-y-3">
              {stats.recentStories.map((story) => (
                <button
                  key={story.id}
                  onClick={() => onNavigate('story-time')}
                  className="w-full text-left p-3 rounded-xl hover:bg-stone-50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-stone-700">
                      {story.title ?? 'Untitled Story'}
                    </span>
                    <span className="text-xs text-stone-400">
                      {story.children?.name ?? '—'}
                    </span>
                  </div>
                  <p className="text-sm text-stone-500 line-clamp-2">
                    {story.story_text ?? 'No story text'}
                  </p>
                </button>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Quick actions */}
      <div className="mt-8">
        <h3 className="font-bold text-stone-800 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { label: 'New Observation', icon: <Eye size={16} />, color: '#E6A335', page: 'observation' as PageId },
            { label: 'Quick Activity', icon: <Zap size={16} />, color: '#D98E4A', page: 'quick-activity' as PageId },
            { label: 'Weekly Plan', icon: <TrendingUp size={16} />, color: '#2F5EA8', page: 'weekly-planner' as PageId },
            { label: 'Home Message', icon: <BookText size={16} />, color: '#4C8B6B', page: 'home-message' as PageId },
          ].map((action) => (
            <button
              key={action.label}
              onClick={() => onNavigate(action.page)}
              className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white border border-stone-200/60 hover:border-stone-300 hover:shadow-sm transition-all text-sm font-medium text-stone-700"
            >
              <span style={{ color: action.color }}>{action.icon}</span>
              {action.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
