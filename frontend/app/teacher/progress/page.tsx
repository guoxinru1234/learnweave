'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { CheckCircle, Circle, Lock } from 'lucide-react';
import { teacherApi, type ProgressResponse } from '@/lib/teacherApi';
import { useRouter } from 'next/navigation';

export default function TeacherProgress() {
  const router = useRouter();
  useEffect(() => { router.replace('/teacher'); }, [router]);
  const [expand, setExpand] = useState<number | null>(null);
  const [data, setData] = useState<ProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    teacherApi
      .getProgress()
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

  const totalStudents = data?.total_students ?? 0;
  const totalLectures = data?.total_lectures ?? 24;

  return (
    <div className="max-w-5xl mx-auto p-6 lg:p-8 space-y-8 pb-16">
      <div>
        <h1 className="text-2xl font-bold text-[#1a1a2e]">📝 课程进度</h1>
        <p className="text-sm text-[#6a6a7e] mt-1">共 {totalStudents} 名学生 · {totalLectures} 讲</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { v: `${data?.started_lectures_count ?? 0}/${totalLectures}`, l: '已开讲次', c: '学生已开始学习', bg: '#eef2ff', color: '#4f46e5' },
          { v: `${data?.avg_completion_rate ?? 0}%`, l: '平均完成率', c: '已完成讲次/总讲次', bg: '#f0fdf4', color: '#16a34a' },
          { v: `${data?.lagging_count ?? 0} 人`, l: '进度落后', c: '完成率 < 30%', bg: '#fef2f2', color: '#dc2626' },
        ].map(s => (
          <div key={s.l} className="bg-white rounded-2xl border border-[#e8e8ea] p-5 text-center" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
            <div className="text-3xl font-extrabold text-[#1a1a2e] mb-1">{s.v}</div>
            <div className="text-sm text-[#6a6a7e]">{s.l}</div>
            <div className="text-xs text-[#8a8a9e] mt-1">{s.c}</div>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        {(data?.modules ?? []).map((mod, mi) => (
          <div key={mi} className="bg-white rounded-2xl border border-[#e8e8ea] overflow-hidden" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
            <button onClick={() => setExpand(expand === mi ? null : mi)}
              className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors">
              <span className="text-base font-bold text-[#1a1a2e]">{mod.name}</span>
              <span className="text-sm text-[#8a8a9e]">{expand === mi ? '收起 ▲' : '展开 ▼'}</span>
            </button>
            {expand === mi && (
              <div className="px-6 pb-4 space-y-2">
                {mod.lectures.map(lec => {
                  const pct = totalStudents > 0 ? Math.round((lec.done / totalStudents) * 100) : 0;
                  return (
                    <Link href={`/learn/python-data-analysis?lecture=${lec.num}&tab=doc`} key={lec.num} className="flex items-center gap-4 rounded-md py-2 border-b border-[#f0f0f5] last:border-0 hover:bg-[#f1fbfa]">
                      <div className="w-10 text-center">
                        {lec.done === totalStudents && totalStudents > 0 ? <CheckCircle className="w-5 h-5 text-[#16a34a] mx-auto" /> :
                         lec.done > 0 ? <Circle className="w-5 h-5 text-[#d97706] mx-auto" /> :
                         <Lock className="w-5 h-5 text-[#8a8a9e] mx-auto" />}
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-semibold text-[#1a1a2e]">第{lec.num}讲：{lec.title}</div>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="flex-1 h-1.5 rounded-full bg-gray-100 overflow-hidden">
                            <div className="h-full rounded-full bg-[#4f46e5]" style={{ width: pct + '%' }} /></div>
                          <span className="text-xs text-[#8a8a9e]">{lec.done}/{totalStudents}人</span>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
