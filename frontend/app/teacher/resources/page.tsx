'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { BookOpen, Code, FileText, Brain, Video, Zap } from 'lucide-react';
import { teacherApi, type ResourcesResponse } from '@/lib/teacherApi';

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  FileText, Brain, Code, BookOpen, Zap, Video,
};

const resourceHref = (type: string) => {
  if (type.includes('导图')) return '/learn/python-data-analysis?lecture=1&tab=mindmap';
  if (type.includes('代码') || type.includes('实验')) return '/learn/python-data-analysis?lecture=1&tab=code';
  if (type.includes('练习') || type.includes('题')) return '/learn/python-data-analysis?lecture=1&tab=quiz';
  if (type.includes('视频')) return '/learn/python-data-analysis?lecture=1&tab=video';
  return '/learn/python-data-analysis?lecture=1&tab=doc';
};

export default function TeacherResources() {
  const [data, setData] = useState<ResourcesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    teacherApi
      .getResources()
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
        <h1 className="text-2xl font-bold text-[#1a1a2e]">📖 教学资源</h1>
        <p className="text-sm text-[#6a6a7e] mt-1">AI 多智能体已生成 {data?.total ?? 0} 份资源</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { v: data?.lecture_count ?? 0, l: '讲义', bg: '#eef2ff', color: '#4f46e5' },
          { v: data?.quiz_count ?? 0, l: '练习题', bg: '#fef2f2', color: '#dc2626' },
          { v: data?.lab_count ?? 0, l: '代码示例', bg: '#fffbeb', color: '#d97706' },
        ].map(s => (
          <div key={s.l} className="bg-white rounded-2xl border border-[#e8e8ea] p-5 text-center" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
            <div className="text-3xl font-extrabold text-[#1a1a2e] mb-1">{s.v}</div>
            <div className="text-sm text-[#6a6a7e]">{s.l}</div>
          </div>
        ))}
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {(data?.resources ?? []).map(r => {
          const IconComp = ICON_MAP[r.icon] || FileText;
          return (
            <Link href={resourceHref(r.type)} key={r.type} className="block bg-white rounded-2xl border border-[#e8e8ea] p-5 hover:-translate-y-0.5 hover:border-[#82cacc] hover:shadow-md transition-all" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: r.color + '15', color: r.color }}>
                  <IconComp className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-bold text-[#1a1a2e]">{r.type}</div>
                  <div className="text-2xl font-extrabold" style={{ color: r.color }}>{r.count}</div>
                </div>
              </div>
              <div className="text-xs text-[#8a8a9e]">{r.desc}</div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
