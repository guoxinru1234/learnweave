import { NextResponse } from 'next/server';

export async function POST(request) {
  try {
    const { messages } = await request.json();
    if (!Array.isArray(messages)) return NextResponse.json({ error: 'messages 必须是数组' }, { status: 400 });
    // 复用后端已有的 AI 导学 Agent、RAG 和 LLM 配置，避免前端重复配置密钥
    const backend = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${backend}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ messages }), signal: AbortSignal.timeout(120000) });
    const data = await response.json();
    if (!response.ok) return NextResponse.json({ error: data?.detail || data?.error || 'AI 导学服务请求失败' }, { status: response.status });
    return NextResponse.json({ content: data?.answer || data?.content || '' });
  } catch (error) { return NextResponse.json({ error: error instanceof Error ? error.message : '请求失败' }, { status: 500 }); }
}
