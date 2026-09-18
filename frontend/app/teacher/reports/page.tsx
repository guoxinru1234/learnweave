'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { TrendingUp, Target, AlertTriangle, FileText, Brain, Code2, ClipboardCheck, ArrowUpRight, ShieldCheck, XCircle, Quote, RefreshCw } from 'lucide-react';
import { teacherApi, type ReportsResponse } from '@/lib/teacherApi';

const DIMS = ['理论基础', '编程能力', '实践操作', '问题排查', '数据思维', '自学能力'];

export default function TeacherReports() {
  const [data, setData] = useState<ReportsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reviews, setReviews] = useState<any[]>([]);
  const [selectedReview, setSelectedReview] = useState<any>(null);
  const [reviewReason, setReviewReason] = useState('');
  const [reviewBusy, setReviewBusy] = useState(false);

  const authHeaders = () => {
    const token = typeof window !== 'undefined' ? sessionStorage.getItem('auth_token') : null;
    return { ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  };

  const loadReviews = async () => {
    const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
    const response = await fetch(`${api}/api/teacher/review/list`, { headers: authHeaders() });
    if (response.ok) setReviews((await response.json()).resources || []);
  };

  const openReview = async (id: number) => {
    const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
    const response = await fetch(`${api}/api/teacher/review/${id}`, { headers: authHeaders() });
    if (response.ok) {
      setSelectedReview(await response.json());
      setReviewReason('');
    }
  };

  const submitReview = async (action: 'approve' | 'reject') => {
    if (!selectedReview || reviewBusy) return;
    setReviewBusy(true);
    const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
    const params = new URLSearchParams({ action, reason: reviewReason });
    const response = await fetch(`${api}/api/teacher/review/${selectedReview.id}/action?${params}`, {
      method: 'POST', headers: authHeaders(),
    });
    if (response.ok) {
      setSelectedReview(null);
      await loadReviews();
    }
    setReviewBusy(false);
  };

  useEffect(() => {
    teacherApi
      .getReports()
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
    loadReviews().catch(() => {});
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6 lg:p-8 flex items-center justify-center min-h-[400px]">
        <div className="text-[#8a8a9e] text-lg">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto p-6 lg:p-8 flex items-center justify-center min-h-[400px]">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <div className="text-red-600 font-bold text-lg mb-1">加载失败</div>
          <div className="text-red-500 text-sm">{error}</div>
        </div>
      </div>
    );
  }

  const classAvgDims = data?.class_dim_averages ?? [0, 0, 0, 0, 0, 0];
  const classAvg = data?.class_avg_overall ?? 0;
  const weakest = data?.weakest_dimension ?? '-';
  const strongest = data?.strongest_dimension ?? '-';
  const attention = data?.attention_count ?? 0;
  const resources = [
    { tab: 'doc', label: '课程讲义', desc: '查看学生端实际使用的讲义内容', icon: FileText, color: '#078fc3', bg: '#e9f7fb' },
    { tab: 'mindmap', label: '思维导图', desc: '查看讲义同步生成的知识结构', icon: Brain, color: '#0b8f83', bg: '#e9f8f4' },
    { tab: 'code', label: '代码实践', desc: '查看课程对应的可运行代码', icon: Code2, color: '#b7791f', bg: '#fff7e8' },
    { tab: 'quiz', label: '练习题', desc: '查看课程对应的选择题与编程题', icon: ClipboardCheck, color: '#7c5cb5', bg: '#f4effb' },
  ];

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8 pb-16">
      <div>
        <h1 className="text-2xl font-bold text-[#1a1a2e]">📋 评估报告</h1>
        <p className="text-sm text-[#6a6a7e] mt-1">班级综合评估 · Python数据分析实战</p>
      </div>

      {/* 班级概况 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { icon: TrendingUp, v: `${classAvg}分`, l: '班级10维均分', bg: '#eef2ff', color: '#4f46e5' },
          { icon: Target, v: weakest, l: '班级最弱维度', bg: '#fef2f2', color: '#dc2626' },
          { icon: Target, v: strongest, l: '班级最强维度', bg: '#f0fdf4', color: '#16a34a' },
          { icon: AlertTriangle, v: `${attention}人`, l: '需重点关注', bg: '#fffbeb', color: '#d97706' },
        ].map((s, i) => (
          <div key={i} className="bg-white rounded-2xl border border-[#e8e8ea] p-5" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: s.bg, color: s.color }}>
                <s.icon className="w-5 h-5" />
              </div>
              <div>
                <div className="text-2xl font-extrabold text-[#1a1a2e]">{s.v}</div>
                <div className="text-sm text-[#6a6a7e]">{s.l}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 班级10维分布 */}
      <div id="student-comparison" className="scroll-mt-24 bg-white rounded-2xl border border-[#e8e8ea] p-6" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
        <h2 className="text-lg font-bold text-[#1a1a2e] mb-5">📊 班级10维能力分布</h2>
        <div className="space-y-3">
          {DIMS.map((dim, i) => (
            <div key={dim} className="flex items-center gap-3">
              <span className="w-20 text-sm font-semibold text-[#6a6a7e]">{dim}</span>
              <div className="flex-1 h-3 rounded-full overflow-hidden bg-gray-100">
                <div className="h-full rounded-full transition-all" style={{
                  width: (classAvgDims[i] ?? 0) + '%',
                  background: (classAvgDims[i] ?? 0) >= 70 ? '#16a34a' : (classAvgDims[i] ?? 0) >= 60 ? '#d97706' : '#dc2626'
                }} />
              </div>
              <span className="w-10 text-right text-sm font-bold text-[#1a1a2e]">{classAvgDims[i] ?? 0}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-[#bfdedf] p-6" style={{ boxShadow: '0 10px 30px rgba(6,91,103,0.06)' }}>
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-bold text-[#1a1a2e]">课程资源</h2>
            <p className="mt-1 text-sm text-[#6a6a7e]">与学生端学习空间使用同一套课程资源</p>
          </div>
          <Link href="/learn/python-data-analysis?lecture=1" className="inline-flex items-center gap-1 text-sm font-semibold text-[#078fc3] hover:text-[#087f89]">
            打开学习空间 <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {resources.map(({ tab, label, desc, icon: Icon, color, bg }) => (
            <Link key={tab} href={`/learn/python-data-analysis?lecture=1&tab=${tab}`} className="group rounded-xl border border-[#d8e9e9] p-4 transition hover:-translate-y-0.5 hover:border-[#82cacc] hover:shadow-[0_8px_20px_rgba(6,91,103,0.08)]">
              <div className="flex items-center justify-between">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg" style={{ background: bg, color }}><Icon className="h-5 w-5" /></span>
                <ArrowUpRight className="h-4 w-4 text-[#9bb4b7] transition group-hover:text-[#078f9b]" />
              </div>
              <div className="mt-4 font-semibold text-[#29464b]">{label}</div>
              <div className="mt-1 text-xs leading-5 text-[#71878b]">{desc}</div>
            </Link>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-[#bfdedf] bg-white p-6 shadow-[0_10px_30px_rgba(6,91,103,0.06)]">
        <div className="mb-5 flex items-center justify-between gap-4">
          <div>
            <h2 className="flex items-center gap-2 text-lg font-bold text-[#1a1a2e]"><ShieldCheck className="h-5 w-5 text-[#078f9b]" />资源人工审核</h2>
            <p className="mt-1 text-sm text-[#6a6a7e]">复核学生端生成资源的正文、代码、引用来源与发布状态</p>
          </div>
          <button onClick={() => loadReviews()} className="inline-flex items-center gap-1.5 rounded-lg border border-[#c9dfdf] px-3 py-2 text-sm text-[#48666b] hover:bg-[#f1fbfa]"><RefreshCw className="h-4 w-4" />刷新</button>
        </div>
        {reviews.length ? (
          <div className="overflow-hidden rounded-xl border border-[#dceaea]">
            {reviews.map(item => (
              <button key={item.id} onClick={() => openReview(item.id)} className="flex w-full items-center justify-between gap-4 border-b border-[#e6f0f0] px-4 py-4 text-left last:border-0 hover:bg-[#f6fcfc]">
                <div className="min-w-0"><div className="truncate font-semibold text-[#29464b]">{item.topic || '未命名课程资源'}</div><div className="mt-1 text-xs text-[#789095]">{item.username || `用户 ${item.user_id}`} · {item.task_id || '无任务编号'}</div></div>
                <div className="flex shrink-0 items-center gap-3"><span className={`rounded-md px-2 py-1 text-xs font-medium ${item.review_status === 'approved' ? 'bg-[#e7f8f1] text-[#16805f]' : item.review_status === 'rejected' ? 'bg-[#fff0f0] text-[#c15353]' : 'bg-[#fff7e8] text-[#9a681d]'}`}>{item.review_status === 'approved' ? '已通过' : item.review_status === 'rejected' ? '已驳回' : '待审核'}</span><ArrowUpRight className="h-4 w-4 text-[#91aaad]" /></div>
              </button>
            ))}
          </div>
        ) : <div className="rounded-xl border border-dashed border-[#c8dddd] bg-[#f8fcfc] px-6 py-10 text-center"><ClipboardCheck className="mx-auto h-8 w-8 text-[#8ab7b8]" /><div className="mt-3 font-semibold text-[#456268]">当前没有待审核资源</div><p className="mt-1 text-sm text-[#789095]">学生端完成资源生成并提交后，会在这里形成可复核记录。</p></div>}
      </div>

      {selectedReview && <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#102126]/45 p-5 backdrop-blur-sm"><div className="grid max-h-[88vh] w-full max-w-6xl overflow-hidden rounded-xl border border-[#b9d8d9] bg-white shadow-2xl lg:grid-cols-[1.35fr_0.65fr]">
        <section className="overflow-y-auto p-6"><div className="mb-5"><div className="text-xs font-semibold uppercase tracking-[0.14em] text-[#078f9b]">Resource preview</div><h3 className="mt-1 text-xl font-semibold text-[#19373d]">{selectedReview.topic || '生成资源详情'}</h3></div><div className="prose max-w-none rounded-lg border border-[#dceaea] bg-[#fbfefe] p-5 text-sm leading-7 text-[#405b60] whitespace-pre-wrap">{selectedReview.content || '暂无讲义正文'}</div>{selectedReview.code && <div className="mt-5"><div className="mb-2 flex items-center gap-2 font-semibold text-[#29464b]"><Code2 className="h-4 w-4" />代码内容</div><pre className="overflow-x-auto rounded-lg bg-[#15282d] p-4 text-xs leading-6 text-[#d9f5f1]">{selectedReview.code}</pre></div>}</section>
        <aside className="overflow-y-auto border-l border-[#dceaea] bg-[#f7fbfb] p-6"><div className="mb-5 flex items-center justify-between"><h3 className="font-semibold text-[#29464b]">审核与发布</h3><button onClick={() => setSelectedReview(null)} className="rounded-md p-1.5 text-[#789095] hover:bg-white"><XCircle className="h-5 w-5" /></button></div><div className="space-y-3 text-sm"><div className="rounded-lg border border-[#dceaea] bg-white p-3"><div className="text-xs text-[#789095]">任务编号</div><div className="mt-1 break-all font-medium text-[#29464b]">{selectedReview.task_id || '-'}</div></div><div className="rounded-lg border border-[#dceaea] bg-white p-3"><div className="text-xs text-[#789095]">当前状态</div><div className="mt-1 font-medium text-[#29464b]">{selectedReview.review_status || 'pending_review'}</div></div></div><div className="mt-5"><div className="mb-2 flex items-center gap-2 text-sm font-semibold text-[#29464b]"><Quote className="h-4 w-4" />引用来源</div><div className="space-y-2">{(selectedReview.citations || []).length ? selectedReview.citations.map((citation: any, index: number) => <div key={index} className="rounded-md border border-[#dceaea] bg-white px-3 py-2 text-xs leading-5 text-[#5d777c]">{citation.title || citation.source || String(citation)}</div>) : <div className="text-xs text-[#91a6a9]">暂无引用记录</div>}</div></div><label className="mt-5 block"><span className="mb-2 block text-sm font-semibold text-[#29464b]">人工审核意见</span><textarea value={reviewReason} onChange={event => setReviewReason(event.target.value)} rows={5} className="w-full resize-none rounded-lg border border-[#c9dfdf] bg-white p-3 text-sm outline-none focus:border-[#08b8bd] focus:ring-4 focus:ring-[#08b8bd]/10" placeholder="填写通过说明或需要修改的问题" /></label><div className="mt-5 grid grid-cols-2 gap-3"><button disabled={reviewBusy} onClick={() => submitReview('reject')} className="rounded-lg border border-[#efcaca] bg-white px-4 py-2.5 text-sm font-semibold text-[#ba4d4d] hover:bg-[#fff5f5] disabled:opacity-50">驳回修改</button><button disabled={reviewBusy} onClick={() => submitReview('approve')} className="rounded-lg bg-gradient-to-r from-[#078fc3] to-[#12c9b8] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">审核通过</button></div></aside>
      </div></div>}

      {/* 学生对比表 */}
      <div className="bg-white rounded-2xl border border-[#e8e8ea] p-6" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
        <h2 className="text-lg font-bold text-[#1a1a2e] mb-5">👥 学生评估对比</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#e8e8ea] bg-[#fafaff]">
                <th className="text-left px-4 py-3 font-semibold text-[#8a8a9e]">学生</th>
                <th className="text-left px-4 py-3 font-semibold text-[#8a8a9e]">综合</th>
                {DIMS.map(d => <th key={d} className="text-left px-4 py-3 font-semibold text-[#8a8a9e] text-xs">{d}</th>)}
                <th className="text-left px-4 py-3 font-semibold text-[#8a8a9e]">薄弱</th>
                <th className="text-left px-4 py-3 font-semibold text-[#8a8a9e]">优势</th>
              </tr>
            </thead>
            <tbody>
              {(data?.students ?? []).map((st, i) => (
                <tr key={i} className="border-b border-[#f0f0f5] hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-semibold text-[#1a1a2e]">{st.name}</td>
                  <td className="px-4 py-3">
                    <span className={`font-extrabold ${st.overall >= 70 ? 'text-[#16a34a]' : st.overall >= 50 ? 'text-[#d97706]' : 'text-[#dc2626]'}`}>{st.overall}</span>
                  </td>
                  {st.scores.map((s, j) => (
                    <td key={j} className="px-4 py-3 text-xs">
                      <span className={`font-bold ${s >= 70 ? 'text-[#16a34a]' : s >= 50 ? 'text-[#d97706]' : 'text-[#dc2626]'}`}>{s}</span>
                    </td>
                  ))}
                  <td className="px-4 py-3 text-xs text-red-500">{st.weak.join('、') || '-'}</td>
                  <td className="px-4 py-3 text-xs text-green-600">{st.strong.join('、')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {(data?.students ?? []).length === 0 && (
          <div className="text-center py-12 text-[#8a8a9e]">暂无学生评估数据</div>
        )}
      </div>
    </div>
  );
}
