'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import {
  Sparkles, Loader2, CheckCircle, AlertCircle,
  Clock, BookOpen, Target, TrendingUp, Play, ChevronRight, Zap,
  BarChart3, ArrowRight, Flame, Map, Star, Rocket, Brain, Shield
} from 'lucide-react';
import { normalizeGenerationResult, saveTaskCache, loadTaskCache } from '@/lib/data-adapters';
import { api } from '@/lib/api';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const STAGES = [
  { id:'profile', label:'学情诊断', desc:'分析当前基础与知识盲区', icon: <Brain className="w-3.5 h-3.5" /> },
  { id:'retrieve', label:'知识检索', desc:'检索专业知识库并整理证据', icon: <BookOpen className="w-3.5 h-3.5" /> },
  { id:'generate', label:'内容生成', desc:'生成个性化学习资源', icon: <Sparkles className="w-3.5 h-3.5" /> },
  { id:'audit', label:'交叉验证', desc:'检查内容、引用和潜在错误', icon: <Shield className="w-3.5 h-3.5" /> },
  { id:'plan', label:'路径规划', desc:'确定难度和下一步任务', icon: <Map className="w-3.5 h-3.5" /> },
];

const LECTURES = [
  { num: 1, title: 'Python环境搭建与Jupyter入门', duration: '45分钟', done: true },
  { num: 2, title: '变量、数据类型与运算符', duration: '45分钟', done: true },
  { num: 3, title: '条件判断与循环控制', duration: '45分钟', done: true },
  { num: 4, title: '函数定义与模块化编程', duration: '90分钟', done: true },
  { num: 5, title: 'NumPy数组创建与索引', duration: '45分钟', done: false },
  { num: 6, title: '数组运算与广播机制', duration: '45分钟', done: false },
];

const PATH_COLORS = [
  { color: '#078fc3', bg: 'bg-[#f1fbfd]', border: 'border-[#c7e7ea]', bar: 'bg-[#078fc3]', tag: 'bg-[#dff6f8] text-[#08758d]' },
  { color: '#167d77', bg: 'bg-[#f1f8f7]', border: 'border-[#cfe6e3]', bar: 'bg-[#167d77]', tag: 'bg-[#dcefed] text-[#11645f]' },
  { color: '#0aa6a6', bg: 'bg-[#f0fbfa]', border: 'border-[#c9e9e5]', bar: 'bg-[#0aa6a6]', tag: 'bg-[#dcf5f1] text-[#087b79]' },
];

const STAT_STYLES = [
  { accent: '#078fc3', soft: '#e9f7fb', border: '#b9dfea' },
  { accent: '#0b8f83', soft: '#e9f8f4', border: '#bde3da' },
  { accent: '#b7791f', soft: '#fff7e8', border: '#ecd8b4' },
  { accent: '#7c5cb5', soft: '#f4effb', border: '#d9cbea' },
];

export default function WorkbenchPage() {
  const { user, token } = useAuth();
  const [topic, setTopic] = useState('');
  const [loading, setLoading] = useState(false);
  type StageStatus = Record<string, 'pending'|'running'|'done'|'error'>;
  const [stageStatus, setStageStatus] = useState<StageStatus>({});
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [sseFail, setSseFail] = useState(false);
  const esRef = useRef<EventSource|null>(null);
  const [profile, setProfile] = useState<any>(null);
  const [paths, setPaths] = useState<any[]>([]);
  const [stats, setStats] = useState({ minutes: 0, quizzes: 0, labs: 0, lectures: 0 });
  const [actualCompletedLectures, setActualCompletedLectures] = useState<number | null>(null);
  const [todos, setTodos] = useState<any[]>([]);
  const [todoInput, setTodoInput] = useState('');

  useEffect(() => {
    const today = new Date().toISOString().slice(0, 10);
    const loadTodos = () => api.getDailyTasks(today).then((d: any) => setTodos(Array.isArray(d) ? d : [])).catch(() => {});
    loadTodos();
    const timer = window.setInterval(loadTodos, 15000);
    return () => window.clearInterval(timer);
  }, []);

  const addTodo = async () => {
    if (!todoInput.trim()) return;
    const today = new Date().toISOString().slice(0, 10);
    const task = await api.addDailyTask({ date: today, content: todoInput.trim(), category: 'student' }).catch(() => null);
    if (task) setTodos((prev) => [...prev, task]);
    setTodoInput('');
  };
  const toggleTodo = async (task: any) => {
    await api.toggleTask(task.id, !task.is_done).catch(() => {});
    setTodos((prev) => prev.map((x) => x.id === task.id ? { ...x, is_done: !x.is_done } : x));
  };

  useEffect(() => {
    const readProgress = () => {
      try {
        const raw = localStorage.getItem('learnmate_progress');
        if (!raw) return setActualCompletedLectures(null);
        const progress = JSON.parse(raw) as Record<string, number>;
        const count = Object.values(progress).filter((value) => Number(value) >= 100).length;
        setActualCompletedLectures(Math.min(count, 20));
      } catch {
        setActualCompletedLectures(null);
      }
    };
    readProgress();
    window.addEventListener('storage', readProgress);
    window.addEventListener('learnmate-progress-updated', readProgress);
    return () => {
      window.removeEventListener('storage', readProgress);
      window.removeEventListener('learnmate-progress-updated', readProgress);
    };
  }, []);

  useEffect(() => {
    if (user?.id) {
      const saved = loadTaskCache(user.id);
      if (saved) setResult(saved);
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      fetch(`${API}/api/profile?user_id=${user.id}`, { headers })
        .then(r => r.json()).then(d => setProfile(d)).catch(() => {});
      fetch(`${API}/api/profile/paths?user_id=${user.id}`, { headers })
        .then(r => r.json()).then(d => setPaths(d.paths || [])).catch(() => {});
    }
    // 从后端获取真实学习数据
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (!user?.id) return;
    const loadStats = () => fetch(`${API}/api/profile/dynamic/${user.id}`, { headers })
      .then(r => r.json())
      .then(d => {
        setStats({
          minutes: d.study_minutes || 0,
          quizzes: d.quiz_attempts || 0,
          labs: d.labs_completed || 0,
          lectures: d.lectures_completed || 0,
        });
      })
      .catch(() => {
        try { const s = localStorage.getItem('learnmate_stats'); if (s) setStats(JSON.parse(s)); } catch {}
      });
    loadStats();
    const timer = window.setInterval(loadStats, 30000);
    return () => window.clearInterval(timer);
  }, [user?.id, token]);

  const runGeneration = async () => {
    if (!topic.trim() || loading) return;
    setLoading(true); setError(''); setResult(null); setSseFail(false);
    const init: StageStatus = {};
    STAGES.forEach(s => init[s.id]='pending');
    setStageStatus(init);
    const profileJson = JSON.stringify({theoretical_basis:50,coding_ability:50,practical_ops:50,troubleshooting:50,data_thinking:50,self_learning:50});
    const qs = new URLSearchParams({mode:'study',profile_json:profileJson});
    const sseUrl = `${API}/api/lecture/python-data-analysis/1/multi-agent-stream?${qs}`;
    const es = new EventSource(sseUrl);
    esRef.current = es;
    const advance = (from: string, to: string) => setStageStatus((p: StageStatus) => ({...p, [from]:'done' as const, [to]:'running' as const}));
    es.addEventListener('generation_started', () => setStageStatus((p: StageStatus) => ({...p, profile:'running' as const})));
    es.addEventListener('generation_completed', () => advance('profile','retrieve'));
    es.addEventListener('audit_started', () => advance('generate','audit'));
    es.addEventListener('revision_started', () => advance('audit','plan'));
    es.addEventListener('final_decision', (e: MessageEvent) => {
      try { const d = JSON.parse(e.data); if (d.status==='approved') setStageStatus((p: StageStatus) => { const f: StageStatus = {}; Object.keys(p).forEach(k => f[k]='done'); return f; }); } catch {}
      es.close(); fetchResult();
    });
    es.addEventListener('error', () => { es.close(); setSseFail(true); fetchResult(); });
    es.onerror = () => { es.close(); setSseFail(true); fetchResult(); };
  };

  const fetchResult = async () => {
    try {
      const profileJson = JSON.stringify({theoretical_basis:50,coding_ability:50,practical_ops:50,troubleshooting:50,data_thinking:50,self_learning:50});
      const qs = new URLSearchParams({mode:'study',profile_json:profileJson});
      const res = await fetch(`${API}/api/lecture/python-data-analysis/1/multi-agent?${qs}`);
      if (!res.ok) throw new Error(`生成失败 (${res.status})`);
      const data = await res.json();
      const norm = normalizeGenerationResult(data);
      setResult(norm);
      if (user?.id) saveTaskCache(user.id, norm);
      setStageStatus((p: StageStatus) => { const f: StageStatus = {}; Object.keys(p).forEach(k => f[k]='done'); return f; });
    } catch (e: any) {
      setError(e.message || '生成失败');
      setStageStatus((p: StageStatus) => { const f: StageStatus = {...p}; Object.keys(f).forEach(k => {if(f[k]==='running') f[k]='error'}); return f; });
    } finally { setLoading(false); }
  };

  useEffect(() => () => { esRef.current?.close(); }, []);

  const hasResult = result?.resource?.content;
  const showProgress = loading || Object.values(stageStatus).some(s => s!=='pending');
  const totalLectures = 20;
  const completedLectures = actualCompletedLectures ?? Math.min(Math.max(stats.lectures || 0, 0), totalLectures);
  const progressPct = completedLectures > 0 ? Math.round(completedLectures / totalLectures * 100) : 0;
  const profileDimensionScores = Object.values(profile?.domain_skills || {})
    .map(Number)
    .filter(score => Number.isFinite(score) && score > 0);
  const profileAverage = profileDimensionScores.length
    ? Math.round(profileDimensionScores.reduce((sum, score) => sum + score, 0) / profileDimensionScores.length)
    : Number(profile?.overall_score || 0);
  const weekday = new Date().toLocaleDateString('zh-CN', { weekday: 'long' });
  const greeting = new Date().getHours() < 12 ? '早上好' : new Date().getHours() < 18 ? '下午好' : '晚上好';

  return (
    <div className="space-y-7 pb-8">
      {/* ===== Hero ===== */}
      <div className="relative overflow-hidden rounded-lg border border-[#a8d8d9] bg-[linear-gradient(115deg,#f0fcfb_0%,#ffffff_52%,#eaf8fb_100%)] shadow-[0_18px_50px_rgba(6,91,103,0.08)]">
        {/* 装饰 */}
        <div className="hidden">
          <div className="absolute -top-20 -right-20 w-80 h-80 rounded-full" style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%)' }} />
          <div className="absolute -bottom-32 left-1/4 w-96 h-96 rounded-full" style={{ background: 'radial-gradient(circle, rgba(167,139,250,0.2) 0%, transparent 70%)' }} />
          <div className="absolute top-1/3 right-1/3 w-4 h-4 rounded-full bg-amber-300/30 blur-sm" style={{ animation: 'twinkle 3s ease-in-out infinite' }} />
          <div className="absolute top-2/3 right-1/4 w-3 h-3 rounded-full bg-emerald-300/30 blur-sm" style={{ animation: 'twinkle 4s ease-in-out infinite 1s' }} />
          <div className="absolute top-1/4 left-2/3 w-2.5 h-2.5 rounded-full bg-sky-300/30 blur-sm" style={{ animation: 'twinkle 3.5s ease-in-out infinite 0.5s' }} />
          {/* 网格纹理 */}
          <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
        </div>
        <div className="pointer-events-none absolute inset-y-0 right-0 w-[42%] bg-[radial-gradient(circle_at_70%_30%,rgba(18,201,184,0.16),transparent_55%)]" />
        <div className="relative flex items-center justify-between px-7 py-9 lg:px-10">
          <div>
            <p className="mb-2 text-sm font-semibold text-[#087f89]">
              {weekday} · {greeting}
            </p>
            <h1 className="mb-3 text-3xl font-semibold text-[#163238] lg:text-[34px]">
              欢迎回来，{user?.username || '同学'}
            </h1>
            <p className="text-sm text-[#707784]">查看当前学习任务，继续完成你的个性化学习路径。</p>
            <div className="flex gap-3 mt-6">
              <Link href="/learn/python-data-analysis"
                className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-[#078fc3] to-[#08b8bd] px-5 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90">
                <Play className="w-5 h-5" />继续学习
              </Link>
              <Link href="/quiz"
                className="inline-flex items-center gap-2 rounded-lg border border-[#dfe2ea] bg-white px-5 py-3 text-sm font-medium text-[#444a57] transition-colors hover:bg-[#f7f8fa]">
                <Target className="w-5 h-5" />去练习
              </Link>
              <Link href="/profile"
                className="inline-flex items-center gap-2 rounded-lg border border-[#dfe2ea] bg-white px-5 py-3 text-sm font-medium text-[#444a57] transition-colors hover:bg-[#f7f8fa]">
                <TrendingUp className="w-5 h-5" />学情画像
              </Link>
            </div>
          </div>
          <div className="hidden min-w-[310px] rounded-lg border border-white/80 bg-white/72 p-5 shadow-[0_10px_30px_rgba(6,91,103,0.07)] backdrop-blur-sm lg:block">
            <div className="flex items-end justify-between">
              <div><div className="text-xs font-medium text-[#858b96]">课程完成率</div><div className="mt-1 text-3xl font-semibold text-[#28303a]">{progressPct}%</div></div>
              <div className="text-right text-xs text-[#858b96]"><div>{completedLectures} 讲已完成</div><div className="mt-1">共 {totalLectures} 讲</div></div>
            </div>
            <div className="mt-5 h-2 overflow-hidden rounded-sm bg-[#e5f2f2]"><div className="h-full bg-gradient-to-r from-[#078fc3] to-[#12c9b8]" style={{ width: `${progressPct}%` }} /></div>
            <div className="mt-4 grid grid-cols-3 gap-2 text-center text-[11px]">
              <div className="border-t-2 border-[#477267] bg-[#f3f7f5] px-2 py-2 text-[#477267]">已完成</div>
              <div className="border-t-2 border-[#08b8bd] bg-[#eefbfb] px-2 py-2 text-[#087f89]">进行中</div>
              <div className="border-t-2 border-[#b17a2d] bg-[#fbf7ef] px-2 py-2 text-[#946523]">待学习</div>
            </div>
          </div>
        </div>
      </div>

      {/* ===== 统计卡片 ===== */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { label: '学习进度', value: completedLectures > 0 ? `${progressPct}%` : '--', sub: completedLectures > 0 ? `${completedLectures}/${totalLectures} 讲完成` : '暂无学习记录', icon: <BarChart3 className="h-[18px] w-[18px]" /> },
          { label: '学习时长', value: (stats.minutes || 0) > 0 ? `${Math.floor(stats.minutes / 60)}h ${stats.minutes % 60}m` : '--', sub: (stats.minutes || 0) > 0 ? `累计 ${stats.minutes} 分钟` : '暂无学习记录', icon: <Clock className="h-[18px] w-[18px]" /> },
          { label: '答题数量', value: (stats.quizzes || 0) > 0 ? stats.quizzes : '--', sub: (stats.labs || 0) > 0 ? `${stats.labs} 个实验完成` : '暂无答题记录', icon: <CheckCircle className="h-[18px] w-[18px]" /> },
          { label: '画像均分', value: profileAverage > 0 ? `${profileAverage}分` : '--', sub: '十维技能综合均分', icon: <Star className="h-[18px] w-[18px]" /> },
        ].map((s, i) => {
          const style = STAT_STYLES[i];
          return (
          <div key={i} className="group relative min-h-[142px] overflow-hidden rounded-lg border bg-white px-5 py-5 shadow-[0_8px_24px_rgba(24,63,70,0.055)] transition-all hover:-translate-y-1 hover:shadow-[0_14px_30px_rgba(24,63,70,0.1)]" style={{ borderColor: style.border }}>
            <div className="absolute inset-y-0 left-0 w-1" style={{ background: style.accent }} />
            <div className="flex items-center justify-between">
              <div className="text-[15px] font-semibold text-[#405b60]">{s.label}</div>
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg" style={{ background: style.soft, color: style.accent }}>
                {s.icon}
              </div>
            </div>
            <div className="mt-5 flex items-end justify-between gap-3">
              <div className="text-[30px] font-semibold leading-none text-[#172d32]">{s.value}</div>
              <div className="max-w-[120px] pb-0.5 text-right text-xs leading-5 text-[#71878b]">{s.sub}</div>
            </div>
          </div>
        )})}
      </div>

      {/* ===== 课程进度 ===== */}
      <div className="grid grid-cols-1 gap-6">
        <div className="rounded-lg border border-[#bfdedf] bg-white p-6 shadow-[0_10px_30px_rgba(6,91,103,0.06)] lg:p-7">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-extrabold text-gray-800 flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#e8fbfa] text-[#078fc3]">
                <BookOpen className="w-5 h-5" />
              </div>
              课程进度
            </h2>
            <Link href="/learn/python-data-analysis" className="text-[13px] font-bold text-[#078fc3] hover:text-[#087f89] flex items-center gap-1 transition-colors">
              全部课程 <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          {/* 进度环 */}
          <div className="mb-5 flex items-center gap-5 rounded-lg border border-[#cfe5e5] bg-[linear-gradient(100deg,#f1fbfa,#f7fbfd)] p-5">
            <div className="flex h-20 w-20 shrink-0 flex-col justify-center border-l-4 border-[#08b8bd] bg-white px-4">
              <svg className="hidden" viewBox="0 0 64 64">
                <circle cx="32" cy="32" r="28" fill="none" stroke="#e0e7ff" strokeWidth="6" />
                <circle cx="32" cy="32" r="28" fill="none" stroke="url(#progGrad)" strokeWidth="6" strokeLinecap="round"
                  strokeDasharray={`${progressPct * 1.76} 176`} />
                <defs>
                  <linearGradient id="progGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#078fc3" />
                    <stop offset="100%" stopColor="#12c9b8" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="text-2xl font-semibold text-[#30343d]">{progressPct}%</span><span className="text-[11px] text-[#8a909c]">完成率</span>
            </div>
            <div>
              <div className="text-[15px] font-bold text-gray-800">Python 数据分析实战</div>
              <div className="text-[13px] text-gray-500 mt-1">已完成 {completedLectures} 讲，还剩 {totalLectures - completedLectures} 讲</div>
              <div className="flex items-center gap-1.5 mt-2">
                <Flame className="w-4 h-4 text-amber-500" />
                <span className="text-[13px] text-amber-600 font-bold">连续学习 7 天</span>
              </div>
            </div>
          </div>
          <div className="space-y-2">
            {LECTURES.map((lec, i) => (
              <Link key={i} href={`/learn/python-data-analysis?lecture=${lec.num}`}
                className={`group flex items-center gap-3 px-4 py-3.5 rounded-md transition-colors hover:bg-gray-50 ${
                  lec.done ? 'bg-[#f4f8f6]' :
                  i === 2 ? 'bg-[#effafa] border-l-[3px] border-l-[#08b8bd]' : ''
                }`}>
                <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-sm font-semibold ${
                  lec.done ? 'bg-[#477267] text-white' :
                  i === 2 ? 'bg-[#08a9b2] text-white' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {lec.done ? <CheckCircle className="w-5 h-5" /> : lec.num}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[15px] font-bold text-gray-800 truncate">{lec.title}</div>
                  <div className="text-[13px] text-gray-500 flex items-center gap-2 mt-0.5">
                    <Clock className="w-3.5 h-3.5" />{lec.duration}
                    {i === 2 && !lec.done && <span className="text-[11px] font-bold text-[#087f89] bg-[#dff7f5] px-2 py-0.5 rounded-md">当前学习</span>}
                  </div>
                </div>
                {!lec.done && <div className="flex items-center justify-center h-9 w-9 rounded-md bg-[#e8fbfa] text-[#078fc3] opacity-0 group-hover:opacity-100 transition-opacity"><Play className="w-4 h-4 ml-0.5" /></div>}
              </Link>
            ))}
          </div>
        </div>

        {/* 个性化学习路径 */}
        <div className="rounded-lg border border-[#bfdedf] bg-white p-6 shadow-[0_10px_30px_rgba(6,91,103,0.06)] lg:p-7">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-extrabold text-gray-800 flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#fff7e8] text-[#b76a00]">
                <Map className="w-5 h-5" />
              </div>
              个性化学习路径
            </h2>
            <span className="text-[11px] font-bold text-amber-600 bg-amber-50 px-3 py-1 rounded-full border border-amber-100">AI 画像驱动</span>
          </div>
          {paths.length > 0 ? (
            <div className="grid grid-cols-3 gap-4">
              {paths.map((p: any, i: number) => {
                const c = PATH_COLORS[i];
                return (
                  <div key={p.id} className={`overflow-hidden rounded-lg border ${c.border} ${c.bg} transition-colors hover:border-gray-300`}>
                    <div className="px-4 py-4" style={{ background: `${c.color}0A` }}>
                      <div className="flex items-center gap-2.5 mb-2">
                        <div className="flex h-9 w-9 items-center justify-center rounded-md text-sm font-semibold text-white" style={{ background: c.color }}>
                          {p.icon || ['🎯','⚡','⚖️'][i]}
                        </div>
                        <div>
                          <div className="text-[15px] font-bold text-gray-800 flex items-center gap-1.5">
                            {p.label}
                            {p.recommended && (
                              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-normal ${c.tag}`}>推荐</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <p className="text-[13px] text-gray-600 leading-relaxed">{p.reason}</p>
                      {p.strategy && (
                        <div className="mt-3 pt-3 border-t border-gray-200/50">
                          <div className="text-[11px] text-gray-500 font-medium mb-1">AI 策略</div>
                          <p className="text-[12px] text-gray-600 leading-relaxed line-clamp-2">{p.strategy}</p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-sm text-gray-500">完成学情画像后，AI 将为你生成专属学习路径</p>
              <Link href="/profile" className="inline-block mt-3 text-sm font-bold text-[#078fc3] hover:text-[#087f89]">
                前往学情画像 →
              </Link>
            </div>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-[#bfdedf] bg-white p-6 shadow-[0_10px_30px_rgba(6,91,103,0.06)]">
        <div className="mb-4 flex items-center justify-between">
          <div><h2 className="flex items-center gap-2 text-lg font-extrabold text-gray-800"><CheckCircle className="h-5 w-5 text-[#078fc3]" />待办事项</h2><p className="mt-1 text-xs text-[#71878b]">教师端下发的学习任务会自动显示在这里</p></div>
          <span className="rounded-full bg-[#e8f8f7] px-3 py-1 text-xs font-semibold text-[#087f89]">{todos.filter((t) => !t.is_done).length} 项待完成</span>
        </div>
        <div className="mb-4 flex gap-2"><input value={todoInput} onChange={(e) => setTodoInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') addTodo(); }} placeholder="添加个人学习待办" className="flex-1 rounded-md border border-[#cfe5e5] px-3 py-2 text-sm outline-none focus:border-[#08b8bd]" /><button onClick={addTodo} className="rounded-md bg-[#078fc3] px-4 py-2 text-sm font-semibold text-white">添加</button></div>
        <div className="space-y-2">{todos.length === 0 ? <div className="rounded-md bg-[#f5fbfb] p-4 text-center text-sm text-[#8aa0a3]">暂无待办事项，教师发布任务后会显示在这里</div> : todos.map((task) => <button key={task.id} onClick={() => toggleTodo(task)} className={`flex w-full items-center gap-3 rounded-md border p-3 text-left hover:bg-[#f4fbfb] ${task.category === 'teacher' ? 'border-[#8bcfd0] bg-[#f0fbfb]' : 'border-[#e3eeee]'}`}><span className={`flex h-5 w-5 items-center justify-center rounded-full border-2 ${task.is_done ? 'border-[#078fc3] bg-[#078fc3] text-white' : 'border-[#9bcacc]'}`}>{task.is_done ? '✓' : ''}</span><span className={`flex-1 text-sm ${task.is_done ? 'text-[#9aa] line-through' : 'text-[#38515a]'}`}>{task.content}</span><span className="text-xs text-[#8aa0a3]">{task.category === 'teacher' ? '教师命令' : '个人学习'}</span></button>)}</div>
      </div>

      {/* ===== 资源生成 ===== */}
      <div className="rounded-lg border border-[#bfdedf] bg-white p-6 shadow-[0_10px_30px_rgba(6,91,103,0.06)] lg:p-7">
        <div className="flex items-center gap-4 mb-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#e8fbfa] text-[#078fc3]">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-gray-800">多智能体资源生成</h2>
            <p className="text-[13px] text-gray-500">输入学习主题，5 个 Agent 协同为你生成个性化学习资源</p>
          </div>
        </div>

        <div className="mt-4 flex gap-3">
          <div className="flex-1 relative">
            <input value={topic} onChange={e => setTopic(e.target.value)} disabled={loading}
              placeholder="试试输入：Pandas DataFrame 数据筛选与过滤..."
              className="w-full px-5 py-3.5 rounded-lg border border-[#c9dfe0] text-[15px] outline-none transition-all focus:border-[#08b8bd] focus:ring-4 focus:ring-[#08b8bd]/10 disabled:opacity-50 bg-[#fbfefe] placeholder:text-gray-400" />
            <Sparkles className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-300" />
          </div>
          <button onClick={runGeneration} disabled={loading || !topic.trim()}
            className="px-7 py-3.5 rounded-lg text-white font-bold text-[15px] disabled:opacity-50 transition-opacity flex items-center gap-2 hover:opacity-90"
            style={{ background: 'linear-gradient(135deg, #078fc3, #12c9b8)' }}>
            {loading ? <><Loader2 className="w-5 h-5 animate-spin" />生成中...</> : <><Rocket className="w-5 h-5" />启动生成</>}
          </button>
        </div>

        {/* 5阶段进度管线 */}
        {showProgress && (
          <div className="mt-5">
            <div className="flex items-center gap-2 mb-3">
              {STAGES.map((s, i) => {
                const st = stageStatus[s.id] || 'pending';
                const colors: Record<string, string> = {
                  running: 'bg-[#e4f8f7] text-[#087f89] border-[#8ed6d3]',
                  done: 'bg-emerald-100 text-emerald-600 border-emerald-300',
                  error: 'bg-red-100 text-red-600 border-red-300',
                  pending: 'bg-gray-50 text-gray-500 border-gray-200',
                };
                return (
                  <div key={s.id} className="flex items-center gap-1.5 flex-1">
                    <div className={`flex-1 flex items-center gap-2 px-3 py-2.5 rounded-lg border text-[13px] font-bold transition-all duration-500 ${colors[st]}`}>
                      <div className={`w-2 h-2 rounded-full ${
                        st === 'running' ? 'bg-[#08b8bd] animate-pulse' :
                        st === 'done' ? 'bg-emerald-500' :
                        st === 'error' ? 'bg-red-500' : 'bg-gray-300'
                      }`} />
                      <span className="hidden sm:inline">{s.label}</span>
                      {st === 'running' && <Loader2 className="w-3.5 h-3.5 animate-spin ml-auto" />}
                      {st === 'done' && <CheckCircle className="w-3.5 h-3.5 ml-auto text-emerald-500" />}
                    </div>
                    {i < STAGES.length - 1 && <div className="w-4 h-px bg-gray-200 shrink-0" />}
                  </div>
                );
              })}
            </div>
            <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
              <div className="h-full rounded-full bg-gradient-to-r from-[#078fc3] to-[#12c9b8] transition-all duration-700"
                style={{ width: `${(Object.values(stageStatus).filter(s => s==='done').length / STAGES.length) * 100}%` }} />
            </div>
          </div>
        )}

        {sseFail && <div className="mt-4 p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-[13px] flex items-center gap-2"><AlertCircle className="w-4 h-4" />SSE 实时连接失败，已自动切换到轮询模式</div>}
        {error && <div className="mt-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-600 text-[13px] flex items-center gap-2"><AlertCircle className="w-4 h-4" />{error}</div>}

        {hasResult && (
          <div className="mt-5 max-h-80 overflow-y-auto rounded-lg border border-[#e6e8ed] bg-[#fafbfc] p-5">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-[13px] font-bold text-gray-700">生成结果预览</span>
              <span className="text-[12px] text-gray-500 ml-auto">由多智能体协同生成</span>
            </div>
            <div className="prose prose-sm max-w-none text-gray-700 text-[15px] leading-relaxed" dangerouslySetInnerHTML={{ __html: result.resource.content?.slice(0, 600) || '' }} />
            {result.resource.content?.length > 600 && (
              <Link href="/learn/python-data-analysis" className="inline-flex items-center gap-1 mt-3 text-[13px] font-bold text-[#078fc3] hover:text-[#087f89]">
                在学习空间查看完整版 <ArrowRight className="w-4 h-4" />
              </Link>
            )}
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes twinkle {
          0%, 100% { opacity: 0.3; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.8); }
        }
      `}</style>
    </div>
  );
}
