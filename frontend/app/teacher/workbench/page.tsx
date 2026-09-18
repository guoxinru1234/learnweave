'use client';

import { useState } from 'react';
import { BookOpen, Users, FileCheck, AlertCircle, Plus, Archive, ArrowRight, X } from 'lucide-react';
import { useRouter } from 'next/navigation';

// ===== 模拟数据 =====
const STATS = [
  { icon: BookOpen, value: '8', label: '当前课程数量', sub: '本学期进行中', bg: '#eff6ff', color: '#2563eb' },
  { icon: Users, value: '346', label: '选课学生', sub: '覆盖 3 个专业', bg: '#f0fdf4', color: '#16a34a' },
  { icon: FileCheck, value: '12', label: '待复核资料', sub: '需本周处理', bg: '#fef3c7', color: '#d97706' },
  { icon: AlertCircle, value: '3', label: '同步异常', sub: '数据同步警告', bg: '#fef2f2', color: '#dc2626' },
];

const INIT_COURSES = [
  { id: 1, name: 'Python数据分析实战', semester: '2026 春季', materials: 42, students: 128, status: 'active' as const },
  { id: 2, name: '分布式系统原理', semester: '2026 春季', materials: 36, students: 95, status: 'active' as const },
  { id: 3, name: '云计算与虚拟化技术', semester: '2026 春季', materials: 28, students: 73, status: 'active' as const },
  { id: 4, name: '数据挖掘导论', semester: '2025 秋季', materials: 55, students: 50, status: 'archived' as const },
];

const SEMESTERS = ['2026 秋季', '2026 春季', '2025 秋季', '2025 春季'];

export default function TeacherWorkbenchPage() {
  const router = useRouter();
  const [courses, setCourses] = useState(INIT_COURSES);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: '', semester: '2026 秋季', materials: '', students: '' });

  const handleCreate = () => {
    if (!form.name.trim()) return;
    const newCourse = {
      id: Date.now(),
      name: form.name.trim(),
      semester: form.semester,
      materials: parseInt(form.materials) || 0,
      students: parseInt(form.students) || 0,
      status: 'active' as const,
    };
    setCourses([newCourse, ...courses]);
    setForm({ name: '', semester: '2026 秋季', materials: '', students: '' });
    setShowModal(false);
  };

  const handleArchive = (id: number) => {
    setCourses(courses.map(c => c.id === id ? { ...c, status: c.status === 'active' ? 'archived' as const : 'active' as const } : c));
  };

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8 pb-16">
      {/* 页头 */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-[#8a8a9e] mb-1">教师工作台</div>
          <h1 className="text-2xl font-bold text-[#1a1a2e]">教师工作台</h1>
          <p className="text-sm text-[#6a6a7e] mt-1">总览课程与学生数据，快速进入备课与管理流程</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#2563eb] text-white text-sm font-medium hover:bg-[#1d4ed8] transition-colors shadow-sm shadow-blue-200"
        >
          <Plus className="w-4 h-4" />
          创建课程
        </button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map((s, i) => (
          <div key={i} className="bg-white rounded-2xl border border-[#e8e8ea] p-5 shadow-[0_1px_3px_rgba(30,27,75,0.04)]">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: s.bg, color: s.color }}>
                <s.icon className="w-5 h-5" />
              </div>
              <div>
                <div className="text-2xl font-bold text-[#1a1a2e]">{s.value}</div>
                <div className="text-sm text-[#6a6a7e]">{s.label}</div>
              </div>
            </div>
            <div className="text-xs text-[#8a8a9e]">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* 课程卡片列表 */}
      <div>
        <h2 className="text-lg font-bold text-[#1a1a2e] mb-4">我的课程</h2>
        <div className="grid lg:grid-cols-2 gap-4">
          {courses.map(c => (
            <div key={c.id} className="bg-white rounded-2xl border border-[#e8e8ea] p-6 shadow-[0_1px_3px_rgba(30,27,75,0.04)] hover:shadow-[0_4px_12px_rgba(30,27,75,0.08)] transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-bold text-[#1a1a2e] text-lg">{c.name}</h3>
                  <span className={`inline-block mt-1.5 text-xs px-2.5 py-0.5 rounded-full font-medium ${
                    c.status === 'active' ? 'bg-[#eff6ff] text-[#2563eb]' : 'bg-gray-100 text-[#8a8a9e]'
                  }`}>
                    {c.semester} {c.status === 'archived' ? '· 已归档' : ''}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-6 text-sm text-[#6a6a7e] mb-5">
                <span className="flex items-center gap-1.5">
                  <FileCheck className="w-4 h-4" /> {c.materials} 份资料
                </span>
                <span className="flex items-center gap-1.5">
                  <Users className="w-4 h-4" /> {c.students} 名学生
                </span>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => router.push('/teacher/course-resource')}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-[#2563eb] text-[#2563eb] text-sm font-medium hover:bg-[#eff6ff] transition-colors"
                >
                  查看课程 <ArrowRight className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => handleArchive(c.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-[#8a8a9e] text-sm hover:text-[#1a1a2e] hover:bg-gray-50 transition-colors"
                >
                  <Archive className="w-3.5 h-3.5" /> {c.status === 'archived' ? '恢复' : '归档'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 创建课程弹窗 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowModal(false)}>
          <div
            className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md mx-4"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-[#1a1a2e]">创建新课程</h2>
              <button onClick={() => setShowModal(false)} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
                <X className="w-4 h-4 text-[#8a8a9e]" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-[#6a6a7e] mb-1.5 block">课程名称 *</label>
                <input
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  placeholder="输入课程名称"
                  className="w-full px-3 py-2.5 rounded-lg border border-[#e0e0e8] text-sm outline-none focus:border-[#2563eb] focus:ring-1 focus:ring-[#2563eb]"
                  onKeyDown={e => e.key === 'Enter' && handleCreate()}
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-[#6a6a7e] mb-1.5 block">开课学期</label>
                <select
                  value={form.semester}
                  onChange={e => setForm({ ...form, semester: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-lg border border-[#e0e0e8] text-sm outline-none focus:border-[#2563eb] bg-white"
                >
                  {SEMESTERS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-[#6a6a7e] mb-1.5 block">资料数量</label>
                  <input
                    type="number"
                    value={form.materials}
                    onChange={e => setForm({ ...form, materials: e.target.value })}
                    placeholder="0"
                    className="w-full px-3 py-2.5 rounded-lg border border-[#e0e0e8] text-sm outline-none focus:border-[#2563eb]"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#6a6a7e] mb-1.5 block">选课学生</label>
                  <input
                    type="number"
                    value={form.students}
                    onChange={e => setForm({ ...form, students: e.target.value })}
                    placeholder="0"
                    className="w-full px-3 py-2.5 rounded-lg border border-[#e0e0e8] text-sm outline-none focus:border-[#2563eb]"
                  />
                </div>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 py-2.5 rounded-lg border border-[#e0e0e8] text-sm text-[#6a6a7e] hover:bg-gray-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreate}
                disabled={!form.name.trim()}
                className="flex-1 py-2.5 rounded-lg bg-[#2563eb] text-white text-sm font-medium hover:bg-[#1d4ed8] disabled:opacity-40 transition-colors"
              >
                创建课程
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
