'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, BarChart3, BookOpen, Brain, CheckCircle2, Code2, Database, FileCheck2, GraduationCap, Layers3, MessageCircle, Network, NotebookPen, ShieldCheck, Sparkles, Users } from 'lucide-react';

const features = [
  { icon: Brain, title: '十维学情画像', desc: '结合测评、学习记录与对话信息识别能力基础、薄弱知识点和学习偏好。' },
  { icon: BookOpen, title: '多资源学习空间', desc: '每一讲统一组织讲义、思维导图、代码示例、练习题和学习路径。' },
  { icon: CheckCircle2, title: '题库与错题练习', desc: '支持知识点练习、难度分级、错题重练和掌握度跟踪。' },
  { icon: MessageCircle, title: '课程资料 AI 导学', desc: '检索本地课程知识库和实验资料回答问题，并展示实际引用来源。' },
  { icon: NotebookPen, title: '学习笔记', desc: '按课程和分类记录学习内容，支持搜索、编辑与学习空间快速笔记。' },
  { icon: Code2, title: '代码运行与修复', desc: '运行课程相关 Python 代码，查看报错并由 AI 辅助分析和修正。' },
];

export default function WelcomePage() {
  const [activeSection, setActiveSection] = useState('product');

  useEffect(() => {
    const sectionIds = ['product', 'features', 'roles'];
    const updateActiveSection = () => {
      const scrollBottom = window.scrollY + window.innerHeight;
      const pageBottom = document.documentElement.scrollHeight;
      if (pageBottom - scrollBottom <= 24) {
        setActiveSection('roles');
        return;
      }

      const marker = window.scrollY + 120;
      let current = sectionIds[0];
      for (const id of sectionIds) {
        const section = document.getElementById(id);
        if (section && section.offsetTop <= marker) current = id;
      }
      setActiveSection(current);
    };

    updateActiveSection();
    window.addEventListener('scroll', updateActiveSection, { passive: true });
    window.addEventListener('resize', updateActiveSection);
    return () => {
      window.removeEventListener('scroll', updateActiveSection);
      window.removeEventListener('resize', updateActiveSection);
    };
  }, []);

  const navClass = (section: string) => `relative py-5 transition-colors ${
    activeSection === section ? 'text-white' : 'text-white/65 hover:text-white'
  }`;

  return (
    <main className="min-h-screen scroll-smooth bg-[#f6fcfc] text-[#15343a]">
      <header className="sticky top-0 z-20 border-b border-[#b9d8d9]/80 bg-[#102126]/95 text-white backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 lg:px-10">
          <Link href="/welcome" className="flex items-center gap-2.5 text-[17px] font-semibold tracking-wide"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#12c9b8] to-[#078fc3]"><BookOpen className="h-4 w-4" /></span>LearnWeave 学习平台</Link>
          <nav className="hidden h-full items-center gap-12 text-[15px] font-medium lg:gap-16 md:flex">
            {[['product', '产品介绍'], ['features', '核心功能'], ['roles', '适用角色']].map(([section, label]) => (
              <a key={section} href={`#${section}`} className={navClass(section)}>
                {label}
                <span className={`absolute inset-x-0 bottom-0 h-0.5 rounded-full bg-[#27e0cd] transition-all ${activeSection === section ? 'scale-x-100 opacity-100' : 'scale-x-0 opacity-0'}`} />
              </a>
            ))}
          </nav>
          <Link href="/login" className="flex items-center gap-1.5 rounded-md bg-gradient-to-r from-[#12c9b8] to-[#078fc3] px-4 py-2 text-[15px] font-semibold text-white shadow-sm hover:opacity-90">登录 / 注册<ArrowRight className="h-4 w-4" /></Link>
        </div>
      </header>

      <section className="relative overflow-hidden border-b border-[#c8e5e4] bg-gradient-to-br from-[#18d7bd] via-[#09b9c0] to-[#078fc3]">
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(circle at 15% 20%, white 1px, transparent 1px), radial-gradient(circle at 80% 60%, white 1px, transparent 1px)', backgroundSize: '34px 34px, 52px 52px' }} />
        <div className="relative mx-auto grid min-h-[590px] max-w-7xl items-center gap-10 px-5 py-16 lg:grid-cols-[0.9fr_1.1fr] lg:px-10">
          <div className="max-w-xl text-white">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/40 bg-white/15 px-3 py-1.5 text-xs font-medium backdrop-blur"><Sparkles className="h-3.5 w-3.5" />面向课程学习的智能学习系统</div>
            <h1 className="text-4xl font-semibold leading-tight tracking-tight md:text-5xl">LearnWeave 学习平台<br /><span className="text-[#dffff9]">个性化 AI 学习空间</span></h1>
            <p className="mt-6 max-w-lg text-[17px] leading-8 text-white/90">围绕课程资料组织学习内容，连接学情画像、学习空间、题库练习、智能笔记与 AI 导学，让每一次学习都有路径、有依据、有反馈。</p>
            <div className="mt-8 flex flex-wrap gap-3"><Link href="/login" className="flex items-center gap-2 rounded-md bg-white px-5 py-3 text-sm font-semibold text-[#087f89] shadow-lg hover:bg-[#f1fffd]">立即体验<ArrowRight className="h-4 w-4" /></Link><a href="#features" className="flex items-center gap-2 rounded-md border border-white/60 px-5 py-3 text-sm font-semibold text-white hover:bg-white/10">了解更多</a></div>
            <div className="mt-10 flex items-center gap-6 text-xs text-white/75"><span className="flex items-center gap-1.5"><ShieldCheck className="h-4 w-4" />课程依据可追溯</span><span className="flex items-center gap-1.5"><Layers3 className="h-4 w-4" />多资源协同</span></div>
          </div>
          <div className="relative hidden min-h-[390px] lg:block" aria-label="课程学习场景插图">
            <div className="absolute right-4 top-8 h-64 w-[420px] rotate-[-5deg] rounded-2xl border border-white/60 bg-white/20 p-5 shadow-2xl backdrop-blur-sm"><div className="flex items-center gap-3 border-b border-white/30 pb-4"><div className="h-9 w-9 rounded-lg bg-white/70" /><div className="h-3 w-36 rounded-full bg-white/70" /></div><div className="mt-5 grid grid-cols-[1fr_0.65fr] gap-4"><div className="space-y-3 rounded-xl bg-white/35 p-4"><div className="h-3 w-24 rounded-full bg-white/70" /><div className="h-20 rounded-lg bg-white/40" /><div className="h-3 w-40 rounded-full bg-white/55" /><div className="h-3 w-28 rounded-full bg-white/45" /></div><div className="rounded-xl bg-[#eafffb]/70 p-4"><BarChart3 className="h-7 w-7 text-[#078f9b]" /><div className="mt-5 h-24 rounded-lg bg-gradient-to-t from-[#12c9b8]/70 to-white/30" /></div></div></div>
            <div className="absolute bottom-4 left-3 flex h-44 w-56 items-center justify-center rounded-2xl border border-white/60 bg-white/25 shadow-xl backdrop-blur-sm"><BookOpen className="h-24 w-24 text-white/90" /></div><div className="absolute bottom-0 right-0 flex h-24 w-24 items-center justify-center rounded-2xl border border-white/60 bg-white/30 shadow-xl backdrop-blur-sm"><Brain className="h-11 w-11 text-white" /></div><div className="absolute left-1/2 top-1/2 h-4 w-4 rounded-full bg-white shadow-[0_0_22px_8px_rgba(255,255,255,0.55)]" />
          </div>
        </div>
      </section>

      <section id="product" className="border-b border-[#c8e5e4] bg-white">
        <div className="mx-auto grid max-w-7xl gap-12 px-5 py-16 lg:grid-cols-[0.85fr_1.15fr] lg:px-10">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[#078f9b]">Product introduction</div>
            <h2 className="mt-2 text-3xl font-semibold leading-tight text-[#15343a]">面向真实课程资料的<br />个性化学习多智能体系统</h2>
            <p className="mt-5 text-[15px] leading-7 text-[#58777c]">LearnWeave 不是通用聊天工具。平台以课程知识库和实验手册为内容依据，通过学情诊断、知识检索、资源生成、交叉审核与学习反馈等智能体协同，为学生生成与课程讲次一致的学习资源。</p>
            <p className="mt-3 text-[15px] leading-7 text-[#58777c]">学生完成学习和练习后，学习记录会持续更新画像与掌握度；教师可以审核生成资源、查看班级学情并进行教学干预；管理员负责用户权限、知识库、智能体和质量指标治理。</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {[{ icon: Database, title: '课程知识库接地', desc: '本地课程讲义、实验资料与知识点作为生成和答疑依据。' }, { icon: Network, title: '多智能体协同', desc: '诊断、检索、讲义、导图、代码、练习与审核 Agent 协同工作。' }, { icon: FileCheck2, title: '内容审核与防幻觉', desc: '检查知识引用、课程一致性、导图结构和 Python 代码有效性。' }, { icon: BarChart3, title: '教学学习闭环', desc: '学习行为进入画像与教师分析，支持后续资源推荐和教学干预。' }].map(({ icon: Icon, title, desc }) => <div key={title} className="rounded-xl border border-[#c8e5e4] bg-[#f7fdfd] p-5"><div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#e8fbfa] text-[#078f9b]"><Icon className="h-5 w-5" /></div><h3 className="mt-4 text-[17px] font-semibold text-[#18343a]">{title}</h3><p className="mt-2 text-[15px] leading-7 text-[#667f83]">{desc}</p></div>)}
          </div>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-7xl px-5 py-16 lg:px-10"><div className="mb-8 text-center"><div className="text-xs font-semibold uppercase tracking-[0.18em] text-[#078f9b]">Core capabilities</div><h2 className="mt-2 text-3xl font-semibold text-[#15343a]">学生端核心功能</h2><p className="mt-3 text-[15px] text-[#667f83]">覆盖学前诊断、课程学习、练习巩固、代码实践、答疑和笔记沉淀。</p></div><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{features.map(({ icon: Icon, title, desc }) => <div key={title} className="rounded-xl border border-[#b9d8d9] bg-white p-6 shadow-[var(--lm-shadow)]"><div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#e8fbfa] text-[#078f9b]"><Icon className="h-5 w-5" /></div><h3 className="mt-5 text-lg font-semibold text-[#18343a]">{title}</h3><p className="mt-2 text-[15px] leading-7 text-[#667f83]">{desc}</p></div>)}</div></section>

      <section id="roles" className="border-y border-[#c8e5e4] bg-white"><div className="mx-auto max-w-7xl px-5 py-14 lg:px-10"><div className="mb-8 text-center"><div className="text-xs font-semibold uppercase tracking-[0.18em] text-[#078f9b]">Target users</div><h2 className="mt-2 text-2xl font-semibold text-[#15343a]">适合使用 LearnWeave 的人群</h2><p className="mt-3 text-[15px] text-[#667f83]">面向需要课程化学习、个性化辅导和教学数据支持的学习者与教育工作者。</p></div><div className="grid gap-4 md:grid-cols-3"><div className="rounded-xl border border-[#c8e5e4] bg-[#f7fdfd] p-6"><GraduationCap className="h-6 w-6 text-[#078fc3]" /><h3 className="mt-4 text-[17px] font-semibold">需要系统学习的学生</h3><p className="mt-2 text-[15px] leading-7 text-[#667f83]">适合零基础、基础不牢或希望按课程路径提升 Python 与数据分析能力的学习者。</p></div><div className="rounded-xl border border-[#c8e5e4] bg-[#f7fdfd] p-6"><Brain className="h-6 w-6 text-[#0aa6a6]" /><h3 className="mt-4 text-[17px] font-semibold">需要个性化辅导的学习者</h3><p className="mt-2 text-[15px] leading-7 text-[#667f83]">适合希望根据自身薄弱点获得讲义、导图、练习、代码和课程答疑的人群。</p></div><div className="rounded-xl border border-[#c8e5e4] bg-[#f7fdfd] p-6"><Users className="h-6 w-6 text-[#087f9b]" /><h3 className="mt-4 text-[17px] font-semibold">开展数字化教学的教师</h3><p className="mt-2 text-[15px] leading-7 text-[#667f83]">适合需要查看班级学情、审核 AI 学习资源并对风险学生进行教学干预的教师。</p></div></div></div></section>

      <footer className="mx-auto flex max-w-7xl items-center justify-between px-5 py-8 text-xs text-[#82979a] lg:px-10"><span>LearnWeave 学习平台</span><Link href="/login" className="font-medium text-[#078f9b] hover:underline">进入平台</Link></footer>
    </main>
  );
}
