'use client';

import { useState } from 'react';

const COURSE_INFO = {
  '课程名称': 'Python数据分析实战',
  '学期': '2026 秋季',
  '总讲次': '24 讲',
  '班级人数': '128 人',
  '授课语言': 'Python 3.10+',
  '开设院系': '人工智能与大数据学院',
};

const INIT_FEATURES = [
  { key: 'auto_assessment', label: '自动学习评估', desc: '基于学习数据自动生成10维能力评估报告', enabled: true },
  { key: 'path_planning', label: '智能路径规划', desc: '根据薄弱维度自动推荐个性化学习路径', enabled: true },
  { key: 'quiz_generation', label: 'AI 出题', desc: '根据知识点自动生成针对性练习题', enabled: true },
  { key: 'mindmap_auto', label: '思维导图生成', desc: '自动提炼知识点结构生成思维导图', enabled: false },
  { key: 'profile_building', label: '学情画像引导', desc: '对话式引导完成初始学情画像评估', enabled: true },
];

export default function TeacherSettings() {
  const [features, setFeatures] = useState(INIT_FEATURES);

  const handleToggle = (key: string) => {
    setFeatures(prev => prev.map(f => f.key === key ? { ...f, enabled: !f.enabled } : f));
  };

  return (
    <div className="max-w-3xl mx-auto p-6 lg:p-8 space-y-6 pb-16">
      <h1 className="text-2xl font-bold text-[#1a1a2e]">⚙️ 系统设置</h1>

      {/* 课程信息 */}
      <div className="bg-white rounded-2xl border border-[#e8e8ea] p-6 space-y-6" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
        <h2 className="text-lg font-bold text-[#1a1a2e]">课程信息</h2>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(COURSE_INFO).map(([label, value]) => (
            <div key={label}>
              <div className="text-xs text-[#8a8a9e] mb-1">{label}</div>
              <div className="text-sm font-semibold text-[#1a1a2e]">{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 功能开关 */}
      <div className="bg-white rounded-2xl border border-[#e8e8ea] p-6 space-y-6" style={{ boxShadow: '0 1px 3px rgba(30,27,75,0.06)' }}>
        <h2 className="text-lg font-bold text-[#1a1a2e]">功能开关</h2>
        <div className="space-y-3">
          {features.map((f) => (
            <div key={f.key} className="flex items-center justify-between py-2 border-b border-[#f0f0f5] last:border-0">
              <div>
                <div className="text-sm font-semibold text-[#1a1a2e]">{f.label}</div>
                <div className="text-xs text-[#8a8a9e]">{f.desc}</div>
              </div>
              <button
                onClick={() => handleToggle(f.key)}
                className={`relative w-11 h-6 rounded-full transition-colors duration-200 cursor-pointer ${
                  f.enabled ? 'bg-[#2563eb]' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200 ${
                    f.enabled ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
