'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { teacherApi, type GradesResponse } from '@/lib/teacherApi';

const gradeColor = (g: string) => {
  if (g.startsWith('A')) return 'text-[#16a34a]';
  if (g.startsWith('B')) return 'text-[#2563eb]';
  if (g.startsWith('C')) return 'text-[#d97706]';
  return 'text-[#dc2626]';
};

export default function TeacherGrades() {
  const [data, setData] = useState<GradesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    teacherApi
      .getGrades()
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto p-6 lg:p-8 flex items-center justify-center min-h-[400px]">
        <div className="text-[#8a8a9e] text-lg">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-5xl mx-auto p-6 lg:p-8 flex items-center justify-center min-h-[400px]">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <div className="text-red-600 font-bold text-lg mb-1">加载失败</div>
          <div className="text-red-500 text-sm">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6 lg:p-8 space-y-8 pb-16">
      <div>
        <h1 className="text-2xl font-bold text-[#1a1a2e]">📋 成绩管理</h1>
        <p className="text-sm text-[#6a6a7e] mt-1">2025 春季学期</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { v: `${data?.avg_score ?? 0}`, l: '平均分', bg: '#eef2ff', color: '#4f46e5' },
          { v: data?.top_grade ?? '-', l: '最高等第', bg: '#f0fdf4', color: '#16a34a' },
          { v: data?.lowest_grade ?? '-', l: '最低等第', bg: '#fef2f2', color: '#dc2626' },
          { v: `${data?.pass_rate ?? 0}%`, l: '及格率', bg: '#fffbeb', color: '#d97706' },
        ].map(s => (
          <div key={s.l} className="bg-white rounded-2xl border border-[#e8e8ea] p-5 text-center" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
            <div className="text-3xl font-extrabold text-[#1a1a2e] mb-1">{s.v}</div>
            <div className="text-sm text-[#6a6a7e]">{s.l}</div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-[#e8e8ea] overflow-hidden" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#e8e8ea] bg-[#fafaff]">
                <th className="text-left px-5 py-3 text-xs font-semibold text-[#8a8a9e]">排名</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-[#8a8a9e]">学生</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-[#8a8a9e]">测验均分</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-[#8a8a9e]">实验成绩</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-[#8a8a9e]">综合成绩</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-[#8a8a9e]">等第</th>
              </tr>
            </thead>
            <tbody>
              {(data?.students ?? []).map(st => (
                <tr key={st.id} className="border-b border-[#f0f0f5] hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3">
                    <span className="text-xs font-bold text-[#8a8a9e]">#{st.rank}</span>
                  </td>
                  <td className="px-5 py-3 font-semibold text-[#1a1a2e]"><Link href={`/teacher/reports?student=${st.id}#student-comparison`} className="hover:text-[#078f9b] hover:underline">{st.name}</Link></td>
                  <td className="px-5 py-3 text-[#6a6a7e]">{st.quiz_avg}</td>
                  <td className="px-5 py-3 text-[#6a6a7e]">{st.lab_score}</td>
                  <td className="px-5 py-3 font-extrabold text-[#1a1a2e]">{st.final_score}</td>
                  <td className="px-5 py-3">
                    <span className={`text-sm font-extrabold ${gradeColor(st.grade)}`}>{st.grade}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {(data?.students ?? []).length === 0 && (
          <div className="text-center py-12 text-[#8a8a9e]">暂无成绩数据</div>
        )}
      </div>
    </div>
  );
}
