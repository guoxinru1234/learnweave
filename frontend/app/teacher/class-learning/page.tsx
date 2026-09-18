'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, BarChart3, CheckCircle2, RefreshCw, Users } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ClassLearningPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [targetStudent, setTargetStudent] = useState('');
  const [command, setCommand] = useState('');
  const [commandDate, setCommandDate] = useState(new Date().toISOString().slice(0, 10));
  const [sending, setSending] = useState(false);
  const sendCommand = async () => {
    if (!targetStudent || !command.trim()) return;
    setSending(true);
    try {
      const token = sessionStorage.getItem('auth_token');
      const response = await fetch(`${API}/api/daily-tasks/teacher`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify({ target_user_id: Number(targetStudent), content: command.trim(), date: commandDate }) });
      if (!response.ok) throw new Error('send failed');
      setCommand('');
      alert('教师命令已发送');
    } catch { alert('发送失败，请检查后端服务'); }
    finally { setSending(false); }
  };

  const load = async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem('auth_token');
      const response = await fetch(`${API}/api/teacher/dashboard`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
      if (!response.ok) throw new Error('无法获取教师端班级数据');
      setData(await response.json());
    } catch (err: any) { setError(err.message || '数据加载失败'); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  if (loading) return <div className="p-10 text-center text-[#6a6a7e]">正在加载班级学情...</div>;
  if (error) return <div className="rounded-2xl bg-white p-10 text-center text-red-500">{error}<button onClick={load} className="ml-3 text-[#078fc3]">重试</button></div>;
  const students = data?.students || [];
  const risks = data?.at_risk_students || [];
  const stats = [
    ['班级学生', data?.student_count ?? students.length, Users],
    ['已完成评估', data?.assessed_count ?? data?.assessment_completed ?? 0, CheckCircle2],
    ['需调整资源', data?.resource_adjustments ?? 0, RefreshCw],
    ['需教师干预', risks.length, AlertTriangle],
  ];
  const commandPanel = <section className="rounded-2xl border border-[#bfe3e3] bg-white p-5"><h2 className="mb-3 font-bold text-[#18343a]">教师命令下发</h2><div className="grid gap-3 md:grid-cols-[1fr_1fr_2fr_auto]"><select value={targetStudent} onChange={e=>setTargetStudent(e.target.value)} className="rounded-lg border p-2 text-sm"><option value="">选择学生</option>{students.map((s:any)=><option key={s.id} value={s.id}>{s.name||s.username}</option>)}</select><input type="date" value={commandDate} onChange={e=>setCommandDate(e.target.value)} className="rounded-lg border p-2 text-sm"/><input value={command} onChange={e=>setCommand(e.target.value)} placeholder="例如：完成第12讲 Pandas 合并练习" className="rounded-lg border p-2 text-sm"/><button disabled={sending||!targetStudent||!command.trim()} onClick={sendCommand} className="rounded-lg bg-[#078fc3] px-4 py-2 text-sm font-semibold text-white disabled:opacity-40">{sending?'发送中':'发送命令'}</button></div></section>;
  return <div className="mx-auto max-w-7xl space-y-6 p-6 lg:p-8"><header><div className="text-xs text-[#8a8a9e]">班级学情</div><h1 className="text-2xl font-bold text-[#18343a]">Python 数据分析班级学情</h1><p className="mt-1 text-sm text-[#6a6a7e]">数据来自真实学生学习记录和学情画像</p></header><div className="grid grid-cols-2 gap-4 lg:grid-cols-4">{stats.map(([label,value,Icon]:any)=><div key={label} className="rounded-2xl border border-[#d6eaea] bg-white p-5"><Icon className="mb-3 h-5 w-5 text-[#078fc3]"/><div className="text-3xl font-bold text-[#18343a]">{value}</div><div className="text-sm text-[#6a6a7e]">{label}</div></div>)}</div><section className="overflow-hidden rounded-2xl border border-[#d6eaea] bg-white"><div className="flex items-center justify-between border-b p-5"><h2 className="font-bold text-[#18343a]">学生学习干预管理</h2><button onClick={load} className="flex items-center gap-1 text-sm text-[#078fc3]"><RefreshCw className="h-4 w-4"/>刷新</button></div>{students.length===0?<div className="p-12 text-center text-[#8aa0a3]">暂无学生数据</div>:<div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="bg-[#f7fcfc] text-left text-[#6a6a7e]"><th className="p-4">学生</th><th className="p-4">学习状态</th><th className="p-4">画像得分</th><th className="p-4">干预建议</th><th className="p-4">操作</th></tr></thead><tbody>{students.map((student:any)=><tr key={student.id||student.username} className="border-t"><td className="p-4 font-semibold text-[#38515a]">{student.name||student.username}</td><td className="p-4">{risks.some((r:any)=>r.id===student.id)?<span className="text-red-500">需要干预</span>:<span className="text-green-600">正常</span>}</td><td className="p-4">{student.overall ?? student.overall_score ?? '--'}</td><td className="p-4 text-[#6a6a7e]">{risks.some((r:any)=>r.id===student.id)?'查看薄弱维度并安排辅导':'持续跟踪学习进度'}</td><td className="p-4"><Link href={`/teacher/students?student=${student.id}`} className="text-[#078fc3] hover:underline">查看并干预</Link></td></tr>)}</tbody></table></div>}</section><section className="grid gap-4 md:grid-cols-2"><div className="rounded-2xl border border-[#d6eaea] bg-white p-5"><h2 className="mb-3 font-bold text-[#18343a]">需重点关注</h2>{risks.length?risks.map((s:any)=><div key={s.id||s.username} className="mb-2 flex items-center justify-between rounded-lg bg-[#fff7f7] p-3"><span>{s.name||s.username}</span><Link href={`/teacher/students?student=${s.id}`} className="text-sm text-[#078fc3]">安排干预</Link></div>):<div className="text-sm text-[#6a6a7e]">暂无高风险学生</div>}</div><div className="rounded-2xl border border-[#d6eaea] bg-white p-5"><h2 className="mb-3 font-bold text-[#18343a]">班级画像概览</h2><p className="text-sm text-[#6a6a7e]">平均掌握度：{data?.class_overall ?? data?.average_score ?? '--'}</p><Link href="/teacher/reports" className="mt-3 inline-flex items-center gap-1 text-sm text-[#078fc3]">查看详细报告 <BarChart3 className="h-4 w-4"/></Link></div></section></div>;
}
