'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Shield, CheckCircle, XCircle, Loader2, Clock, AlertTriangle,
  RefreshCw, FileText, ChevronDown, ChevronRight,
  History, BookOpen, Code2, Search, Target, Wifi, WifiOff
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

interface VerificationStep {
  step: string; agent: string; action: string; status: string;
  version: number; score: number;
  issues: Array<{ location?: string; problem?: string; severity?: string; fix?: string }>;
  feedback: string; started_at: string; finished_at: string | null;
}

interface VerificationResponse {
  task_id: string; status: string; verified: boolean;
  generation_mode: string; final_version: number; retry_count: number;
  verification_steps: VerificationStep[];
  audit_report: { overall_confidence: number; total_issues: number; critical_issues: number; details: any[] } | null;
  citations: Array<{ title: string; source: string }>;
  resource: { title: string; content: string; code: string; mindmap: any[] };
  warning?: string;
}

interface SSEEvent {
  event: string;
  task_id?: string;
  step?: string;
  agent?: string;
  message?: string;
  status?: string;
  version?: number;
  score?: number;
  issues?: any[];
}

const STEP_NAMES: Record<string, string> = {
  resource_generation: '资源生成', professional_audit: '专业审核',
  code_validation: '代码验证', difficulty_audit: '难度审核',
  citation_audit: '引用审核', revision: '内容修订',
  re_audit: '复审', final_decision: '最终决策',
};

function mapEventToSteps(prev: VerificationStep[], evt: SSEEvent): VerificationStep[] {
  const now = new Date().toISOString();
  const stepName = evt.step || evt.event || '';
  const stepLabel = STEP_NAMES[stepName] || stepName;

  // Map event type to status
  let stepStatus = 'running';
  if (evt.event === 'generation_completed') stepStatus = 'passed';
  else if (evt.event === 'audit_completed') stepStatus = 'passed';
  else if (evt.event === 'audit_failed') stepStatus = 'failed';
  else if (evt.event === 'revision_completed') stepStatus = 'passed';
  else if (evt.event === 're_audit_completed') stepStatus = 'passed';
  else if (evt.event === 'final_decision') stepStatus = evt.status === 'approved' ? 'passed' : 'failed';
  else if (evt.event === 'error') stepStatus = 'failed';

  // Find existing step or create new
  const existingIdx = prev.findIndex(s => s.step === stepName);
  const version = evt.version || 1;

  if (existingIdx >= 0) {
    const updated = [...prev];
    updated[existingIdx] = {
      ...updated[existingIdx],
      status: stepStatus,
      score: evt.score ?? updated[existingIdx].score,
      issues: evt.issues || updated[existingIdx].issues,
      feedback: evt.message || updated[existingIdx].feedback,
      finished_at: now,
    };
    return updated;
  }

  // New step
  return [...prev, {
    step: stepName,
    agent: evt.agent || stepName.split('_')[0] || 'Orchestrator',
    action: evt.message || stepLabel,
    status: stepStatus,
    version,
    score: evt.score || 0,
    issues: evt.issues || [],
    feedback: evt.message || '',
    started_at: now,
    finished_at: stepStatus !== 'running' ? now : null,
  }];
}

function StepRow({ step, isLast }: { step: VerificationStep; isLast: boolean }) {
  const [expanded, setExpanded] = useState(step.status === 'failed');
  const isPassed = step.status === 'passed';
  const isRunning = step.status === 'running';
  const isFailed = step.status === 'failed';
  return (
    <div className="relative">
      {!isLast && <div className={`absolute left-5 top-10 w-0.5 h-full -mb-2 ${isPassed ? 'bg-green-200' : isFailed ? 'bg-red-200' : 'bg-gray-200'}`} />}
      <div className={`flex items-start gap-3 py-3 px-4 rounded-xl transition-colors ${isRunning ? 'bg-amber-50' : isFailed ? 'bg-red-50' : isPassed ? 'bg-green-50/50' : 'bg-gray-50'}`}>
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${isRunning ? 'bg-amber-100 text-amber-600' : isFailed ? 'bg-red-100 text-red-500' : isPassed ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
          {isRunning ? <Loader2 className="w-5 h-5 animate-spin" /> : isPassed ? <CheckCircle className="w-5 h-5" /> : isFailed ? <XCircle className="w-5 h-5" /> : <Clock className="w-5 h-5" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm text-gray-800">{STEP_NAMES[step.step] || step.step}</span>
            <span className="text-xs px-1.5 py-0.5 rounded font-medium bg-gray-100 text-gray-500">{step.agent}</span>
            <span className="text-xs px-1.5 py-0.5 rounded-full font-bold bg-purple-50 text-purple-600">V{step.version}</span>
            {step.score > 0 && <span className={`text-xs font-bold ${step.score >= 75 ? 'text-green-600' : 'text-red-500'}`}>{step.score}分</span>}
            <span className={`text-xs font-medium ${isPassed ? 'text-green-600' : isFailed ? 'text-red-500' : 'text-gray-400'}`}>{isPassed ? '通过' : isFailed ? '未通过' : '执行中'}</span>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">{step.action}</p>
          {step.issues.length > 0 && (
            <button onClick={() => setExpanded(!expanded)} className="mt-2 flex items-center gap-1 text-xs text-red-500 hover:text-red-700">
              {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}{step.issues.length} 个问题
            </button>
          )}
          {expanded && step.issues.map((issue, i) => (
            <div key={i} className="mt-2 p-2 rounded-lg bg-red-50 border border-red-100 text-xs">
              <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold mr-1 ${issue.severity === 'critical' ? 'bg-red-200 text-red-700' : issue.severity === 'major' ? 'bg-amber-200 text-amber-700' : 'bg-blue-200 text-blue-700'}`}>{issue.severity || 'minor'}</span>
              <span className="text-red-700">{issue.problem}</span>
              {issue.fix && <p className="text-green-700 mt-1">→ {issue.fix}</p>}
            </div>
          ))}
        </div>
        <div className="text-[10px] text-gray-400 shrink-0 text-right">{step.started_at ? new Date(step.started_at).toLocaleTimeString() : ''}</div>
      </div>
    </div>
  );
}

export default function VerifyPage() {
  const { user } = useAuth();
  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [courseId, setCourseId] = useState('python-data-analysis');
  const [lectureNum, setLectureNum] = useState(1);
  const [profileJson, setProfileJson] = useState('');
  const [sseConnected, setSseConnected] = useState(false);
  const [connectionMode, setConnectionMode] = useState<'sse' | 'polling_fallback' | 'idle'>('idle');
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const startSSE = useCallback((taskId: string) => {
    const url = `${API}/api/lecture/${courseId}/${lectureNum}/multi-agent-stream?mode=study${profileJson ? `&profile_json=${encodeURIComponent(profileJson)}` : ''}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;
    setConnectionMode('sse');

    es.onopen = () => setSseConnected(true);
    es.onerror = () => {
      setSseConnected(false);
      es.close();
      // Fallback to polling
      setConnectionMode('polling_fallback');
      startPolling();
    };

    es.addEventListener('generation_started', (e: MessageEvent) => {
      const data: SSEEvent = JSON.parse(e.data);
      setResult(prev => prev ? { ...prev, task_id: data.task_id || prev.task_id, verification_steps: mapEventToSteps(prev.verification_steps, data) } : prev);
    });
    es.addEventListener('generation_completed', (e: MessageEvent) => {
      const data: SSEEvent = JSON.parse(e.data);
      setResult(prev => prev ? { ...prev, verification_steps: mapEventToSteps(prev.verification_steps, data) } : prev);
    });
    es.addEventListener('audit_started', (e: MessageEvent) => {
      const data: SSEEvent = JSON.parse(e.data);
      setResult(prev => prev ? { ...prev, verification_steps: mapEventToSteps(prev.verification_steps, { ...data, event: 'audit_started' }) } : prev);
    });
    es.addEventListener('audit_failed', (e: MessageEvent) => {
      const data: SSEEvent = JSON.parse(e.data);
      setResult(prev => prev ? { ...prev, verification_steps: mapEventToSteps(prev.verification_steps, { ...data, event: 'audit_failed' }) } : prev);
    });
    es.addEventListener('revision_started', (e: MessageEvent) => {
      const data: SSEEvent = JSON.parse(e.data);
      setResult(prev => prev ? { ...prev, verification_steps: mapEventToSteps(prev.verification_steps, { ...data, event: 'revision_started' }) } : prev);
    });
    es.addEventListener('revision_completed', (e: MessageEvent) => {
      const data: SSEEvent = JSON.parse(e.data);
      setResult(prev => prev ? { ...prev, verification_steps: mapEventToSteps(prev.verification_steps, { ...data, event: 'revision_completed' }) } : prev);
    });
    es.addEventListener('re_audit_completed', (e: MessageEvent) => {
      const data: SSEEvent = JSON.parse(e.data);
      setResult(prev => prev ? { ...prev, verification_steps: mapEventToSteps(prev.verification_steps, { ...data, event: 're_audit_completed' }) } : prev);
    });
    es.addEventListener('final_decision', (e: MessageEvent) => {
      const data: SSEEvent = JSON.parse(e.data);
      setResult(prev => {
        if (!prev) return prev;
        const steps = mapEventToSteps(prev.verification_steps, { ...data, event: 'final_decision' });
        // Fetch full result to get audit_report + citations
        fetch(`${API}/api/verification/audit-report/${courseId}/${lectureNum}`)
          .then(r => r.json())
          .then(report => {
            if (report.verified !== undefined) {
              setResult(p => p ? { ...p, audit_report: report, status: data.status || 'approved', verified: data.status === 'approved', final_version: data.version || 1 } : p);
            }
          }).catch(() => {});
        return { ...prev, verification_steps: steps, status: data.status || 'approved', verified: data.status === 'approved', final_version: data.version || 1 };
      });
      es.close();
      setLoading(false);
    });
    es.addEventListener('error', (e: MessageEvent) => {
      try {
        const data: SSEEvent = JSON.parse(e.data);
        setError(data.message || 'SSE error');
      } catch { setError('SSE connection error'); }
      es.close();
      setLoading(false);
    });
  }, [courseId, lectureNum, profileJson]);

  const startPolling = useCallback(() => {
    setConnectionMode('polling_fallback');
    let attempts = 0;
    pollingRef.current = setInterval(async () => {
      attempts++;
      try {
        const res = await fetch(`${API}/api/lecture/${courseId}/${lectureNum}/multi-agent?mode=study${profileJson ? `&profile_json=${encodeURIComponent(profileJson)}` : ''}`);
        if (res.ok) {
          const data: VerificationResponse = await res.json();
          setResult(data);
          setLoading(false);
          if (pollingRef.current) clearInterval(pollingRef.current);
        }
      } catch { /* retry */ }
      if (attempts > 60) {
        if (pollingRef.current) clearInterval(pollingRef.current);
        setError('轮询超时（60次尝试）');
        setLoading(false);
      }
    }, 2000);
  }, [courseId, lectureNum, profileJson]);

  const run = useCallback(() => {
    setLoading(true); setError(''); setResult(null);
    setConnectionMode('idle');
    if (eventSourceRef.current) eventSourceRef.current.close();
    if (pollingRef.current) clearInterval(pollingRef.current);
    // Try SSE first
    startSSE('');
  }, [startSSE]);

  const vsteps = result?.verification_steps || [];
  const isApproved = result?.status === 'approved';
  const isRejected = result?.status === 'rejected';
  const isFallback = result?.status === 'fallback_pending';

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div>
        <div className="text-xs text-gray-400 mb-1">首页 / 验证中心</div>
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2"><Shield className="w-6 h-6 text-indigo-500" />多智能体协同验证中心</h1>
        <p className="text-sm text-gray-500 mt-0.5">SSE 实时数据 · 审核闭环 · 版本追溯</p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
          <div><label className="text-xs font-medium text-gray-500">课程</label><input value={courseId} onChange={e => setCourseId(e.target.value)} className="w-full mt-1 px-3 py-2 rounded-xl border border-gray-200 text-sm outline-none focus:border-indigo-400" /></div>
          <div><label className="text-xs font-medium text-gray-500">讲次</label><input type="number" value={lectureNum} onChange={e => setLectureNum(Number(e.target.value))} className="w-full mt-1 px-3 py-2 rounded-xl border border-gray-200 text-sm outline-none focus:border-indigo-400" /></div>
          <div><label className="text-xs font-medium text-gray-500">画像JSON(可选)</label><input value={profileJson} onChange={e => setProfileJson(e.target.value)} placeholder='{"theoretical_basis":50,...}' className="w-full mt-1 px-3 py-2 rounded-xl border border-gray-200 text-sm outline-none focus:border-indigo-400" /></div>
          <button onClick={run} disabled={loading} className="px-6 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" />生成+审核中...</> : <><Shield className="w-4 h-4" />运行验证</>}
          </button>
        </div>
      </div>

      {connectionMode !== 'idle' && (
        <div className="flex items-center gap-2 text-xs">
          {connectionMode === 'sse' ? <Wifi className="w-3 h-3 text-green-500" /> : <WifiOff className="w-3 h-3 text-amber-500" />}
          <span className="text-gray-400">{connectionMode === 'sse' ? 'SSE 实时连接' : '轮询降级模式 (SSE不可用)'}</span>
        </div>
      )}

      {error && <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-600 text-sm flex items-center gap-2"><AlertTriangle className="w-4 h-4" />{error}</div>}
      {isFallback && result?.warning && <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-sm flex items-start gap-2"><AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /><div><span className="font-bold">降级模式</span> — {result.warning}</div></div>}

      {result && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[{ l: '任务ID', v: result.task_id }, { l: '状态', v: isApproved ? '已批准' : isRejected ? '已拒绝' : '降级待审', c: isApproved ? 'text-green-600' : isRejected ? 'text-red-500' : 'text-amber-600' }, { l: '版本', v: `V${result.final_version}` }, { l: '重试', v: `${result.retry_count}/3` }, { l: '连接模式', v: connectionMode === 'sse' ? 'SSE' : '轮询' }].map(s => (
            <div key={s.l} className="bg-white rounded-xl border border-gray-100 p-3 text-center"><div className="text-[10px] text-gray-400">{s.l}</div><div className={`text-sm font-bold mt-0.5 ${s.c || 'text-gray-800'}`}>{s.v}</div></div>
          ))}
        </div>
      )}

      {vsteps.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2 mb-1"><History className="w-5 h-5 text-indigo-500" />审核流程（实时）</h2>
          <div className="space-y-1">{vsteps.map((step, i) => <StepRow key={i} step={step} isLast={i === vsteps.length - 1} />)}</div>
        </div>
      )}

      {result?.citations && result.citations.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2 mb-3"><BookOpen className="w-5 h-5 text-indigo-500" />知识引用来源</h2>
          <div className="flex flex-wrap gap-2">{result.citations.map((c, i) => <span key={i} className="px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-medium">{c.title}</span>)}</div>
        </div>
      )}

      {result?.audit_report && (
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2 mb-3"><Target className="w-5 h-5 text-indigo-500" />审核评分</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[{ l: '综合置信度', v: `${result.audit_report.overall_confidence}%`, c: 'text-indigo-600' }, { l: '总问题数', v: result.audit_report.total_issues, c: 'text-green-600' }, { l: '关键问题', v: result.audit_report.critical_issues, c: 'text-red-500' }, { l: '审核项目', v: result.audit_report.details?.length || 0, c: 'text-gray-600' }].map(s => (
              <div key={s.l} className="p-3 rounded-xl bg-gray-50 text-center"><div className={`text-2xl font-bold ${s.c}`}>{s.v}</div><div className="text-xs text-gray-400">{s.l}</div></div>
            ))}
          </div>
        </div>
      )}

      {result && (
        <div className={`p-6 rounded-2xl border-2 text-center ${isApproved ? 'bg-green-50 border-green-300' : isRejected ? 'bg-red-50 border-red-300' : 'bg-amber-50 border-amber-300'}`}>
          {isApproved ? <div className="flex items-center justify-center gap-2"><CheckCircle className="w-8 h-8 text-green-500" /><span className="text-2xl font-bold text-green-700">审核通过 — 资源已批准发布</span></div>
           : isRejected ? <div className="flex items-center justify-center gap-2"><XCircle className="w-8 h-8 text-red-500" /><span className="text-2xl font-bold text-red-700">审核拒绝 — 3次重试已用尽</span></div>
           : <div className="flex items-center justify-center gap-2"><AlertTriangle className="w-8 h-8 text-amber-500" /><span className="text-2xl font-bold text-amber-700">降级待审 — 不作为最终发布资源</span></div>}
          <p className="text-sm text-gray-500 mt-2">任务: {result.task_id} · 版本: V{result.final_version} · 连接: {connectionMode}</p>
        </div>
      )}

      {loading && !result && (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">SSE 实时接收多智能体验证事件...</p>
        </div>
      )}
    </div>
  );
}
