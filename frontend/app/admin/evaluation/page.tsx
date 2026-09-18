'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, BarChart3, BookOpen, CheckCircle2, FileText, Shield, Target, TrendingUp } from 'lucide-react';
import { formatMetric, safeNum } from '@/lib/data-adapters';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AdminEvaluationPage() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API}/api/evaluation/report`).then(r => r.json()).then(data => setReport(data.available && data.report ? data.report : null)).catch(err => setError(err.message || '评估报告加载失败')).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-12 text-center text-gray-400">正在加载评估报告...</div>;
  if (error) return <div className="p-12 text-center text-red-500">{error}</div>;
  if (!report) return <div className="mx-auto max-w-5xl p-8"><div className="rounded-2xl border border-gray-100 bg-white p-12 text-center shadow-sm"><Shield className="mx-auto mb-4 h-12 w-12 text-indigo-300" /><h1 className="text-lg font-semibold text-gray-700">暂无离线评估报告</h1><p className="mt-2 text-sm text-gray-400">运行评估脚本后，质量指标会显示在这里。</p></div></div>;

  const hallucination = report.generated_resource_hallucination_rate;
  const matching = report.assignment_level_matching;
  const coverage = report.knowledge_coverage;
  const total = Number(safeNum(hallucination?.total_verifiable_facts));
  const percentage = (value: unknown) => total > 0 ? Math.round(Number(safeNum(value)) / total * 100) : 0;
  const metrics = [
    ['可验证事实', total, '可进行知识核验的陈述', FileText],
    ['证据覆盖率', formatMetric(hallucination?.evidence_coverage_rate), '具有知识库依据的内容比例', Target],
    ['幻觉率', formatMetric(hallucination?.hallucination_rate), '目标控制在 5% 以下', AlertTriangle],
    ['知识覆盖率', formatMetric(coverage?.coverage_rate), '课程大纲知识点覆盖程度', BookOpen],
  ] as const;

  return <div className="mx-auto max-w-6xl space-y-6 p-6 lg:p-8">
    <header><h1 className="flex items-center gap-2 text-2xl font-bold text-gray-800"><BarChart3 className="h-6 w-6 text-indigo-500" />质量评测</h1><p className="mt-1 text-sm text-gray-400">基于真实数据的内容质量与知识可靠性监控</p></header>
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{metrics.map(([label,value,note,Icon]) => <section key={label} className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-white to-indigo-50 p-5"><Icon className="mb-3 h-5 w-5 text-indigo-500" /><div className="text-2xl font-bold text-gray-800">{value}</div><div className="text-sm font-medium text-gray-600">{label}</div><div className="mt-1 text-xs text-gray-400">{note}</div></section>)}</div>
    <div className="grid gap-6 md:grid-cols-3">
      <section className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm"><h2 className="mb-4 flex items-center gap-2 font-semibold text-gray-700"><FileText className="h-4 w-4 text-indigo-500" />事实核查</h2>{[['有据支持',hallucination?.supported,'bg-emerald-500'],['缺少依据',hallucination?.unsupported,'bg-red-500'],['暂不可验证',hallucination?.unverifiable,'bg-amber-500']].map(([label,value,color]) => { const pct=percentage(value); return <div key={String(label)} className="mb-4"><div className="mb-1 flex justify-between text-sm"><span>{String(label)}</span><span>{safeNum(value)}（{pct}%）</span></div><div className="h-2 overflow-hidden rounded-full bg-gray-100"><div className={`h-full ${color}`} style={{width:`${pct}%`}} /></div></div>; })}</section>
      <section className="rounded-2xl border border-gray-100 bg-white p-6 text-center shadow-sm"><TrendingUp className="mx-auto mb-3 h-5 w-5 text-indigo-500" /><div className="text-3xl font-bold text-indigo-600">{formatMetric(matching?.accuracy)}</div><div className="mt-1 text-sm text-gray-500">难度适配准确率</div><div className="mt-5 grid grid-cols-2 gap-2"><div className="rounded-xl bg-emerald-50 p-3"><div className="text-xl font-bold text-emerald-600">{safeNum(matching?.correct)}</div><div className="text-xs text-gray-400">匹配正确</div></div><div className="rounded-xl bg-red-50 p-3"><div className="text-xl font-bold text-red-500">{safeNum(matching?.incorrect)}</div><div className="text-xs text-gray-400">需要调整</div></div></div></section>
      <section className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm"><h2 className="mb-4 flex items-center gap-2 font-semibold text-gray-700"><Shield className="h-4 w-4 text-indigo-500" />质量门禁</h2><div className={`rounded-xl p-4 text-center ${report.all_passed ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>{report.all_passed ? <CheckCircle2 className="mx-auto mb-2 h-9 w-9" /> : <AlertTriangle className="mx-auto mb-2 h-9 w-9" />}<div className="font-bold">{report.all_passed ? '全部指标通过' : '部分指标需要优化'}</div></div></section>
    </div>
  </div>;
}
