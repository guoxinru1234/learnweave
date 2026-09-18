'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, ArrowRight, BarChart3, BookOpen, CheckCircle2, ClipboardCheck, FileText, RefreshCw, ShieldCheck, Users } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
const DIMENSIONS = ['理论基础', '编程能力', '实践操作', '问题排查', '数据思维', '自学能力'];

export default function TeacherOverview() {
  const [dashboard, setDashboard] = useState<any>(null);
  const [reviews, setReviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    const token = sessionStorage.getItem('auth_token');
    if (!token) { setError('请先登录教师账号'); setLoading(false); return; }
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const [dashboardRes, reviewRes] = await Promise.all([
        fetch(`${API}/api/teacher/dashboard`, { headers }),
        fetch(`${API}/api/teacher/review/list`, { headers }),
      ]);
      if (!dashboardRes.ok) throw new Error('当前账号没有教师权限');
      setDashboard(await dashboardRes.json());
      if (reviewRes.ok) {
        const data = await reviewRes.json();
        setReviews(Array.isArray(data) ? data : data.resources || data.items || []);
      }
    } catch (err: any) { setError(err.message || '教师数据加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <div className="flex min-h-[60vh] items-center justify-center text-sm text-[var(--lm-text-tertiary)]">正在加载教学数据...</div>;
  if (error) return <div className="mx-auto max-w-6xl py-10"><div className="rounded-lg border border-[#c8e0e1] bg-white p-10 text-center shadow-[var(--lm-shadow)]"><Users className="mx-auto mb-3 h-10 w-10 text-[#8eb8ba]" /><h1 className="text-lg font-semibold text-[#18343a]">教师工作台暂不可用</h1><p className="mt-2 text-sm text-[var(--lm-text-secondary)]">{error}</p></div></div>;

  const students = dashboard?.students || [];
  const risks = dashboard?.at_risk_students || [];
  const dimensions = dashboard?.class_dim_averages || [0, 0, 0, 0, 0, 0];
  const pending = dashboard?.pending_review ?? reviews.filter(item => !item.review_status || item.review_status === 'pending_review').length;
  const statCards = [
    { label: '班级学生', value: dashboard?.student_count ?? students.length, note: `${dashboard?.active_count ?? 0} 人本周活跃`, icon: Users },
    { label: '任务完成率', value: `${dashboard?.completion_rate ?? 0}%`, note: '课程任务总体进度', icon: CheckCircle2 },
    { label: '待审核资源', value: pending, note: '讲义、导图与练习', icon: ClipboardCheck },
    { label: '需关注学生', value: risks.length, note: '建议进行学习干预', icon: AlertTriangle },
  ];
  const actions = [
    { title: '审核 AI 资源', desc: '核对知识依据、导图结构、代码与练习', href: '/teacher/reports', icon: ShieldCheck, badge: pending ? `${pending} 项待处理` : '暂无待办' },
    { title: '查看班级学情', desc: '比较知识掌握度并定位薄弱知识点', href: '/teacher/class-learning', icon: BarChart3, badge: `${risks.length} 人需关注` },
    { title: '管理学生', desc: '查看学生画像、学习记录与个体表现', href: '/teacher/students', icon: Users, badge: `${students.length} 名学生` },
    { title: '教学报告', desc: '查看成绩、学习进度与课程资源统计', href: '/teacher/resources', icon: FileText, badge: '课程分析' },
  ];

  return <div className="mx-auto max-w-7xl space-y-6">
    <div className="flex items-start justify-between gap-4"><div><div className="text-xs font-semibold uppercase tracking-[0.14em] text-[#078f9b]">Teaching workspace</div><h1 className="mt-1 text-2xl font-semibold text-[#132c32]">教学工作台</h1><p className="mt-1 text-sm text-[var(--lm-text-secondary)]">审核学习资源、识别风险学生并跟踪班级学习效果。</p></div><button onClick={load} className="flex items-center gap-2 rounded-md border border-[#b9d8d9] bg-white px-3 py-2 text-sm text-[#38515a] hover:bg-[#effafa]"><RefreshCw className="h-4 w-4" />刷新数据</button></div>

    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">{statCards.map(({ label, value, note, icon: Icon }) => <div key={label} className="relative overflow-hidden rounded-lg border border-[#c8e0e1] bg-white p-5 shadow-[var(--lm-shadow)]"><div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-[#078fc3] to-[#12c9b8]" /><div className="flex items-center justify-between"><span className="text-sm font-medium text-[#536d72]">{label}</span><span className="flex h-9 w-9 items-center justify-center rounded-md border border-[#cce8e7] bg-[#eaf9f8] text-[#078f9b]"><Icon className="h-[18px] w-[18px]" /></span></div><div className="mt-5 text-3xl font-semibold text-[#172d32]">{value}</div><div className="mt-1 text-xs text-[#7b9094]">{note}</div></div>)}</div>

    <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
      <section className="rounded-lg border border-[#c8e0e1] bg-white p-6 shadow-[var(--lm-shadow)]"><div className="mb-5 flex items-center justify-between"><div><h2 className="font-semibold text-[#18343a]">班级能力概览</h2><p className="mt-1 text-xs text-[var(--lm-text-tertiary)]">根据学生画像与学习行为汇总</p></div><Link href="/teacher/class-learning" className="flex items-center gap-1 text-xs font-medium text-[#078f9b]">查看详情<ArrowRight className="h-3.5 w-3.5" /></Link></div><div className="space-y-4">{DIMENSIONS.map((label, index) => { const score = Math.round(Number(dimensions[index]) || 0); return <div key={label}><div className="mb-1.5 flex items-center justify-between text-sm"><span className="text-[#496267]">{label}</span><span className="font-semibold text-[#18343a]">{score}</span></div><div className="h-2 overflow-hidden rounded-sm bg-[#e8f2f2]"><div className="h-full bg-gradient-to-r from-[#078fc3] to-[#12c9b8]" style={{ width: `${Math.min(score, 100)}%` }} /></div></div>; })}</div></section>
      <section className="rounded-lg border border-[#c8e0e1] bg-white p-6 shadow-[var(--lm-shadow)]"><div className="mb-4 flex items-center justify-between"><h2 className="font-semibold text-[#18343a]">教学干预</h2><Link href="/teacher/students" className="text-xs font-medium text-[#078f9b]">学生管理</Link></div>{risks.length ? <div className="space-y-2">{risks.slice(0, 5).map((student: any) => <div key={student.id || student.username} className="flex items-center justify-between rounded-md border border-[#f0d3d3] bg-[#fff8f8] px-4 py-3"><div><div className="text-sm font-medium text-[#493b3b]">{student.name || student.username}</div><div className="mt-0.5 text-xs text-[#9a6767]">综合掌握度低于班级目标</div></div><span className="text-sm font-semibold text-[#c54d4d]">{student.overall ?? '--'}</span></div>)}</div> : <div className="flex min-h-[220px] flex-col items-center justify-center text-center"><CheckCircle2 className="mb-3 h-9 w-9 text-[#19a990]" /><div className="text-sm font-medium text-[#38515a]">暂无高风险学生</div><div className="mt-1 text-xs text-[var(--lm-text-tertiary)]">班级学习状态总体稳定</div></div>}</section>
    </div>

    <section><div className="mb-3 flex items-center gap-2"><BookOpen className="h-4 w-4 text-[#078f9b]" /><h2 className="font-semibold text-[#18343a]">常用教学流程</h2></div><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{actions.map(({ title, desc, href, icon: Icon, badge }) => <Link key={title} href={href} className="group rounded-lg border border-[#c8e0e1] bg-white p-5 transition-all hover:-translate-y-0.5 hover:border-[#83caca] hover:shadow-[var(--lm-shadow)]"><div className="flex items-start justify-between"><span className="flex h-9 w-9 items-center justify-center rounded-md bg-[#eaf9f8] text-[#078f9b]"><Icon className="h-[18px] w-[18px]" /></span><ArrowRight className="h-4 w-4 text-[#a1b6b8] transition-transform group-hover:translate-x-0.5" /></div><h3 className="mt-4 text-sm font-semibold text-[#18343a]">{title}</h3><p className="mt-1 min-h-10 text-xs leading-5 text-[#71878b]">{desc}</p><div className="mt-3 text-xs font-medium text-[#078f9b]">{badge}</div></Link>)}</div></section>
  </div>;
}
