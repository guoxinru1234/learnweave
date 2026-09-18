'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Search } from 'lucide-react';
import { teacherApi, type StudentsResponse } from '@/lib/teacherApi';

export default function StudentManagement() {
  const [search, setSearch] = useState('');
  const [data, setData] = useState<StudentsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [commandTarget, setCommandTarget] = useState<any>(null);
  const [command, setCommand] = useState('');
  const [sending, setSending] = useState(false);

  const sendCommand = async () => {
    if (!commandTarget || !command.trim()) return;
    setSending(true);
    try {
      const token = sessionStorage.getItem('auth_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/daily-tasks/teacher`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify({ target_user_id: commandTarget.id, content: command.trim(), date: new Date().toISOString().slice(0, 10) }) });
      if (!response.ok) throw new Error('send failed');
      setCommand(''); setCommandTarget(null); alert('教师命令已发送');
    } catch { alert('发送失败，请检查后端服务'); }
    finally { setSending(false); }
  };

  useEffect(() => {
    teacherApi
      .getStudents()
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
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

  const allStudents = data?.students ?? [];

  const filtered = allStudents.filter(s =>
    s.name.includes(search) || s.username.includes(search) || s.major.includes(search)
  );

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-6 pb-16">
      <div>
        <h1 className="text-2xl font-bold text-[#1a1a2e]">👥 学生管理</h1>
        <p className="text-sm text-[#6a6a7e] mt-1">共 {data?.total ?? 0} 名学生</p>
      </div>

      {/* 搜索 */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8a8a9e]" />
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="搜索学生姓名或学号..."
          className="w-full h-10 pl-10 pr-4 rounded-xl border border-[#e8e8ea] text-sm outline-none focus:border-[#4f46e5] focus:ring-2 focus:ring-indigo-100" />
      </div>

      {/* 学生列表 */}
      <div className="bg-white rounded-2xl border border-[#e8e8ea] overflow-hidden" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
        <div className="overflow-x-auto">
          <table className="w-full text-base">
            <thead>
              <tr className="border-b border-[#e8e8ea] bg-[#fafaff]">
                <th className="text-left px-5 py-3 font-semibold text-[#8a8a9e]">学生</th>
                <th className="text-left px-5 py-3 font-semibold text-[#8a8a9e]">年级/专业</th>
                <th className="text-left px-5 py-3 font-semibold text-[#8a8a9e]">称号</th>
                <th className="text-left px-5 py-3 font-semibold text-[#8a8a9e]">综合分</th>
                <th className="text-left px-5 py-3 font-semibold text-[#8a8a9e]">学习路径</th>
                <th className="text-left px-5 py-3 font-semibold text-[#8a8a9e]">进度</th>
                <th className="text-left px-5 py-3 font-semibold text-[#8a8a9e]">学习时长</th>
                <th className="text-left px-5 py-3 font-semibold text-[#8a8a9e]">做题正确率</th>
                <th className="text-left px-5 py-3 font-semibold text-[#8a8a9e]">操作</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(st => (
                <tr key={st.id} className="border-b border-[#f0f0f5] hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-[#eef2ff] flex items-center justify-center text-base font-bold text-[#4f46e5]">
                        {st.name[0]}
                      </div>
                      <div>
                        <div className="text-base font-bold text-[#1a1a2e]">{st.name}</div>
                        <div className="text-sm text-[#8a8a9e]">@{st.username}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-[#6a6a7e]">{st.grade || '-'} · {st.major || '-'}</td>
                  <td className="px-5 py-3">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#eef2ff] text-[#4f46e5]">{st.title}</span>
                  </td>
                  <td className="px-5 py-3">
                    <span className={`font-extrabold ${st.overall >= 70 ? 'text-[#16a34a]' : st.overall >= 50 ? 'text-[#d97706]' : 'text-[#dc2626]'}`}>{st.overall}</span>
                  </td>
                  <td className="px-5 py-3 text-[#6a6a7e]">{st.path}</td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full rounded-full bg-[#4f46e5]" style={{ width: st.progress + '%' }} />
                      </div>
                      <span className="text-xs text-[#8a8a9e]">{st.progress}%</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-[#6a6a7e]">{st.learning_hours}h</td>
                  <td className="px-5 py-3">
                    <span className={`text-sm font-bold ${st.quiz_accuracy >= 80 ? 'text-[#16a34a]' : st.quiz_accuracy >= 60 ? 'text-[#d97706]' : 'text-[#dc2626]'}`}>{st.quiz_accuracy}%</span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex gap-2">
                      <Link href={`/teacher/reports?student=${st.id}#student-comparison`} className="text-xs text-[#078f9b] hover:underline">画像</Link>
                      <Link href={`/teacher/grades?student=${st.id}`} className="text-xs text-[#078f9b] hover:underline">评估</Link><button onClick={() => setCommandTarget(st)} className="text-xs text-[#078f9b] hover:underline">发命令</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-[#8a8a9e]">没有匹配的学生</div>
        )}
      </div>
      {commandTarget && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"><div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"><h2 className="mb-3 text-lg font-bold">向 {commandTarget.name} 下发命令</h2><textarea value={command} onChange={e=>setCommand(e.target.value)} rows={4} placeholder="例如：完成第12讲练习" className="w-full rounded-xl border p-3 text-sm"/><div className="mt-4 flex justify-end gap-2"><button onClick={()=>setCommandTarget(null)} className="rounded-lg border px-4 py-2 text-sm">取消</button><button disabled={sending||!command.trim()} onClick={sendCommand} className="rounded-lg bg-[#078f9b] px-4 py-2 text-sm text-white disabled:opacity-40">{sending?'发送中':'发送命令'}</button></div></div></div>}
    </div>
  );
}
