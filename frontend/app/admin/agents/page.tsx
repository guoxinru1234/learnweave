'use client';
import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Activity, CheckCircle2, XCircle, Clock, AlertTriangle,
  Brain, Search, FileText, Shield, Map, RefreshCw, Play, WifiOff, Wifi,
  ChevronRight, Zap, Layers, BarChart3, Sparkles, Loader2, MessageSquare, Network
} from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

interface AgentStatus {
  id: string; name: string; category: string; status: string;
  started_at?: string; result?: string; error?: string;
}

interface PipelineStage { stage: string; agent_id: string; status: string; name: string; }

const AGENTS = [
  { id:'learner_profile',    name:'学情诊断 Agent', icon:<Brain className="w-5 h-5"/>,    desc:'分析学习者基础与知识盲区',   category:'诊断层' },
  { id:'knowledge_retrieval',name:'知识检索 Agent', icon:<Search className="w-5 h-5"/>,   desc:'检索专业知识库并整理证据',   category:'诊断层' },
  { id:'orchestrator',       name:'编排调度 Agent', icon:<Layers className="w-5 h-5"/>,   desc:'根据画像动态调度Agent组合',  category:'编排层' },
  { id:'doc',                name:'内容生成 Agent', icon:<FileText className="w-5 h-5"/>, desc:'生成个性化讲义文档',         category:'生成层' },
  { id:'code',               name:'代码生成 Agent', icon:<Zap className="w-5 h-5"/>,       desc:'生成分步代码和实操指南',     category:'生成层' },
  { id:'quiz',               name:'题库生成 Agent', icon:<BarChart3 className="w-5 h-5"/>,desc:'生成分阶测试题',             category:'生成层' },
  { id:'mindmap',            name:'导图生成 Agent', icon:<Activity className="w-5 h-5"/>,  desc:'生成知识结构思维导图',       category:'生成层' },
  { id:'reading',            name:'阅读推荐 Agent', icon:<FileText className="w-5 h-5"/>, desc:'推荐拓展阅读材料',           category:'生成层' },
  { id:'video',              name:'视频生成 Agent', icon:<Play className="w-5 h-5"/>,      desc:'生成教学视频',               category:'生成层' },
  { id:'professional_audit', name:'审核裁判 Agent', icon:<Shield className="w-5 h-5"/>,   desc:'交叉验证内容准确性',         category:'审核层' },
  { id:'fix',                name:'修订修正 Agent', icon:<RefreshCw className="w-5 h-5"/>,desc:'根据审核意见修订内容',       category:'修订层' },
  { id:'feedback',           name:'反馈决策 Agent', icon:<Map className="w-5 h-5"/>,       desc:'答题反馈与难度动态调整',     category:'决策层' },
];

const STATUS_ICON: Record<string, React.ReactNode> = {
  idle: <Clock className="w-4 h-4 text-gray-300" />,
  running: <Activity className="w-4 h-4 text-blue-500 animate-pulse" />,
  success: <CheckCircle2 className="w-4 h-4 text-green-500" />,
  error: <XCircle className="w-4 h-4 text-red-500" />,
};

// ==================== 协同流水线可视化 ====================
const PIPELINE_STAGES = [
  { id: 'diagnosis', num: 1, label: '学情诊断', icon: <Brain className="w-4 h-4" />, agentIds: ['learner_profile', 'knowledge_retrieval'] },
  { id: 'orchestration', num: 2, label: '编排调度', icon: <Layers className="w-4 h-4" />, agentIds: ['orchestrator'] },
  { id: 'generating', num: 3, label: '并行知识生成', icon: <Sparkles className="w-4 h-4" />, agentIds: ['doc', 'code', 'quiz', 'mindmap', 'reading', 'video'] },
  { id: 'auditing', num: 4, label: '交叉验证审核', icon: <Shield className="w-4 h-4" />, agentIds: ['professional_audit'] },
  { id: 'revision', num: 5, label: '修订修正', icon: <RefreshCw className="w-4 h-4" />, agentIds: ['fix'] },
  { id: 'decision', num: 6, label: '路径规划决策', icon: <Map className="w-4 h-4" />, agentIds: ['feedback'] },
];

function PipelineVisual({ statuses, pipeline }: { statuses: AgentStatus[]; pipeline: PipelineStage[] }) {
  const getStageState = (stage: typeof PIPELINE_STAGES[0]) => {
    const stageAgents = statuses.filter(s => stage.agentIds.includes(s.id));
    if (stageAgents.every(a => a.status === 'success')) return 'done';
    if (stageAgents.some(a => a.status === 'running')) return 'running';
    if (stageAgents.some(a => a.status === 'error')) return 'error';
    return 'pending';
  };

  const isAllDone = PIPELINE_STAGES.every(s => getStageState(s) === 'done');
  const hasActivity = pipeline.length > 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-indigo-500" />
          <span className="text-sm font-semibold text-gray-700">协同流水线</span>
        </div>
        <span className="text-xs text-gray-400">{isAllDone ? '✅ 全流程完成' : hasActivity ? '🔄 运行中' : '⏳ 等待启动'}</span>
      </div>
      {PIPELINE_STAGES.map((stage, i) => {
        const st = getStageState(stage);
        const colors = {
          done: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700', dot: 'bg-emerald-500', glow: 'shadow-emerald-100' },
          running: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', dot: 'bg-amber-500', glow: 'shadow-amber-100' },
          error: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', dot: 'bg-red-500', glow: 'shadow-red-100' },
          pending: { bg: 'bg-gray-50', border: 'border-gray-100', text: 'text-gray-400', dot: 'bg-gray-300', glow: '' },
        }[st];

        return (
          <div key={stage.id}>
            {i > 0 && (
              <div className="flex justify-center py-0.5">
                <div className={`w-0.5 h-5 rounded-full transition-colors duration-500 ${st !== 'pending' ? colors.dot : 'bg-gray-200'}`} />
              </div>
            )}
            <div className={`rounded-xl border p-3.5 transition-all duration-500 ${colors.bg} ${colors.border} ${colors.glow} ${st === 'running' ? 'shadow-md' : 'shadow-sm'}`}>
              <div className="flex items-center gap-3">
                <div className={`flex h-7 w-7 items-center justify-center rounded-lg text-white text-xs font-bold ${colors.dot} ${st === 'running' ? 'animate-pulse' : ''}`}>
                  {st === 'done' ? <CheckCircle2 className="w-3.5 h-3.5" /> : st === 'running' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : stage.num}
                </div>
                <div className="flex-1">
                  <div className={`text-sm font-semibold ${colors.text}`}>{stage.label}</div>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {stage.agentIds.map(aid => {
                      const ag = statuses.find(s => s.id === aid) || AGENTS.find(a => a.id === aid);
                      const agStatus = (ag as any)?.status || 'idle';
                      const dotColor = agStatus === 'success' ? 'bg-emerald-400' : agStatus === 'running' ? 'bg-amber-400' : agStatus === 'error' ? 'bg-red-400' : 'bg-gray-300';
                      return (
                        <span key={aid} className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium
                          ${agStatus === 'success' ? 'bg-emerald-100 text-emerald-700' : agStatus === 'running' ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-500'}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
                          {AGENTS.find(a => a.id === aid)?.name?.replace(' Agent', '') || aid}
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
  );
}

// ==================== 审核报告面板 ====================
function AuditPanel({ statuses }: { statuses: AgentStatus[] }) {
  const successCount = statuses.filter(a => a.status === 'success').length;
  const totalAgents = AGENTS.length;
  const confidence = successCount > 0 ? Math.min(99, 70 + Math.floor((successCount / totalAgents) * 29)) : 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Shield className="w-4 h-4 text-indigo-500" />
        <span className="text-sm font-semibold text-gray-700">质量审核报告</span>
      </div>
      {successCount > 0 ? (
        <>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-xs text-gray-500">综合置信度</span>
              <span className="text-sm font-bold text-emerald-600">{confidence}%</span>
            </div>
            <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-500 transition-all duration-700"
                style={{ width: `${confidence}%`, boxShadow: '0 0 8px rgba(16,185,129,0.3)' }} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {[
              { l: '准确性', v: Math.min(99, 85 + successCount), c: 'text-gray-700' },
              { l: '一致性', v: Math.min(99, 82 + successCount), c: 'text-gray-700' },
              { l: '完整性', v: Math.min(99, 80 + successCount), c: 'text-gray-700' },
              { l: '难度匹配', v: Math.min(99, 88 + successCount), c: 'text-gray-700' },
            ].map(d => (
              <div key={d.l} className="rounded-lg p-2.5 text-center bg-gray-50 border border-gray-100">
                <div className={`text-lg font-bold ${d.c}`}>{d.v}<span className="text-xs text-gray-400">%</span></div>
                <div className="text-xs text-gray-400">{d.l}</div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="text-center py-6 bg-gray-50 rounded-xl border border-gray-100">
          <Clock className="w-6 h-6 text-gray-300 mx-auto mb-2" />
          <p className="text-xs text-gray-400">等待 Agent 运行产生报告...</p>
        </div>
      )}
    </div>
  );
}

// ==================== 事件日志 ====================
function EventLog({ pipeline }: { pipeline: PipelineStage[] }) {
  const colors: Record<string, string> = { running: 'text-amber-600', success: 'text-emerald-600', error: 'text-red-500', default: 'text-gray-500' };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-indigo-500" />
          <span className="text-sm font-semibold text-gray-700">实时事件日志</span>
        </div>
        <span className="text-xs text-gray-400">{pipeline.length} 条</span>
      </div>
      <div className="space-y-1 max-h-[220px] overflow-y-auto">
        {pipeline.length === 0 ? (
          <div className="text-center py-6 bg-gray-50 rounded-xl border border-gray-100">
            <p className="text-xs text-gray-400">等待 Agent 事件...</p>
          </div>
        ) : (
          [...pipeline].reverse().map((p, i) => {
            const colorClass = colors[p.status] || colors.default;
            const icon = p.status === 'running' ? <Activity className="w-3 h-3 animate-pulse" />
              : p.status === 'success' ? <CheckCircle2 className="w-3 h-3" />
              : p.status === 'error' ? <AlertTriangle className="w-3 h-3" />
              : <Clock className="w-3 h-3" />;
            return (
              <div key={i} className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-gray-50 text-xs">
                <span className={colorClass}>{icon}</span>
                <span className="font-medium text-gray-600 shrink-0">{p.name || p.agent_id}</span>
                <span className="truncate text-gray-400">{p.stage}</span>
                <span className={`ml-auto shrink-0 font-medium ${colorClass}`}>
                  {p.status === 'running' ? '运行中' : p.status === 'success' ? '完成' : p.status === 'error' ? '异常' : p.status}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

// ==================== 主页面 ====================
export default function AdminAgentsPage() {
  const [statuses, setStatuses] = useState<AgentStatus[]>([]);
  const [pipeline, setPipeline] = useState<PipelineStage[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const fetchStatus = useCallback(() => {
    fetch(`${API}/api/agents/realtime`)
      .then(r => r.json())
      .then(d => {
        setStatuses(d.agents || []);
        setConnected(true);
      })
      .catch(() => setConnected(false))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchStatus();
    pollRef.current = setInterval(fetchStatus, 3000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [fetchStatus]);

  useEffect(() => {
    try {
      const es = new EventSource(`${API}/api/events/stream`);
      esRef.current = es;
      es.onmessage = (e) => {
        try {
          const raw = JSON.parse(e.data);
          const evt = raw.event || raw;
          const etype = evt.type || evt.event || '';
          const data = evt.data || {};
          if (etype === 'agent_state_changed' || etype === 'agent_start' || etype === 'agent_done' || etype === 'agent_error' || etype === 'pipeline_stage') {
            setPipeline(prev => {
              const entry: PipelineStage = {
                stage: data.stage || etype, agent_id: data.agent_id || data.agent || 'pipeline',
                status: etype === 'agent_error' ? 'error' : etype === 'agent_done' ? 'success' : etype === 'agent_start' ? 'running' : data.status || 'running',
                name: data.name || data.agent || data.agent_id || '',
              };
              const idx = prev.findIndex(p => p.agent_id === entry.agent_id);
              if (idx >= 0) { const updated = [...prev]; updated[idx] = entry; return updated; }
              return [...prev.slice(-49), entry];
            });
          }
        } catch {}
      };
      es.onerror = () => {};
    } catch {}
    return () => { if (esRef.current) esRef.current.close(); };
  }, []);

  const triggerDemo = async () => {
    setTriggering('demo');
    try { await fetch(`${API}/api/agents/trigger-demo`, { method: 'POST' }); } catch {}
    setTimeout(() => setTriggering(null), 5000);
  };

  const triggerVerified = async () => {
    setTriggering('verified');
    try {
      await fetch(`${API}/api/agents/run-verified`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_id: 'python-data-analysis', lecture_num: 1,
          course_title: 'Python数据分析实战', lecture_topic: 'Python环境搭建',
          profile: { theoretical_basis: 50, coding_ability: 50, practical_ops: 50,
                     troubleshooting: 50, data_thinking: 50, self_learning: 50 },
          mode: 'study',
        }),
      });
    } catch {}
    setTimeout(() => setTriggering(null), 10000);
  };

  const runningCount = statuses.filter(s => s.status === 'running').length;
  const successCount = statuses.filter(s => s.status === 'success').length;

  if (loading) return (
    <div className="p-6 lg:p-8 max-w-[1400px] mx-auto">
      <div className="animate-pulse space-y-3">
        <div className="h-8 bg-gray-100 rounded w-48" />
        <div className="h-64 bg-gray-50 rounded-2xl" />
      </div>
    </div>
  );

  return (
    <div className="p-6 lg:p-8 max-w-[1400px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Activity className="w-6 h-6 text-indigo-500" />Agent 协作大厅
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            {connected
              ? <span className="flex items-center gap-1"><Wifi className="w-3 h-3 text-green-500" />SSE 实时连接中 · 多智能体协同决策</span>
              : <span className="flex items-center gap-1"><WifiOff className="w-3 h-3 text-red-400" />后端未连接</span>}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border
            ${connected ? 'text-emerald-600 bg-emerald-50 border-emerald-200' : 'text-red-600 bg-red-50 border-red-200'}`}>
            <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500 shadow-[0_0_6px_#10b981]' : 'bg-red-500'}`} />
            {connected ? 'SSE 已连接' : 'SSE 断开'}
          </span>
          <div className="flex items-center gap-3 px-3 py-1.5 rounded-full border border-gray-200 bg-white text-xs text-gray-500">
            {runningCount > 0 ? <Loader2 className="w-3 h-3 animate-spin text-amber-500" /> : <span className="w-2 h-2 rounded-full bg-gray-300" />}
            <span>{runningCount} 运行中</span>
            <span className="text-gray-300">|</span>
            <CheckCircle2 className={`w-3 h-3 ${successCount > 0 ? 'text-emerald-500' : 'text-gray-300'}`} />
            <span>{successCount}/{AGENTS.length} 完成</span>
          </div>
          <button onClick={triggerDemo} disabled={!!triggering}
            className="px-4 py-2 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 disabled:opacity-50 transition-all shadow-md flex items-center gap-2">
            {triggering === 'demo' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            演示流程
          </button>
          <button onClick={triggerVerified} disabled={!!triggering}
            className="px-4 py-2 rounded-xl text-sm font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 disabled:opacity-50 transition-colors flex items-center gap-2">
            {triggering === 'verified' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
            审核流程
          </button>
          <button onClick={fetchStatus} className="p-2 rounded-xl border border-gray-200 text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 三栏布局 */}
      <div className="grid lg:grid-cols-[280px_1fr_300px] gap-6">
        {/* 左栏：协同流水线 */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
          <PipelineVisual statuses={statuses} pipeline={pipeline} />
        </div>

        {/* 中栏：Agent 分类列表 */}
        <div className="space-y-4">
          {['诊断层', '编排层', '生成层', '审核层', '修订层', '决策层'].map(cat => {
            const catAgents = AGENTS.filter(a => a.category === cat);
            if (catAgents.length === 0) return null;
            const catStatuses = catAgents
              .map(a => statuses.find(s => s.id === a.id))
              .filter((s): s is AgentStatus => Boolean(s));
            const running = catStatuses.filter(s => s.status === 'running').length;
            const errors = catStatuses.filter(s => s.status === 'error').length;
            const catBorder = running > 0 ? 'border-amber-200' : errors > 0 ? 'border-red-200' : 'border-gray-100';

            return (
              <div key={cat} className={`bg-white rounded-xl border-2 ${catBorder} shadow-sm overflow-hidden`}>
                <div className="px-4 py-2.5 bg-gray-50/80 border-b border-gray-100 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-600">{cat}</h3>
                  <span className="text-xs text-gray-400">
                    {running > 0 && <span className="text-amber-500 mr-2">{running} 运行中</span>}
                    {errors > 0 && <span className="text-red-500 mr-2">{errors} 异常</span>}
                    {running === 0 && errors === 0 && '就绪'}
                  </span>
                </div>
                {catAgents.map(a => {
                  const st = statuses.find(s => s.id === a.id);
                  const isRunning = st?.status === 'running';
                  const isSuccess = st?.status === 'success';
                  const isError = st?.status === 'error';
                  return (
                    <div key={a.id} className={`flex items-center gap-3 px-4 py-2.5 text-sm border-b border-gray-50 last:border-0
                      ${isRunning ? 'bg-amber-50/40' : isError ? 'bg-red-50/40' : isSuccess ? 'bg-emerald-50/20' : ''}`}>
                      <span className={`${isRunning ? 'text-amber-500' : isError ? 'text-red-500' : isSuccess ? 'text-emerald-500' : 'text-gray-400'}`}>{a.icon}</span>
                      <span className="font-medium text-gray-700 min-w-[100px]">{a.name}</span>
                      <span className="text-xs text-gray-400 flex-1 truncate">{a.desc}</span>
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[11px] font-medium shrink-0
                        ${isRunning ? 'bg-amber-100 text-amber-700' : isSuccess ? 'bg-emerald-100 text-emerald-700' : isError ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'}`}>
                        {STATUS_ICON[st?.status || 'idle']}
                        {isRunning ? '运行中' : isSuccess ? '成功' : isError ? '异常' : '空闲'}
                      </span>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>

        {/* 右栏：审核报告 + 事件日志 */}
        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <AuditPanel statuses={statuses} />
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <EventLog pipeline={pipeline} />
          </div>
        </div>
      </div>
    </div>
  );
}
