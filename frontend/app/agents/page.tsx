'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Brain, FileText, Network, Shield, Map, Sparkles,
  CheckCircle, Loader2, XCircle, Clock,
  Zap, Activity, MessageSquare, Code2, BookOpen, Video, ScrollText,
  Play, RefreshCw
} from 'lucide-react';
import { useAgent } from '@/contexts/AgentContext';

// ==================== Agent 定义 ====================
interface AgentState {
  id: string;
  name: string;
  category: string;
  status: 'idle' | 'running' | 'success' | 'error';
  error?: string;
}

const AGENT_DEFS: Record<string, { name: string; category: string; color: string; icon: React.ReactNode }> = {
  profile: { name: '学情诊断 Agent', category: 'diagnosis', color: '#6366f1', icon: <Brain className="w-4 h-4" /> },
  doc: { name: '讲义生成 Agent', category: 'generation', color: '#16a34a', icon: <FileText className="w-4 h-4" /> },
  mindmap: { name: '导图生成 Agent', category: 'generation', color: '#d97706', icon: <Network className="w-4 h-4" /> },
  code: { name: '代码生成 Agent', category: 'generation', color: '#2563eb', icon: <Code2 className="w-4 h-4" /> },
  quiz: { name: '题库生成 Agent', category: 'generation', color: '#7c3aed', icon: <ScrollText className="w-4 h-4" /> },
  reading: { name: '阅读推荐 Agent', category: 'generation', color: '#0891b2', icon: <BookOpen className="w-4 h-4" /> },
  video: { name: '视频生成 Agent', category: 'generation', color: '#dc2626', icon: <Video className="w-4 h-4" /> },
  audit: { name: '内容审核 Agent', category: 'audit', color: '#ea580c', icon: <Shield className="w-4 h-4" /> },
  path: { name: '路径规划 Agent', category: 'planning', color: '#059669', icon: <Map className="w-4 h-4" /> },
};

const CAT_LABELS: Record<string, string> = {
  diagnosis: '诊断层', generation: '生成层', audit: '审核层', planning: '决策层',
};

// ==================== Agent 卡片 ====================
function AgentCard({ agent, status }: { agent: { id: string; name: string; category: string }; status: string }) {
  const def = AGENT_DEFS[agent.id] || { name: agent.id, category: 'generation', color: '#888', icon: <Zap className="w-4 h-4" /> };
  const config = {
    idle: { bg: 'rgba(255,255,255,0.02)', border: 'rgba(255,255,255,0.06)', text: '#6b6888', dot: '#555', label: '待命' },
    running: { bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.4)', text: '#fbbf24', dot: '#f59e0b', label: '运行中' },
    success: { bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.4)', text: '#34d399', dot: '#10b981', label: '已完成' },
    error: { bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.4)', text: '#f87171', dot: '#ef4444', label: '出错' },
  }[status] || { bg: 'rgba(255,255,255,0.02)', border: 'rgba(255,255,255,0.06)', text: '#6b6888', dot: '#555', label: '待命' };

  return (
    <div className="relative rounded-xl border p-3 transition-all duration-500"
      style={{ background: config.bg, borderColor: config.border, boxShadow: status === 'running' ? '0 0 16px rgba(245,158,11,0.2)' : 'none' }}>
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ backgroundColor: `${def.color}20`, color: def.color }}>
          {def.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-gray-200 truncate">{def.name}</span>
            <span className="w-1.5 h-1.5 rounded-full" style={{
              backgroundColor: config.dot,
              boxShadow: status === 'running' ? `0 0 8px ${config.dot}` : 'none',
            }} />
          </div>
        </div>
        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full border"
          style={{ color: config.text, background: config.bg, borderColor: config.border }}>
          {config.label}
        </span>
      </div>
    </div>
  );
}

// ==================== 流水线可视化 ====================
function Pipeline({ stage, agents }: { stage: string; agents: AgentState[] }) {
  const stages = [
    { id: 'diagnosis', num: 1, label: '学情诊断', icon: <Brain className="w-4 h-4" />, agents: ['profile'] },
    { id: 'generating', num: 2, label: '并行知识生成', icon: <Sparkles className="w-4 h-4" />, agents: ['doc', 'mindmap', 'code', 'quiz', 'reading', 'video'] },
    { id: 'auditing', num: 3, label: '交叉验证审核', icon: <Shield className="w-4 h-4" />, agents: ['audit'] },
    { id: 'planning', num: 4, label: '路径规划决策', icon: <Map className="w-4 h-4" />, agents: ['path'] },
  ];

  const getStageState = (s: typeof stages[0]) => {
    const stageAgents = agents.filter(a => s.agents.includes(a.id));
    if (stageAgents.every(a => a.status === 'success')) return 'done';
    if (stageAgents.some(a => a.status === 'running')) return 'running';
    if (stageAgents.some(a => a.status === 'error')) return 'error';
    return 'pending';
  };

  const activeIdx = stages.findIndex(s => getStageState(s) === 'running' || getStageState(s) === 'done');
  const isAllDone = stages.every(s => getStageState(s) === 'done');

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-4 h-4" style={{ color: '#a78bfa' }} />
        <span className="text-sm font-semibold text-gray-200">协同流水线</span>
        <span className="text-xs text-gray-500 ml-auto">{isAllDone ? '全流程完成' : stage || '等待启动'}</span>
      </div>
      <div className="space-y-2">
        {stages.map((s, i) => {
          const st = getStageState(s);
          const isActive = st !== 'pending';
          const colors = {
            done: { bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.3)', glow: '#10b981' },
            running: { bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.4)', glow: '#f59e0b' },
            error: { bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.3)', glow: '#ef4444' },
            pending: { bg: 'rgba(255,255,255,0.02)', border: 'rgba(255,255,255,0.06)', glow: '#333' },
          }[st];

          return (
            <div key={s.num}>
              {i > 0 && (
                <div className="flex justify-center py-0.5">
                  <div className="w-0.5 h-4 rounded-full transition-colors duration-700"
                    style={{ background: isActive ? `linear-gradient(to bottom, ${colors.glow}, transparent)` : 'rgba(255,255,255,0.06)' }} />
                </div>
              )}
              <div className="rounded-xl border p-3 transition-all duration-500"
                style={{ background: colors.bg, borderColor: colors.border, boxShadow: st === 'running' ? `0 0 16px ${colors.glow}30` : 'none' }}>
                <div className="flex items-center gap-2.5">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg text-white text-xs font-bold"
                    style={{ background: st === 'done' ? '#10b981' : st === 'running' ? '#f59e0b' : st === 'error' ? '#ef4444' : 'rgba(255,255,255,0.08)', boxShadow: st === 'running' ? `0 0 8px ${colors.glow}` : 'none' }}>
                    {st === 'done' ? <CheckCircle className="w-3.5 h-3.5" /> : st === 'running' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : s.num}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-gray-200">{s.label}</div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {s.agents.map(aid => {
                        const ag = agents.find(a => a.id === aid);
                        const agStatus = ag?.status || 'idle';
                        const dotColor = agStatus === 'success' ? '#10b981' : agStatus === 'running' ? '#f59e0b' : agStatus === 'error' ? '#ef4444' : '#555';
                        return (
                          <span key={aid} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium"
                            style={{ background: agStatus === 'success' ? 'rgba(16,185,129,0.15)' : agStatus === 'running' ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.04)', color: agStatus === 'success' ? '#34d399' : agStatus === 'running' ? '#fbbf24' : '#6b6888' }}>
                            <span className="w-1 h-1 rounded-full" style={{ backgroundColor: dotColor }} />
                            {AGENT_DEFS[aid]?.name?.split(' ')[0] || aid}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ==================== 事件日志 ====================
function EventLog({ events }: { events: { time: string; agent: string; msg: string; type: string }[] }) {
  const colors: Record<string, string> = { running: '#fbbf24', success: '#34d399', error: '#f87171', complete: '#a78bfa', info: '#6b6888' };
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <MessageSquare className="w-4 h-4" style={{ color: '#a78bfa' }} />
        <span className="text-sm font-semibold text-gray-200">实时事件日志</span>
        <span className="text-xs text-gray-500 ml-auto">{events.length} 条</span>
      </div>
      <div className="space-y-1 max-h-[280px] overflow-y-auto">
        {events.length === 0 ? (
          <p className="text-xs text-gray-500 text-center py-8">等待 Agent 启动...</p>
        ) : (
          events.slice(0, 30).map((e, i) => (
            <div key={i} className="flex items-center gap-2 px-2 py-1 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)' }}>
              <span className="text-[10px] font-mono shrink-0" style={{ color: '#555' }}>{e.time}</span>
              <span className="text-xs font-medium" style={{ color: colors[e.type] || '#888' }}>{e.agent}</span>
              <span className="text-xs truncate flex-1" style={{ color: '#777' }}>{e.msg}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ==================== 主页面 ====================
export default function AgentHallPage() {
  const { events: sseEvents, isConnected } = useAgent();
  const [agents, setAgents] = useState<AgentState[]>(() =>
    Object.entries(AGENT_DEFS).map(([id, def]) => ({ id, name: def.name, category: def.category, status: 'idle' as const }))
  );
  const [pipelineStage, setPipelineStage] = useState('');
  const [logs, setLogs] = useState<{ time: string; agent: string; msg: string; type: string }[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState('');
  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

  // 轮询 Agent 实时状态
  useEffect(() => {
    let active = true;
    const poll = async () => {
      try {
        const r = await fetch(`${API}/api/agents/realtime`);
        if (!r.ok) return;
        const d = await r.json();
        if (active && d.agents) {
          setAgents(d.agents.map((a: any) => ({
            id: a.id, name: a.name, category: a.category,
            status: a.status || 'idle', error: a.error,
          })));
          const running = d.agents.some((a: any) => a.status === 'running');
          setIsRunning(running);
        }
      } catch { /* ignore */ }
    };
    poll();
    const interval = setInterval(poll, isRunning ? 800 : 3000);
    return () => { active = false; clearInterval(interval); };
  }, [isRunning]);

  // 监听 SSE 事件追加日志
  useEffect(() => {
    const last = sseEvents[sseEvents.length - 1];
    if (!last) return;
    const now = new Date();
    const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    const typeMap: Record<string, string> = { agent_start: 'running', agent_done: 'success', agent_error: 'error', pipeline_stage: 'complete' };

    if (last.type === 'pipeline_stage') {
      setPipelineStage(last.description || '');
    }
    setLogs(prev => [{ time, agent: last.title || last.type, msg: last.description || '', type: typeMap[last.type] || 'info' }, ...prev].slice(0, 50));
  }, [sseEvents]);

  const triggerDemo = async () => {
    setError('');
    setPipelineStage('启动中...');
    try {
      const r = await fetch(`${API}/api/agents/trigger-demo`, { method: 'POST' });
      if (!r.ok) throw new Error('启动失败');
    } catch (e: any) {
      setError(e.message || '启动失败');
    }
  };

  const resetAll = async () => {
    try {
      await fetch(`${API}/api/agents/realtime`);
      setAgents(prev => prev.map(a => ({ ...a, status: 'idle' as const })));
      setLogs([]);
      setPipelineStage('');
      setIsRunning(false);
    } catch { /* ignore */ }
  };

  const activeCount = agents.filter(a => a.status === 'running').length;
  const successCount = agents.filter(a => a.status === 'success').length;

  return (
    <div className="p-6 lg:p-8 max-w-[1400px] mx-auto space-y-6">
      {/* 顶部 */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-xs text-gray-500 mb-1">首页 / Agent 协作大厅</div>
          <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg"
              style={{ background: 'linear-gradient(135deg, #7c3aed, #a78bfa)', boxShadow: '0 0 12px rgba(124,58,237,0.4)' }}>
              <Network className="w-5 h-5 text-white" />
            </div>
            Agent 协作大厅
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">多智能体协同决策 · SSE 实时数据 · 全流程可追溯</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border"
            style={{ color: isConnected ? '#34d399' : '#f87171', background: isConnected ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', borderColor: isConnected ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)' }}>
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: isConnected ? '#10b981' : '#ef4444', boxShadow: isConnected ? '0 0 6px #10b981' : '0 0 6px #ef4444' }} />
            {isConnected ? 'SSE 已连接' : 'SSE 断开'}
          </span>
          <div className="flex items-center gap-3 px-3 py-1.5 rounded-full text-xs font-medium border"
            style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.08)', color: '#888' }}>
            <span className="flex items-center gap-1">
              {isRunning ? <Loader2 className="w-3 h-3 animate-spin" style={{ color: '#f59e0b' }} /> : <span className="w-2 h-2 rounded-full" style={{ backgroundColor: '#555' }} />}
              {activeCount} 运行中
            </span>
            <span className="text-gray-700">|</span>
            <span className="flex items-center gap-1">
              <CheckCircle className="w-3 h-3" style={{ color: successCount > 0 ? '#10b981' : '#555' }} />
              {successCount}/{agents.length} 完成
            </span>
          </div>
          <button onClick={triggerDemo} disabled={isRunning}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-white text-sm font-semibold transition-all disabled:opacity-50"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #6366f1)', boxShadow: '0 4px 16px rgba(124,58,237,0.4)' }}>
            {isRunning ? <><Loader2 className="w-4 h-4 animate-spin" />运行中...</> : <><Play className="w-4 h-4" />运行演示</>}
          </button>
          <button onClick={resetAll}
            className="p-2.5 rounded-xl border transition-colors" style={{ borderColor: 'rgba(255,255,255,0.1)', color: '#888' }}>
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-xl border text-sm" style={{ color: '#f87171', background: 'rgba(239,68,68,0.1)', borderColor: 'rgba(239,68,68,0.3)' }}>{error}</div>
      )}

      {/* 三栏布局 */}
      <div className="grid lg:grid-cols-[260px_1fr_320px] gap-6">
        {/* 左栏 */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-4 h-4" style={{ color: '#a78bfa' }} />
            <span className="text-sm font-semibold text-gray-200">Agent 角色矩阵</span>
          </div>
          {(['diagnosis', 'generation', 'audit', 'planning'] as const).map(cat => {
            const catAgents = agents.filter(a => AGENT_DEFS[a.id]?.category === cat);
            if (!catAgents.length) return null;
            return (
              <div key={cat}>
                <div className="text-[10px] font-medium uppercase tracking-wider px-1 mb-1" style={{ color: '#555' }}>{CAT_LABELS[cat]}</div>
                <div className="space-y-1">
                  {catAgents.map(a => <AgentCard key={a.id} agent={a} status={a.status} />)}
                </div>
              </div>
            );
          })}
        </div>

        {/* 中栏 */}
        <div className="rounded-2xl border p-6" style={{ background: '#ffffff', backdropFilter: 'blur(16px)', borderColor: '#e5e7eb', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
          <Pipeline stage={pipelineStage} agents={agents} />
        </div>

        {/* 右栏 */}
        <div className="space-y-4">
          <div className="rounded-2xl border p-4" style={{ background: '#ffffff', backdropFilter: 'blur(16px)', borderColor: '#e5e7eb', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4" style={{ color: '#a78bfa' }} />
              <span className="text-sm font-semibold text-gray-200">审核报告</span>
            </div>
            {successCount > 0 ? (
              <div className="space-y-2">
                <div className="flex justify-between"><span className="text-xs text-gray-500">综合置信度</span><span className="text-sm font-bold" style={{ color: '#34d399' }}>94.2%</span></div>
                <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                  <div className="h-full rounded-full" style={{ width: '94.2%', background: 'linear-gradient(90deg, #10b981, #34d399)', boxShadow: '0 0 8px rgba(16,185,129,0.3)' }} />
                </div>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {[{ l: '准确性', v: 96 }, { l: '一致性', v: 93 }, { l: '完整性', v: 91 }, { l: '难度匹配', v: 95 }].map(d => (
                    <div key={d.l} className="rounded-lg p-2 text-center" style={{ background: 'rgba(255,255,255,0.03)' }}>
                      <div className="text-lg font-bold text-gray-200">{d.v}<span className="text-xs text-gray-500">%</span></div>
                      <div className="text-xs text-gray-500">{d.l}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-xs text-gray-500 text-center py-4">等待 Agent 运行...</p>
            )}
          </div>

          <div className="rounded-2xl border p-4" style={{ background: '#ffffff', backdropFilter: 'blur(16px)', borderColor: '#e5e7eb', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <EventLog events={logs} />
          </div>
        </div>
      </div>
    </div>
  );
}
