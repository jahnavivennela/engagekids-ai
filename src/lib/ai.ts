import { supabase } from '@/lib/supabase';
import type { AIGenerationResult } from '@/types';

interface AIRequest {
  feature: string;
  prompt: string;
  context?: Record<string, string>;
}

export async function generateAIContent(
  feature: string,
  prompt: string,
  context?: Record<string, string>
): Promise<AIGenerationResult> {
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData.session?.access_token;

  if (!token) {
    throw new Error('You must be signed in to use AI features.');
  }

  const body: AIRequest = { feature, prompt, context };

  const response = await fetch(
    `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/ai-generate`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    }
  );

  if (!response.ok) {
    const errText = await response.text().catch(() => 'AI generation failed');
    throw new Error(errText);
  }

  const data = await response.json();
  if (!data || typeof data !== 'object') {
    throw new Error('AI returned an unexpected response');
  }
  return data as AIGenerationResult;
}
