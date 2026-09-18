'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ArrowRight, BarChart3, BookOpen, Brain, Check, Code2, GraduationCap, Layers3, LineChart, LockKeyhole, LogIn, Shield, Sparkles, User, UserPlus, Users } from 'lucide-react';

const ROLE_CARDS = [
  { id: 'student' as const, icon: GraduationCap, label: '学生端', desc: '课程学习 · AI 导学', color: '#078fc3', soft: '#e9f8fb' },
  { id: 'teacher' as const, icon: Users, label: '教师端', desc: '班级分析 · 资源审核', color: '#0aa6a6', soft: '#e9f9f7' },
  { id: 'admin' as const, icon: Shield, label: '管理员端', desc: '平台治理 · 质量监控', color: '#087f9b', soft: '#e9f7f8' },
];

export default function LoginPage() {
  const router = useRouter();
  const { login, register, isAuthenticated, isLoading, isNewUser } = useAuth();
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [role, setRole] = useState<'student' | 'teacher' | 'admin'>('student');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) router.push(role === 'admin' ? '/admin' : role === 'teacher' ? '/teacher' : isNewUser ? '/profile' : '/');
  }, [isAuthenticated, isLoading, isNewUser, role, router]);

  if (isLoading) return <div className="flex min-h-screen items-center justify-center bg-[#f2fbfb] text-sm text-[#71878b]">加载中...</div>;
  if (isAuthenticated) return null;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault(); setError(''); setLoading(true);
    try {
      if (isRegisterMode) {
        if (password !== confirmPassword) { setError('两次输入的密码不一致'); setLoading(false); return; }
        if (password.length < 6) { setError('密码长度不能少于6位'); setLoading(false); return; }
        await register({ username, password, role: role === 'teacher' || role === 'admin' ? 'admin' : 'user' });
      } else await login({ username, password });
      sessionStorage.setItem('auth_portal', role);
    } catch (err: any) {
      if (err.response?.status === 409) setError('该用户名已被占用');
      else if (err.response?.status === 401) setError('用户名或密码错误');
      else if (!err.response) setError('后端服务未启动，请先启动 8000 端口服务');
      else setError('操作失败，请稍后重试');
    } finally { setLoading(false); }
  };

  const activeRole = ROLE_CARDS.find(item => item.id === role)!;
  return <main className="relative min-h-screen overflow-hidden bg-[#f5fcfc] text-[#163238]">
    <div className="pointer-events-none absolute inset-0 bg-[url('/images/login-education-background.svg')] bg-cover bg-center bg-no-repeat" />
    <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-white/35 via-white/18 to-white/24" />
    <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_12%_20%,rgba(8,184,189,0.14),transparent_28%),radial-gradient(circle_at_88%_8%,rgba(7,143,195,0.12),transparent_30%)]" />
    <div className="pointer-events-none absolute -left-24 bottom-[-140px] h-80 w-80 rounded-full border border-[#bce7e2] bg-[#dff8f3]/50" />
    <div className="pointer-events-none absolute right-[-90px] top-[-100px] h-72 w-72 rounded-full border border-[#b8e0eb] bg-[#e3f8fb]/60" />

    <div className="relative mx-auto grid min-h-screen max-w-[1380px] items-center gap-7 px-5 py-6 lg:grid-cols-2 lg:px-8 lg:[&_.text-xs]:text-sm lg:[&_.text-sm]:text-base lg:[&>section:last-child]:h-[620px] lg:[&>section:last-child]:min-h-0 lg:[&>section:last-child]:rounded-2xl lg:[&>section:last-child]:border lg:[&>section:last-child]:border-[#b9dfe0] lg:[&>section:last-child]:bg-white/42 lg:[&>section:last-child]:px-9 lg:[&>section:last-child]:py-6 lg:[&>section:last-child]:shadow-[0_24px_70px_rgba(6,91,103,0.1)] lg:[&>section:last-child]:backdrop-blur-[2px] lg:[&>section:last-child_.mb-7]:mb-4 lg:[&>section:last-child_.mb-6]:mb-4 lg:[&>section:last-child_.mb-5]:mb-3 lg:[&>section:last-child_.mt-5]:mt-3 lg:[&>section:last-child_.p-7]:p-5">
      <section className="relative hidden h-[620px] min-h-0 flex-col justify-start gap-3 overflow-hidden rounded-2xl border border-[#b9dfe0] bg-gradient-to-br from-[#e9fcf9] via-[#e8f8fb] to-[#dff3fa] p-8 shadow-[0_24px_70px_rgba(6,91,103,0.1)] [&_.mt-44]:!mt-6 [&_.mt-8]:!mt-5 lg:flex">
        <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full border border-[#bce7e2] bg-[#dff8f3]/70" />
        <div><div className="relative z-10 flex items-center gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-[#12c9b8] to-[#078fc3] text-white shadow-sm"><BookOpen className="h-5 w-5" /></div><span className="text-lg font-semibold tracking-wide text-[#12353b]">LearnWeave</span></div><div className="relative z-10 mt-44 max-w-xl"><div className="mb-4 inline-flex items-center gap-2 rounded-md border border-[#bce7e2] bg-white/80 px-3 py-1.5 text-xs font-medium text-[#087f89]"><Sparkles className="h-3.5 w-3.5" />个性化学习空间</div><h1 className="text-4xl font-semibold leading-tight tracking-tight text-[#15343a]">把课程资料，<br /><span className="bg-gradient-to-r from-[#078fc3] to-[#0aa6a6] bg-clip-text text-transparent">编织成可执行的学习路径</span></h1><p className="mt-5 max-w-md text-[15px] leading-7 text-[#58777c]">从讲义、思维导图到练习与代码，围绕真实课程资料组织学习内容，并用学情画像持续调整学习节奏。</p></div>
          <div className="relative mt-8 max-w-[520px] rounded-xl border border-[#b9d8d9] bg-white/85 p-4 shadow-[0_14px_35px_rgba(6,91,103,0.08)]"><div className="flex items-center justify-between border-b border-[#e2eeee] pb-3"><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-md bg-[#e8fbfa] text-[#078f9b]"><BookOpen className="h-4 w-4" /></span><div><div className="text-xs font-semibold">Python环境搭建与Jupyter入门</div><div className="text-[10px] text-[#8aa0a3]">讲义 · 导图 · 代码 · 练习</div></div></div><span className="rounded-md bg-[#e7f8f4] px-2 py-1 text-[10px] font-medium text-[#168f7d]">学习中</span></div><div className="mt-4 grid grid-cols-[1fr_120px] gap-3"><div className="space-y-2"><div className="h-2.5 w-3/4 rounded-full bg-[#cde9e8]" /><div className="h-2.5 w-full rounded-full bg-[#e2f1f1]" /><div className="h-2.5 w-5/6 rounded-full bg-[#e2f1f1]" /><div className="mt-4 flex gap-2"><span className="flex h-9 w-9 items-center justify-center rounded-md bg-[#eaf9f8] text-[#078f9b]"><Brain className="h-4 w-4" /></span><span className="flex h-9 w-9 items-center justify-center rounded-md bg-[#e9f8fb] text-[#078fc3]"><Code2 className="h-4 w-4" /></span><span className="flex h-9 w-9 items-center justify-center rounded-md bg-[#eaf9f8] text-[#0aa6a6]"><Layers3 className="h-4 w-4" /></span></div></div><div className="rounded-lg bg-[#f0fbfa] p-3"><BarChart3 className="h-5 w-5 text-[#078f9b]" /><div className="mt-4 flex h-16 items-end gap-1.5"><span className="h-7 w-3 rounded-sm bg-[#a9dfdb]" /><span className="h-11 w-3 rounded-sm bg-[#62cbc4]" /><span className="h-14 w-3 rounded-sm bg-[#078fc3]" /><span className="h-9 w-3 rounded-sm bg-[#12c9b8]" /></div></div></div></div>
        </div>
        <div className="grid grid-cols-3 gap-3"><div className="rounded-lg border border-[#c8e5e4] bg-white/80 p-4"><Brain className="h-5 w-5 text-[#078f9b]" /><div className="mt-4 text-sm font-semibold">AI 导学</div><div className="mt-1 text-xs text-[#82979a]">基于课程资料答疑</div></div><div className="rounded-lg border border-[#c8e5e4] bg-white/80 p-4"><Layers3 className="h-5 w-5 text-[#078fc3]" /><div className="mt-4 text-sm font-semibold">资源联动</div><div className="mt-1 text-xs text-[#82979a]">讲义与导图同步</div></div><div className="rounded-lg border border-[#c8e5e4] bg-white/80 p-4"><LineChart className="h-5 w-5 text-[#0aa6a6]" /><div className="mt-4 text-sm font-semibold">学情反馈</div><div className="mt-1 text-xs text-[#82979a]">学习进度可追踪</div></div></div>
      </section>

      <section className="mx-auto w-full max-w-[480px] lg:max-w-none"><div className="mb-7 flex items-center gap-3 lg:hidden"><div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-[#12c9b8] to-[#078fc3] text-white"><BookOpen className="h-5 w-5" /></div><span className="text-lg font-semibold">LearnWeave</span></div><div className="mb-6"><div className="text-xs font-semibold uppercase tracking-[0.16em] text-[#078f9b]">Welcome back</div><h2 className="mt-2 text-3xl font-semibold text-[#15343a]">登录学习平台</h2><p className="mt-2 text-base text-[#647f83]">选择使用端，进入对应工作空间。</p></div>
        <div className="mb-5 grid grid-cols-3 gap-2">{ROLE_CARDS.map(card => { const Icon = card.icon; const active = role === card.id; return <button key={card.id} onClick={() => setRole(card.id)} className={`relative rounded-lg border p-3 text-left transition-all duration-200 ${active ? 'border-[#64c5c5] bg-white shadow-[0_8px_22px_rgba(6,91,103,0.09)] -translate-y-0.5' : 'border-[#d6e8e8] bg-white/55 hover:border-[#aadada] hover:bg-white/80'}`}><div className="flex items-center justify-between"><span className="flex h-8 w-8 items-center justify-center rounded-md" style={{ background: active ? card.soft : '#edf6f6', color: active ? card.color : '#8aa1a4' }}><Icon className="h-4 w-4" /></span>{active && <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#12bba9] text-white"><Check className="h-3 w-3" /></span>}</div><div className="mt-3 text-sm font-semibold text-[#29464b]">{card.label}</div><div className="mt-1 text-xs leading-5 text-[#71878b]">{card.desc}</div></button>; })}</div>
        <div className="rounded-xl border border-[#a9d5d6] bg-white/90 p-7 shadow-[0_20px_55px_rgba(6,91,103,0.1)] backdrop-blur-sm"><div className="mb-6 flex items-center justify-between"><div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full" style={{ background: activeRole.color }} /><span className="text-base font-semibold text-[#29464b]">{isRegisterMode ? '创建账号' : '登录'} {activeRole.label}</span></div><span className="text-xs text-[#82979a]">安全访问</span></div>{error && <div className="mb-4 rounded-md border border-[#efcaca] bg-[#fff7f7] px-3 py-2.5 text-sm text-[#bf5555]">{error}</div>}<form onSubmit={handleSubmit} className="space-y-4"><label className="block"><span className="mb-1.5 block text-sm font-medium text-[#4d696e]">用户名</span><div className="relative"><User className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8aa4a7]" /><input value={username} onChange={e => setUsername(e.target.value)} className="h-12 w-full rounded-lg border border-[#c8dfe0] bg-[#fbfefe] pl-11 pr-4 text-base text-[#17343a] outline-none transition focus:border-[#08b8bd] focus:bg-white focus:ring-4 focus:ring-[#08b8bd]/10" placeholder="请输入用户名" required minLength={3} /></div></label><label className="block"><span className="mb-1.5 block text-sm font-medium text-[#4d696e]">密码</span><div className="relative"><LockKeyhole className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8aa4a7]" /><input type="password" value={password} onChange={e => setPassword(e.target.value)} className="h-12 w-full rounded-lg border border-[#c8dfe0] bg-[#fbfefe] pl-11 pr-4 text-base text-[#17343a] outline-none transition focus:border-[#08b8bd] focus:bg-white focus:ring-4 focus:ring-[#08b8bd]/10" placeholder={isRegisterMode ? '密码不少于6位' : '请输入密码'} required minLength={6} /></div></label>{isRegisterMode && <label className="block"><span className="mb-1.5 block text-sm font-medium text-[#4d696e]">确认密码</span><div className="relative"><LockKeyhole className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8aa4a7]" /><input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} className="h-12 w-full rounded-lg border border-[#c8dfe0] bg-[#fbfefe] pl-11 pr-4 text-base text-[#17343a] outline-none transition focus:border-[#08b8bd] focus:bg-white focus:ring-4 focus:ring-[#08b8bd]/10" placeholder="再次输入密码" required minLength={6} /></div></label>}<button type="submit" disabled={loading} className="flex h-12 w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#078fc3] to-[#12c9b8] text-base font-semibold text-white shadow-[0_8px_20px_rgba(8,169,178,0.22)] transition hover:-translate-y-0.5 hover:shadow-[0_12px_24px_rgba(8,169,178,0.26)] disabled:opacity-50">{loading ? '处理中...' : isRegisterMode ? <><UserPlus className="h-4 w-4" />创建账号</> : <><LogIn className="h-4 w-4" />立即登录<ArrowRight className="h-4 w-4" /></>}</button></form><div className="mt-5 text-center text-sm text-[#71878b]">{isRegisterMode ? <>已有账号？ <button onClick={() => { setIsRegisterMode(false); setError(''); }} className="font-semibold text-[#078f9b] hover:underline">去登录</button></> : <>还没有账号？ <button onClick={() => { setIsRegisterMode(true); setError(''); }} className="font-semibold text-[#078f9b] hover:underline">立即注册</button></>}</div></div>
        <p className="mt-5 flex items-center justify-center gap-1.5 text-center text-sm text-[#82979a]"><Shield className="h-4 w-4" />课程资料、学习记录与权限分端管理</p>
      </section>
    </div>
  </main>;
}
