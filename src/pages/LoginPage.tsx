import { useState, type FormEvent } from 'react';
import { Sparkles, Mail, Lock, LogIn, UserPlus, Loader2 } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export function LoginPage() {
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const result =
      mode === 'signin' ? await signIn(email, password) : await signUp(email, password);

    if (result.error) {
      setError(result.error);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-stone-50 via-amber-50/30 to-blue-50/20 px-4">
      <div className="w-full max-w-md">
        {/* Logo and title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-[#E6A335] to-[#D98E4A] shadow-lg mb-4">
            <Sparkles size={32} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-stone-800">EngageKids AI</h1>
          <p className="text-sm text-stone-500 mt-1.5">
            AI-powered tools for early childhood educators
          </p>
        </div>

        {/* Auth card */}
        <div className="bg-white rounded-2xl shadow-xl border border-stone-200/60 p-8">
          <div className="flex gap-2 mb-6 p-1 bg-stone-100 rounded-xl">
            <button
              onClick={() => {
                setMode('signin');
                setError(null);
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                mode === 'signin'
                  ? 'bg-white text-[#2F5EA8] shadow-sm'
                  : 'text-stone-500 hover:text-stone-700'
              }`}
            >
              <LogIn size={16} />
              Sign In
            </button>
            <button
              onClick={() => {
                setMode('signup');
                setError(null);
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                mode === 'signup'
                  ? 'bg-white text-[#2F5EA8] shadow-sm'
                  : 'text-stone-500 hover:text-stone-700'
              }`}
            >
              <UserPlus size={16} />
              Sign Up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1.5">
                Email
              </label>
              <div className="relative">
                <Mail
                  size={18}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-stone-400"
                />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@school.edu"
                  required
                  className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-stone-300 bg-white text-stone-800 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-[#2F5EA8]/30 focus:border-[#2F5EA8] transition-all text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock
                  size={18}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-stone-400"
                />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={6}
                  className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-stone-300 bg-white text-stone-800 placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-[#2F5EA8]/30 focus:border-[#2F5EA8] transition-all text-sm"
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-[#2F5EA8] text-white font-medium hover:bg-[#285595] shadow-md transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.99] text-sm"
            >
              {loading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : mode === 'signin' ? (
                <>
                  <LogIn size={18} />
                  Sign In
                </>
              ) : (
                <>
                  <UserPlus size={18} />
                  Create Account
                </>
              )}
            </button>
          </form>

          {mode === 'signup' && (
            <p className="text-xs text-stone-400 mt-4 text-center">
              Sign up with your email and a password (min 6 characters).
            </p>
          )}
        </div>

        <p className="text-center text-xs text-stone-400 mt-6">
          Built from real classroom experience at Nido Early Learning Centre
        </p>
      </div>
    </div>
  );
}
