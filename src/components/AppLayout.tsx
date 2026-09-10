import { useState, type ReactNode } from 'react';
import {
  LayoutDashboard,
  Users,
  Eye,
  BookOpen,
  BookMarked,
  Zap,
  Sparkles,
  Calendar,
  PenTool,
  Home,
  BookText,
  GraduationCap,
  LogOut,
  Menu,
  X,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import type { User } from '@supabase/supabase-js';
import type { PageId } from '@/types';
import { PALETTE } from '@/lib/theme';

interface NavItem {
  id: PageId;
  icon: ReactNode;
  label: string;
  color: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', icon: <LayoutDashboard size={18} />, label: 'Dashboard', color: PALETTE.blue },
  { id: 'children', icon: <Users size={18} />, label: 'Children', color: PALETTE.coral },
  { id: 'observation', icon: <Eye size={18} />, label: 'Situation Support', color: PALETTE.coral },
  { id: 'history', icon: <BookOpen size={18} />, label: 'Child History', color: PALETTE.green },
  { id: 'learning-story', icon: <BookMarked size={18} />, label: 'Learning Story', color: PALETTE.green },
  { id: 'quick-activity', icon: <Zap size={18} />, label: 'Quick Activity', color: PALETTE.coral },
  { id: 'magic-trick', icon: <Sparkles size={18} />, label: 'Magic Trick', color: PALETTE.coral },
  { id: 'weekly-planner', icon: <Calendar size={18} />, label: 'Weekly Planner', color: PALETTE.blue },
  { id: 'worksheets', icon: <PenTool size={18} />, label: 'Worksheets', color: PALETTE.blue },
  { id: 'home-message', icon: <Home size={18} />, label: 'Home Message', color: PALETTE.green },
  { id: 'story-time', icon: <BookText size={18} />, label: 'Story Time', color: PALETTE.coral },
  { id: 'independence-skills', icon: <GraduationCap size={18} />, label: 'Independence Skills', color: PALETTE.lavender },
];

export function AppLayout({
  currentPage,
  onNavigate,
  children,
}: {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
  children: ReactNode;
}) {
  const { user, signOut } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleNavigate = (page: PageId) => {
    onNavigate(page);
    setMobileOpen(false);
  };

  return (
    <div className="min-h-screen bg-stone-50 flex">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-64 bg-white border-r border-stone-200/60 fixed h-full z-30">
        <SidebarContent currentPage={currentPage} onNavigate={onNavigate} user={user} onSignOut={signOut} />
      </aside>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/30 z-40 lg:hidden"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-stone-200/60 z-50 lg:hidden">
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute top-3 right-3 p-1.5 rounded-lg hover:bg-stone-100"
            >
              <X size={18} className="text-stone-500" />
            </button>
            <SidebarContent currentPage={currentPage} onNavigate={handleNavigate} user={user} onSignOut={signOut} />
          </aside>
        </>
      )}

      {/* Main content */}
      <main className="flex-1 lg:ml-64 min-h-screen">
        {/* Mobile header */}
        <div className="lg:hidden bg-white border-b border-stone-200/60 px-4 py-3 flex items-center gap-3 sticky top-0 z-30">
          <button
            onClick={() => setMobileOpen(true)}
            className="p-2 rounded-lg hover:bg-stone-100"
          >
            <Menu size={20} className="text-stone-600" />
          </button>
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-[#E6A335] to-[#D98E4A]">
              <Sparkles size={14} className="text-white" />
            </div>
            <span className="font-bold text-stone-800 text-sm">EngageKids AI</span>
          </div>
        </div>
        <div className="p-6 lg:p-8 max-w-6xl mx-auto">{children}</div>
      </main>
    </div>
  );
}

function SidebarContent({
  currentPage,
  onNavigate,
  user,
  onSignOut,
}: {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
  user: User | null;
  onSignOut: () => void;
}) {
  return (
    <>
      <div className="px-5 py-5 border-b border-stone-200/60">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-[#E6A335] to-[#D98E4A] shadow-sm">
            <Sparkles size={18} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold text-stone-800 text-sm leading-tight">EngageKids AI</h1>
            <p className="text-[10px] text-stone-400">Early Childhood Educator</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
        {NAV_ITEMS.map((item) => (
          <NavButton
            key={item.id}
            item={item}
            active={currentPage === item.id}
            onClick={() => onNavigate(item.id)}
          />
        ))}
      </nav>

      <div className="border-t border-stone-200/60 px-4 py-3">
        <div className="text-xs text-stone-400 mb-2 truncate">{user?.email}</div>
        <button
          onClick={onSignOut}
          className="flex items-center gap-2 text-sm text-stone-500 hover:text-red-500 transition-colors"
        >
          <LogOut size={16} />
          Sign Out
        </button>
      </div>
    </>
  );
}

function NavButton({
  item,
  active,
  onClick,
}: {
  item: NavItem;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
        active ? 'text-white shadow-sm' : 'text-stone-600 hover:bg-stone-100'
      }`}
      style={active ? { backgroundColor: item.color } : undefined}
    >
      <span style={!active ? { color: item.color } : undefined}>{item.icon}</span>
      {item.label}
    </button>
  );
}
