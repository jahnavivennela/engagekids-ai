import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import { LoginPage } from '@/pages/LoginPage';
import { AppLayout } from '@/components/AppLayout';
import { DashboardPage } from '@/pages/DashboardPage';
import { ChildrenPage } from '@/pages/ChildrenPage';
import { ObservationPage } from '@/pages/ObservationPage';
import { HistoryPage } from '@/pages/HistoryPage';
import { LearningStoryPage } from '@/pages/LearningStoryPage';
import { QuickActivityPage } from '@/pages/QuickActivityPage';
import { MagicTrickPage } from '@/pages/MagicTrickPage';
import { WeeklyPlannerPage } from '@/pages/WeeklyPlannerPage';
import { WorksheetsPage } from '@/pages/WorksheetsPage';
import { HomeMessagePage } from '@/pages/HomeMessagePage';
import { StoryTimePage } from '@/pages/StoryTimePage';
import { IndependenceSkillsPage } from '@/pages/IndependenceSkillsPage';
import { LoadingSpinner } from '@/components/ui';
import type { PageId } from '@/types';

function AppContent() {
  const { session, loading } = useAuth();
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');

  // Restore last page from hash
  useEffect(() => {
    const hash = window.location.hash.slice(1);
    if (hash) {
      setCurrentPage(hash as PageId);
    }
  }, []);

  // Update hash on navigate
  const handleNavigate = (page: PageId) => {
    setCurrentPage(page);
    window.location.hash = page;
    window.scrollTo(0, 0);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <LoadingSpinner size={32} />
      </div>
    );
  }

  if (!session) {
    return <LoginPage />;
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardPage onNavigate={handleNavigate} />;
      case 'children':
        return <ChildrenPage />;
      case 'observation':
        return <ObservationPage />;
      case 'history':
        return <HistoryPage />;
      case 'learning-story':
        return <LearningStoryPage />;
      case 'quick-activity':
        return <QuickActivityPage />;
      case 'magic-trick':
        return <MagicTrickPage />;
      case 'weekly-planner':
        return <WeeklyPlannerPage />;
      case 'worksheets':
        return <WorksheetsPage />;
      case 'home-message':
        return <HomeMessagePage />;
      case 'story-time':
        return <StoryTimePage />;
      case 'independence-skills':
        return <IndependenceSkillsPage />;
      default:
        return <DashboardPage onNavigate={handleNavigate} />;
    }
  };

  return (
    <AppLayout currentPage={currentPage} onNavigate={handleNavigate}>
      {renderPage()}
    </AppLayout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
