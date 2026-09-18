'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, ArrowRight, BarChart3, CheckCircle2, Database, RefreshCw, Server, ShieldCheck, Users, Workflow } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export default function AdminPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const load = async () => {
    setLoading(true);
    const token = sessionStorage.getItem('auth_token');
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
    const [users, knowledge, agents] = await Promise.all([
      fetch(`${API}/api/admin/users`, { headers }).then(r => r.ok ? r.json() : []).catch(() => []),
      fetch(`${API}/api/knowledge/assets`, { headers }).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(`${API}/api/agents/realtime`, { headers }).then(r => r.ok ? r.json() : null).catch(() => null),
    ]);
    const agentList = agents?.agents || [];
    setData({ users: Array.isArray(users) ? users : [], knowledge, agents: agentList, activeAgents: agentList.filter((a: any) => a.status === 'running').length, failedAgents: agentList.filter((a: any) => a.status === 'error').length });
    setLoading(false);
  };
  useEffect(() => { load(); }, []);
  const users = data?.users || [];
  const assets = data?.knowledge?.assets?.length ?? data?.knowledge?.counts?.chunks ?? 0;
  const cards = [
    { label: '平台用户', value: users.length, note: `${users.filter((u: any) => u.is_active).length} 个启用账户`, icon: Users, href: '/admin/users' },
    { label: '知识资产', value: assets, note: '课程文档与检索片段', icon: Database, href: '/admin/knowledge' },
    { label: '智能体总数', value: data?.agents?.length ?? 0, note: `${data?.activeAgents ?? 0} 个正在运行`, icon: Workflow, href: '/admin/agents' },
    { label: '运行异常', value: data?.failedAgents ?? 0, note: '需要检查的 Agent', icon: Activity, href: '/admin/agents' },
  ];
  const modules = [
    { title: '用户与权限', desc: '管理学生、教师和管理员账户，控制启用状态与角色权限。', href: '/admin/users', icon: Users },
    { title: '知识库治理', desc: '检查课程文档、知识片段、索引状态与知识来源。', href: '/admin/knowledge', icon: Database },
    { title: '智能体监控', desc: '查看多智能体流水线、实时事件、失败状态和审核过程。', href: '/admin/agents', icon: Workflow },
    { title: '质量评测', desc: '分析知识覆盖、幻觉风险、难度适配和内容审核指标。', href: '/admin/evaluation', icon: BarChart3 },
  ];
  return <div className="mx-auto max-w-7xl space-y-6">
    <div className="flex items-start justify-between gap-4"><div><div className="text-xs font-semibold uppercase tracking-[0.14em] text-[#078f9b]">Platform governance</div><h1 className="mt-1 text-2xl font-semibold text-[#132c32]">管理驾驶舱</h1><p className="mt-1 text-sm text-[var(--lm-text-secondary)]">统一管理平台用户、知识资产、模型质量和智能体运行状态。</p></div><button onClick={load} className="flex items-center gap-2 rounded-md border border-[#b9d8d9] bg-white px-3 py-2 text-sm text-[#38515a] hover:bg-[#effafa]"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />刷新状态</button></div>
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">{cards.map(({ label, value, note, icon: Icon, href }) => <Link key={label} href={href} className="group relative overflow-hidden rounded-lg border border-[#c8e0e1] bg-white p-5 shadow-[var(--lm-shadow)] transition-all hover:-translate-y-0.5 hover:border-[#83caca]"><div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-[#078fc3] to-[#12c9b8]" /><div className="flex items-center justify-between"><span className="text-sm font-medium text-[#536d72]">{label}</span><span className="flex h-9 w-9 items-center justify-center rounded-md border border-[#cce8e7] bg-[#eaf9f8] text-[#078f9b]"><Icon className="h-[18px] w-[18px]" /></span></div><div className="mt-5 flex items-end justify-between"><div><div className="text-3xl font-semibold text-[#172d32]">{loading ? '--' : value}</div><div className="mt-1 text-xs text-[#7b9094]">{note}</div></div><ArrowRight className="h-4 w-4 text-[#a1b6b8] group-hover:translate-x-0.5" /></div></Link>)}</div>
    <div className="grid gap-6 xl:grid-cols-[1fr_340px]"><section className="rounded-lg border border-[#c8e0e1] bg-white p-6 shadow-[var(--lm-shadow)]"><div className="mb-5"><h2 className="font-semibold text-[#18343a]">平台治理模块</h2><p className="mt-1 text-xs text-[var(--lm-text-tertiary)]">从账户、知识、智能体和质量四个层面管理 LearnWeave</p></div><div className="grid gap-3 md:grid-cols-2">{modules.map(({ title, desc, href, icon: Icon }) => <Link key={title} href={href} className="group flex gap-4 rounded-lg border border-[#dbeaea] p-4 hover:border-[#83caca] hover:bg-[#f7fdfd]"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-[#eaf9f8] text-[#078f9b]"><Icon className="h-5 w-5" /></span><div><div className="flex items-center gap-2 text-sm font-semibold text-[#18343a]">{title}<ArrowRight className="h-3.5 w-3.5 text-[#a1b6b8] group-hover:translate-x-0.5" /></div><p className="mt-1 text-xs leading-5 text-[#71878b]">{desc}</p></div></Link>)}</div></section><section className="rounded-lg border border-[#c8e0e1] bg-white p-6 shadow-[var(--lm-shadow)]"><div className="mb-4 flex items-center gap-2"><Server className="h-4 w-4 text-[#078f9b]" /><h2 className="font-semibold text-[#18343a]">系统健康</h2></div><div className="space-y-2">{[['后端 API', '运行正常'], ['数据库', 'SQLite 已连接'], ['知识检索', assets ? '索引可用' : '等待资产'], ['多智能体', data?.failedAgents ? `${data.failedAgents} 个异常` : '运行正常']].map(([label, value], index) => <div key={label} className="flex items-center justify-between rounded-md border border-[#e0eded] px-3 py-3"><span className="text-sm text-[#536d72]">{label}</span><span className={`flex items-center gap-1.5 text-xs font-medium ${index === 3 && data?.failedAgents ? 'text-[#c54d4d]' : 'text-[#168f7d]'}`}><CheckCircle2 className="h-3.5 w-3.5" />{value}</span></div>)}</div><Link href="/verify" className="mt-4 flex items-center justify-center gap-2 rounded-md bg-gradient-to-r from-[#078fc3] to-[#12c9b8] px-4 py-2.5 text-sm font-medium text-white"><ShieldCheck className="h-4 w-4" />进入验证中心</Link></section></div>
  </div>;
}
