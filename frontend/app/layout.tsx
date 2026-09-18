// frontend/app/layout.tsx
'use client';

import { useState, useEffect, ReactNode } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Link from "next/link";
import { X, Bell, LayoutDashboard, Brain, BookOpen, FlaskConical, ScrollText, MessageSquare, Database, BarChart3, StickyNote, RefreshCw, LogOut, Shield, Settings, Activity, Users, AlertCircle, UsersRound } from 'lucide-react';
import "./globals.css";
import "./learnmate.css";

import { AgentProvider, useAgent, type AgentEvent } from "@/contexts/AgentContext";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import TomatoPet from "@/components/TomatoPet";

// ✅ 修改：AI 答疑链接从 /ai-chat 改为 /tutor（实际页面目录名）
const STUDENT_NAV = [
  { icon: LayoutDashboard, label: "学习工作台", href: "/" },
  { icon: Brain, label: "学情画像", href: "/profile" },
  { icon: BookOpen, label: "学习空间", href: "/learn/python-data-analysis" },
  { icon: ScrollText, label: "题库练习", href: "/quiz" },
  { icon: MessageSquare, label: "AI 导学", href: "/tutor" },
  { icon: StickyNote, label: "学习笔记", href: "/notes" },
  { icon: AlertCircle, label: "错题本", href: "/notes?category=wrong_question" },
  { icon: BarChart3, label: "学情评估", href: "/assessment" },
  { icon: UsersRound, label: "学习者讨论社区", href: "/community" },
  { icon: Database, label: "知识库", href: "/knowledge" },
];

const TEACHER_NAV = [
  { icon: LayoutDashboard, label: "教学总览", href: "/teacher" },
  { icon: BarChart3, label: "班级学情", href: "/teacher/class-learning" },
  { icon: Users, label: "学生管理", href: "/teacher/students" },
  { icon: BookOpen, label: "成绩分析", href: "/teacher/grades" },
  { icon: Shield, label: "资源审核", href: "/teacher/reports" },
  { icon: StickyNote, label: "教学报告", href: "/teacher/resources" },
  { icon: Database, label: "系统设置", href: "/teacher/settings" },
];

const ADMIN_NAV = [
  { icon: Settings, label: "系统管理", href: "/admin" },
  { icon: Users, label: "用户管理", href: "/admin/users" },
  { icon: Database, label: "知识库管理", href: "/admin/knowledge" },
  { icon: BarChart3, label: "质量评测", href: "/admin/evaluation" },
  { icon: Activity, label: "Agent 监控", href: "/admin/agents" },
  { icon: Shield, label: "验证中心", href: "/verify" },
];

// Toast 组件（不变）
function ToastManager() {
  const { onNewEvent } = useAgent();
  const [toast, setToast] = useState<{ visible: boolean; event: AgentEvent | null }>({
    visible: false,
    event: null,
  });
  const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const unsubscribe = onNewEvent((event) => {
      setToast({ visible: true, event });
      if (timer) clearTimeout(timer);
      const newTimer = setTimeout(() => {
        setToast({ visible: false, event: null });
      }, 3000);
      setTimer(newTimer);
    });

    return () => {
      unsubscribe();
      if (timer) clearTimeout(timer);
    };
  }, [onNewEvent, timer]);

  const handleClose = () => {
    if (timer) clearTimeout(timer);
    setToast({ visible: false, event: null });
  };

  if (!toast.visible || !toast.event) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-4 fade-in duration-300">
      <div className="flex items-center gap-3 rounded-2xl bg-white/95 backdrop-blur-sm border border-[#e8e8ea] shadow-xl px-4 py-3 min-w-[280px] max-w-[400px]">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#f0f0ff] text-[#4f46e5]">
          <Bell className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-[#1a1a2e]">📬 智能体有新动态</div>
          <div className="text-xs text-[#6a6a7e] truncate">
            {toast.event.title}
            {toast.event.description && ` · ${toast.event.description}`}
          </div>
        </div>
        <button
          onClick={handleClose}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full hover:bg-[#f0f0f5] transition-colors text-[#8a8a9e]"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

// ============================================================
// 包含导航栏的主布局（修改部分）
// ============================================================
function MainLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [category, setCategory] = useState<string | null>(null);
  const { isAuthenticated, isAdmin, isLoading, user, logout } = useAuth();
  const [profileOpen, setProfileOpen] = useState(false);
  const [sidebarProfile, setSidebarProfile] = useState<any>(null);
  const [showProfileGuide, setShowProfileGuide] = useState(false);
  const [profileChecked, setProfileChecked] = useState(false);
  const portal = typeof window !== 'undefined' ? sessionStorage.getItem('auth_portal') || 'student' : 'student';

  // Read category query param on client (avoids useSearchParams prerender issue)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setCategory(new URLSearchParams(window.location.search).get('category'));
    }
  }, [pathname]);

  // 全局学习计时：学生端每 60 秒向后端发送心跳，累积学习时长
  useEffect(() => {
    if (portal !== 'student' || !user?.id) return;
    const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
    const token = sessionStorage.getItem('auth_token');
    const heartbeat = () => {
      fetch(`${API}/api/profile/heartbeat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
        body: JSON.stringify({}),
      }).catch(() => {});
    };
    heartbeat(); // 首次立即记录
    const interval = setInterval(heartbeat, 60000); // 之后每分钟一次
    return () => clearInterval(interval);
  }, [portal, user?.id]);

  // 获取画像（侧边栏显示用）
  useEffect(() => {
    if (!user?.id || isAdmin) return;
    const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
    const token = sessionStorage.getItem('auth_token');
    fetch(`${API}/api/profile?user_id=${user.id}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} }).then(r => r.json()).then(d => {
      setSidebarProfile(d);
    }).catch(() => {});
  }, [user?.id]);

  // 画像引导弹窗（仅首次检测，画像为空时弹出一次）
  useEffect(() => {
    if (!user?.id || isAdmin || profileChecked) return;
    // 如果 sessionStorage 已记录过，不再检查
    if (sessionStorage.getItem('profile_guide_shown')) return;
    const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
    const token = sessionStorage.getItem('auth_token');
    fetch(`${API}/api/profile?user_id=${user.id}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} }).then(r => r.json()).then(d => {
      setProfileChecked(true);
      const hasAnyScore = (d.theoretical_basis || 0) > 0
        || (d.coding_ability || 0) > 0
        || (d.practical_ops || 0) > 0
        || (d.troubleshooting || 0) > 0
        || (d.data_thinking || 0) > 0
        || (d.self_learning || 0) > 0;
      // 有画像数据 → 不弹
      if (hasAnyScore || d.dialogue_completed) return;
      // 无画像 → 弹引导
      setShowProfileGuide(true);
      sessionStorage.setItem('profile_guide_shown', '1');
    }).catch(() => {});
  }, [user?.id, isAdmin, profileChecked]);

  // ✅ 1. 将重定向逻辑移到 useEffect 中
  useEffect(() => {
    // 只有在认证状态加载完成且未认证时跳转
    if (!isLoading && !isAuthenticated && pathname !== '/login' && pathname !== '/welcome') {
      const target = sessionStorage.getItem('auth_redirect_target');
      router.replace(target === '/login' ? '/login' : '/welcome');
    }
    if (pathname === '/login') sessionStorage.removeItem('auth_redirect_target');
  }, [isAuthenticated, isLoading, pathname, router]);

  // 等待认证状态加载
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f5f5f7]">
        <div className="text-[#6a6a7e]">加载中...</div>
      </div>
    );
  }

  // 登录页不显示导航栏
  if (pathname === '/login' || pathname === '/welcome') {
    return <>{children}</>;
  }

  // ✅ 2. 未认证时不渲染，由 useEffect 负责跳转
  if (!isAuthenticated) {
    return null;
  }

  // 构建导航菜单
  const navItems = portal === 'admin' ? ADMIN_NAV : portal === 'teacher' ? TEACHER_NAV : STUDENT_NAV;

  return (
    <div className="flex min-h-screen bg-[#f7fcfc]">
      {/* 左侧导航栏 */}
      <aside className="fixed inset-y-0 left-0 z-40 flex w-[232px] flex-col overflow-hidden border-r border-[#b9d8d9] bg-[#effcfc]">
        {/* Logo */}
        <div className="flex h-16 items-center gap-2.5 border-b border-[#b9d8d9] px-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#18d4c7] to-[#078fc3] text-white shadow-sm">
            <BookOpen className="w-4 h-4" />
          </div>
          <span className="text-[17px] font-bold text-[#0a1720]">LearnWeave</span>
        </div>

        {/* 导航 */}
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <ul className="space-y-0.5">
            {navItems.map((item, idx) => {
              const isWrongQuestions = item.href.includes('category=wrong_question');
              const isNotes = item.href === '/notes';
              const isActive = isWrongQuestions
                ? pathname === '/notes' && category === 'wrong_question'
                : isNotes
                  ? pathname === '/notes' && category !== 'wrong_question'
                  : item.href === '/' ? pathname === '/' : item.href === '/teacher' ? pathname === '/teacher' : pathname.startsWith(item.href);
              const IconComponent = item.icon;
              return (
              <li key={`${item.label}-${idx}`}>
                <Link href={item.href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive ? 'bg-gradient-to-r from-[#08a9d2] to-[#12d3c2] text-white shadow-sm' : 'text-[#38515a] hover:bg-[#dff7f5] hover:text-[#087f8c]'
                  }`}>
                  <IconComponent className="w-4 h-4" />
                  {item.label}
                </Link>
              </li>
            )})}
          </ul>
        </nav>

        {/* 底部用户区 */}
        <div className="border-t border-[#b9d8d9] p-3">
          <div className="relative">
            <button onClick={() => setProfileOpen(!profileOpen)}
              className="w-full flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-[#dff7f5] transition-colors cursor-pointer">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#c8f3ef] text-sm font-semibold text-[#087f8c]">
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="min-w-0 flex-1 text-left">
                <div className="text-sm font-medium text-[#14242b] truncate">{user?.username || '未登录'}</div>
                <div className="text-xs text-[#66828a] truncate">{sidebarProfile?.major_background || (portal === 'admin' ? '系统管理员' : portal === 'teacher' ? '教师' : '学生')}</div>
              </div>
            </button>
            {profileOpen && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setProfileOpen(false)} />
                <div className="absolute bottom-full left-0 right-0 mb-2 z-40 bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden">
                  <button onClick={() => { sessionStorage.setItem('auth_redirect_target', '/login'); setProfileOpen(false); logout(); router.replace('/login'); }} className="w-full text-left px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-50 flex items-center gap-2"><RefreshCw className="w-4 h-4" />切换账号</button>
                  <button onClick={() => { setProfileOpen(false); logout(); router.push('/login'); }} className="w-full text-left px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 flex items-center gap-2"><LogOut className="w-4 h-4" />退出登录</button>
                </div>
              </>
            )}
          </div>
        </div>
      </aside>

      {/* 右侧主内容 */}
      <main className="ml-[232px] flex-1 min-h-screen">
        <div className="flex h-16 items-center justify-end gap-4 border-b border-[#b9d8d9] bg-white/90 px-8 backdrop-blur">
          <span className="text-sm text-gray-500">{user?.username || '用户'}</span>
          <button type="button" onClick={() => { logout(); setProfileOpen(false); router.replace('/login'); }} className="text-xs text-gray-400 hover:text-indigo-600 transition-colors">退出</button>
        </div>
        <div className="p-8">{children}</div>
      </main>

      {/* 画像引导弹窗（仅新用户未完成画像时弹出） */}
      {showProfileGuide && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md mx-4 text-center">
            <div className="flex justify-center mb-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-100">
                <Brain className="w-8 h-8 text-indigo-600" />
              </div>
            </div>
            <h2 className="text-xl font-bold text-gray-800 mb-2">欢迎来到 LearnWeave！</h2>
            <p className="text-sm text-gray-500 mb-3">我是你的 AI 学习助手。在开始学习之前，让我先了解一下你的基础，为你生成专属的10维学情画像。</p>
            <p className="text-xs text-gray-400 mb-6">只需 2 分钟聊天对话，AI 就能摸清你的编程基础与数据思维</p>
            <div className="flex gap-3 justify-center">
              <button onClick={() => setShowProfileGuide(false)} className="px-5 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-500 hover:bg-gray-50">稍后再说</button>
              <Link href="/profile" onClick={() => setShowProfileGuide(false)} className="px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700">开始画像评估 →</Link>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

// ============================================================
// 根布局
// ============================================================
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body style={{ fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif' }}>
        <AuthProvider>
          <AgentProvider>
            <MainLayout>{children}</MainLayout>
          </AgentProvider>
        </AuthProvider>
        <TomatoPet />
      </body>
    </html>
  );
}
