import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Client-Info, Apikey',
};

const GROQ_API_KEY = Deno.env.get('GROQ_API_KEY') ?? '';
const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const MODEL = 'llama-3.3-70b-versatile';

interface AIRequestBody {
  feature: string;
  prompt: string;
  context?: Record<string, string>;
}

const FEATURE_SYSTEM_PROMPTS: Record<string, string> = {
  observation: `You are an expert early childhood educator assistant. Given an observation of a child, generate:
1. skill_note: A plain-language description of the skill being developed (1-2 sentences)
2. parent_note: A warm, parent-facing note about what the child did (2-3 sentences, encouraging tone)
3. home_suggestion: A simple activity the family can try at home to extend the learning (1-2 sentences)
Return ONLY valid JSON with these three keys.`,
  'learning-story': `You are an expert early childhood educator. Create a warm, professional learning story based on the provided observations. The story should:
- Be written in a narrative, observational style
- Connect to early childhood development principles
- Be suitable to share with families
- Be 3-5 paragraphs
Return ONLY valid JSON with a "title" key and a "content" key containing the story text.`,
  'quick-activity': `You are an expert early childhood educator. Design a quick, engaging 5-minute activity for young children. Provide:
1. activity_name: A catchy name
2. description: Clear steps to run the activity (3-5 sentences)
3. materials: A comma-separated list of simple materials needed
Return ONLY valid JSON with these three keys.`,
  'magic-trick': `You are an expert early childhood educator. Create a fun, simple "magic trick" activity that will delight young children and spark wonder. Provide:
1. trick_name: A fun, magical name
2. description: How to do it with children (3-5 sentences, enthusiastic tone)
Return ONLY valid JSON with these two keys.`,
  'weekly-planner': `You are an expert early childhood educator. Create a weekly experience plan for a child or group. Provide 5 daily experiences (Monday-Friday) connected to a theme. Each experience should be age-appropriate, play-based, and developmentally sound. Return ONLY valid JSON with:
1. theme: The weekly theme
2. experiences: An array of objects, each with "day" and "experience" keys.`,
  worksheet: `You are an expert early childhood educator. Create a simple, printable worksheet activity for young children based on the given theme. The worksheet should be age-appropriate, visually describable, and fun. Return ONLY valid JSON with a "content" key containing the full worksheet description including instructions, activities, and any visual layout notes.`,
  'home-message': `You are an expert early childhood educator. Write a warm, professional message to send home to a child's family. The message should:
- Share something positive about the child's day
- Be warm and personal
- Include a simple suggestion for extending learning at home
- Be 2-3 short paragraphs
Return ONLY valid JSON with a "message" key containing the message text.`,
  story: `You are a children's story writer. Create a short, engaging story for young children (ages 3-6) based on the given theme. The story should:
- Be 300-500 words
- Use simple, imaginative language
- Have a gentle moral or learning moment
- Be suitable for read-aloud
Return ONLY valid JSON with a "title" key and a "content" key containing the story.`,
};

function extractJson(text: string): Record<string, string> {
  let cleaned = text.trim();
  if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/i, '');
  }
  try {
    return JSON.parse(cleaned);
  } catch {
    const match = cleaned.match(/\{[\s\S]*\}/);
    if (match) {
      try {
        return JSON.parse(match[0]);
      } catch {
        // fall through
      }
    }
    return { content: text };
  }
}

async function callGroq(systemPrompt: string, userPrompt: string): Promise<string> {
  const response = await fetch(GROQ_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${GROQ_API_KEY}`,
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      temperature: 0.7,
      max_tokens: 1500,
    }),
  });

  if (!response.ok) {
    const errText = await response.text().catch(() => 'Unknown error');
    throw new Error(`Groq API error: ${response.status} — ${errText}`);
  }

  const data = await response.json();
  const content = data?.choices?.[0]?.message?.content;
  if (!content || typeof content !== 'string') {
    throw new Error('Groq returned no content');
  }
  return content;
}

function buildUserPrompt(prompt: string, context?: Record<string, string>): string {
  if (!context || Object.keys(context).length === 0) {
    return prompt;
  }
  const ctxStr = Object.entries(context)
    .map(([k, v]) => `${k}: ${v}`)
    .join('\n');
  return `Context:\n${ctxStr}\n\nRequest: ${prompt}`;
}

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const { feature, prompt, context } = (await req.json()) as AIRequestBody;

    if (!feature || !prompt) {
      return new Response(
        JSON.stringify({ error: 'feature and prompt are required' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const systemPrompt = FEATURE_SYSTEM_PROMPTS[feature];
    if (!systemPrompt) {
      return new Response(
        JSON.stringify({ error: `Unknown feature: ${feature}` }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (!GROQ_API_KEY) {
      const fallback = generateFallback(feature, prompt, context);
      return new Response(
        JSON.stringify(fallback),
        { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const userPrompt = buildUserPrompt(prompt, context);
    const rawContent = await callGroq(systemPrompt, userPrompt);
    const parsed = extractJson(rawContent);

    return new Response(
      JSON.stringify(parsed),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return new Response(
      JSON.stringify({ error: message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});

function generateFallback(
  feature: string,
  prompt: string,
  context?: Record<string, string>
): Record<string, string> {
  const childName = context?.child_name ?? 'the child';
  switch (feature) {
    case 'observation':
      return {
        skill_note: 'This activity supports fine motor coordination and social engagement.',
        parent_note: `Today ${childName} showed wonderful focus and curiosity during the activity. We observed growing confidence and a willingness to try new things.`,
        home_suggestion: 'Try a similar activity at home using everyday household items to extend the learning.',
      };
    case 'learning-story':
      return {
        title: `${childName}'s Learning Journey`,
        content: `Over the past weeks, ${childName} has shown remarkable growth in curiosity and engagement. Through play-based experiences, we've observed developing social skills, increasing independence, and a joyful approach to learning. ${childName} demonstrates particular interest in hands-on activities and thrives when given opportunities to explore at their own pace.`,
      };
    case 'quick-activity':
      return {
        activity_name: 'Sensory Treasure Bin',
        description: 'Fill a shallow bin with textured materials and hide small objects for children to find. Encourage them to describe what they feel. This supports sensory development and descriptive language.',
        materials: 'Shallow bin, rice or sand, small toys, spoons',
      };
    case 'magic-trick':
      return {
        trick_name: 'The Disappearing Coin',
        description: 'Show children a coin, place it under a cup, say magic words, and secretly slide it into your other hand. Lift the cup to reveal it "vanished!" Children love the surprise and want to try it themselves.',
      };
    case 'weekly-planner':
      return {
        theme: 'Colors All Around',
        experiences: JSON.stringify([
          { day: 'Monday', experience: 'Color sorting with colored blocks and bowls' },
          { day: 'Tuesday', experience: 'Finger painting with primary colors' },
          { day: 'Wednesday', experience: 'Color scavenger hunt around the room' },
          { day: 'Thursday', experience: 'Mixing colors with water and food coloring' },
          { day: 'Friday', experience: 'Wearing our favorite color and sharing why' },
        ]),
      };
    case 'worksheet':
      return {
        content: `Worksheet: ${prompt}\n\nInstructions: Circle the items that match the theme. Color the pictures. Count and write the number.\n\nActivity 1: Match the shapes\nActivity 2: Color by number\nActivity 3: Trace the letters`,
      };
    case 'home-message':
      return {
        message: `Dear Family,\n\nToday ${childName} had a wonderful day exploring and learning. We noticed great progress in social play and curiosity. ${childName} showed particular enthusiasm during group activities.\n\nAt home, you might try reading a story together and talking about the pictures. This helps build language and connection.\n\nWarm regards,\nThe Teaching Team`,
      };
    case 'story':
      return {
        title: 'The Little Star Who Wanted to Shine',
        content: `Once upon a time, there was a little star named Sparkle who lived high up in the night sky. Sparkle watched all the children below and wanted to shine as bright as the big stars. "Don't worry," said the Moon. "Every star shines in its own way." So Sparkle practiced every night, twinkling a little brighter each time. One evening, a little child looked up and said, "That star is the most beautiful one!" Sparkle glowed with happiness. From that day on, Sparkle knew that being yourself is the brightest way to shine. The end.`,
      };
    default:
      return { content: prompt };
  }
}
