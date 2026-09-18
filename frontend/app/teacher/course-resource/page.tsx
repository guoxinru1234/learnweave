'use client';

import { useState, useRef } from 'react';
import {
  FileText, FlaskConical, Database, FileCode, Filter,
  Calendar, Clock, MapPin, User, GraduationCap, Settings2,
  Upload, BookOpen, ExternalLink, X, CheckCircle2,
} from 'lucide-react';
import { useRouter } from 'next/navigation';

// ===== 模拟数据 =====
const MATERIAL_TYPES = [
  { icon: FileText, name: '讲义课件', color: '#2563eb', bg: '#eff6ff' },
  { icon: FlaskConical, name: '实验指导', color: '#16a34a', bg: '#f0fdf4' },
  { icon: Database, name: '数据集', color: '#d97706', bg: '#fef3c7' },
  { icon: FileCode, name: '参考答案', color: '#7c3aed', bg: '#f5f3ff' },
] as const;

const CLASS_INFO: { icon: React.ComponentType<{ className?: string }>; label: string; value: string }[] = [
  { icon: BookOpen, label: '课程代码', value: 'CS401' },
  { icon: Calendar, label: '开课学期', value: '2026 年春季学期' },
  { icon: Clock, label: '上课时间', value: '周一 8:00-10:35 / 周三 10:00-11:35' },
  { icon: MapPin, label: '上课地点', value: '教学楼 A301 / 实验中心 B102' },
  { icon: User, label: '授课教师', value: '张明华 教授' },
  { icon: GraduationCap, label: '课程学分', value: '4.0' },
];

interface LessonItem { num: number; title: string; type: 'theory' | 'lab'; date: string; }
const LESSONS: LessonItem[] = [
  { num: 1, title: '分布式计算概述与集群架构', type: 'theory', date: '2026-02-24' },
  { num: 2, title: 'Hadoop 生态系统与 HDFS 原理', type: 'theory', date: '2026-03-03' },
  { num: 3, title: 'Hadoop 集群搭建与配置实践', type: 'lab', date: '2026-03-05' },
  { num: 4, title: 'MapReduce 编程模型详解', type: 'theory', date: '2026-03-10' },
  { num: 5, title: 'MapReduce 词频统计实战', type: 'lab', date: '2026-03-12' },
  { num: 6, title: 'YARN 资源管理与作业调度', type: 'theory', date: '2026-03-17' },
  { num: 7, title: 'YARN 调度器配置实验', type: 'lab', date: '2026-03-19' },
  { num: 8, title: 'HDFS 数据块与副本策略', type: 'theory', date: '2026-03-24' },
  { num: 9, title: 'HDFS 读写操作实践', type: 'lab', date: '2026-03-26' },
  { num: 10, title: 'Pandas核心架构与 DataFrame 原理', type: 'theory', date: '2026-03-31' },
  { num: 11, title: 'Python 环境部署与基础操作', type: 'lab', date: '2026-04-02' },
  { num: 12, title: 'DataFrame 转换与行动操作详解', type: 'theory', date: '2026-04-07' },
  { num: 13, title: 'DataFrame 算子综合实验', type: 'lab', date: '2026-04-09' },
  { num: 14, title: '数据清洗流程与性能优化', type: 'theory', date: '2026-04-14' },
  { num: 15, title: 'Shuffle 调优对比实验', type: 'lab', date: '2026-04-16' },
  { num: 16, title: 'Pandas SQL 与 DataFrame API', type: 'theory', date: '2026-04-21' },
  { num: 17, title: 'Pandas SQL 数据分析实战', type: 'lab', date: '2026-04-23' },
  { num: 18, title: 'Python Streaming 流处理', type: 'theory', date: '2026-04-28' },
  { num: 19, title: '实时流处理编程实验', type: 'lab', date: '2026-04-30' },
  { num: 20, title: '广播变量与累加器', type: 'theory', date: '2026-05-05' },
  { num: 21, title: '共享变量应用实验', type: 'lab', date: '2026-05-07' },
  { num: 22, title: '集群监控与故障排查', type: 'theory', date: '2026-05-12' },
  { num: 23, title: '集群性能监控实验', type: 'lab', date: '2026-05-14' },
  { num: 24, title: '综合项目展示与课程总结', type: 'lab', date: '2026-05-19' },
];

const RULES = [
  { label: '作业提交期限', value: '每周日 23:59' },
  { label: '迟交扣分规则', value: '每天扣减 10%，超过 3 天零分' },
  { label: '考勤成绩权重', value: '10%' },
  { label: '实验成绩权重', value: '30%' },
  { label: '期末考试成绩权重', value: '40%' },
  { label: '平时测验权重', value: '20%' },
  { label: '学术诚信政策', value: '查重率超过 30% 按零分处理' },
];

export default function CourseResourcePage() {
  const [filter, setFilter] = useState<'all' | 'theory' | 'lab'>('all');
  const [materials, setMaterials] = useState([
    { name: '讲义课件', count: 24, color: '#2563eb', bg: '#eff6ff', icon: FileText, href: '/knowledge' },
    { name: '实验指导', count: 12, color: '#16a34a', bg: '#f0fdf4', icon: FlaskConical, href: '/knowledge' },
    { name: '数据集', count: 8, color: '#d97706', bg: '#fef3c7', icon: Database, href: '/knowledge' },
    { name: '参考答案', count: 12, color: '#7c3aed', bg: '#f5f3ff', icon: FileCode, href: '/knowledge' },
  ]);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadForm, setUploadForm] = useState({ type: '讲义课件', fileName: '' });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadDone, setUploadDone] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadForm(prev => ({ ...prev, fileName: file.name }));
    }
  };

  const handleUpload = () => {
    if (!selectedFile) return;
    setMaterials(prev => prev.map(m =>
      m.name === uploadForm.type ? { ...m, count: m.count + 1 } : m
    ));
    setUploadDone(true);
    setTimeout(() => {
      setUploadDone(false);
      setShowUpload(false);
      setUploadForm({ type: '讲义课件', fileName: '' });
      setSelectedFile(null);
    }, 1200);
  };

  const filteredLessons = filter === 'all'
    ? LESSONS
    : LESSONS.filter(l => l.type === filter);

  return (
    <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-6 pb-16">
      {/* 页头 */}
      <div>
        <div className="text-xs text-[#8a8a9e] mb-1">课程与资源</div>
        <h1 className="text-2xl font-bold text-[#1a1a2e]">Python数据分析实战</h1>
        <p className="text-sm text-[#6a6a7e] mt-1">课程资料管理 · 教学规划 · 规则配置</p>
      </div>

      {/* 区域 1：课程资料 + 教学班信息 */}
      <div className="grid lg:grid-cols-[1fr_360px] gap-6">
        {/* 课程资料与知识库 */}
        <div className="bg-white rounded-2xl border border-[#e8e8ea] p-6 shadow-[0_1px_3px_rgba(30,27,75,0.04)]">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-bold text-[#1a1a2e] flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#2563eb]" /> 课程资料与知识库
            </h2>
            <button
              onClick={() => setShowUpload(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#2563eb] text-white text-xs font-medium hover:bg-[#1d4ed8] transition-colors"
            >
              <Upload className="w-3.5 h-3.5" /> 上传资料
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3 mb-5">
            {materials.map((m, i) => (
              <button
                key={i}
                onClick={() => router.push(m.href)}
                className="flex items-center gap-3 p-4 rounded-xl border border-[#f0f0f2] hover:border-[#2563eb] hover:bg-[#eff6ff] transition-colors text-left cursor-pointer"
              >
                <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: m.bg, color: m.color }}>
                  <m.icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-bold text-[#1a1a2e]">{m.name}</div>
                  <div className="text-xs text-[#8a8a9e]">{m.count} 个文件</div>
                </div>
                <ExternalLink className="w-3.5 h-3.5 text-[#c8c8d2]" />
              </button>
            ))}
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push('/knowledge')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-[#e0e0e8] text-sm text-[#6a6a7e] hover:bg-[#fafbfc] transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" /> 教学大纲
            </button>
            <button
              onClick={() => router.push('/knowledge')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-[#e0e0e8] text-sm text-[#6a6a7e] hover:bg-[#fafbfc] transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" /> 知识库管理
            </button>
          </div>
        </div>

        {/* 教学班信息 */}
        <div className="bg-white rounded-2xl border border-[#e8e8ea] p-6 shadow-[0_1px_3px_rgba(30,27,75,0.04)]">
          <h2 className="font-bold text-[#1a1a2e] mb-4 flex items-center gap-2">
            <GraduationCap className="w-4 h-4 text-[#2563eb]" /> 教学班信息
          </h2>
          <div className="space-y-3">
            {CLASS_INFO.map((info, i) => (
              <div key={i} className="flex items-start gap-3">
                <info.icon className="w-4 h-4 text-[#8a8a9e] flex-shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <div className="text-xs text-[#8a8a9e]">{info.label}</div>
                  <div className="text-sm text-[#1a1a2e] font-medium">{info.value}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-5 pt-4 border-t border-[#f0f0f2]">
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#6a6a7e]">选课人数：<strong className="text-[#1a1a2e]">128 人</strong></span>
              <button
                onClick={() => router.push('/teacher/class-learning')}
                className="flex items-center gap-1 text-xs text-[#2563eb] hover:underline font-medium"
              >
                班级学情详情 <ExternalLink className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 区域 2 + 区域 3 双栏 */}
      <div className="grid lg:grid-cols-[1fr_320px] gap-6">
        {/* 左栏：课程规划与备课 */}
        <div className="bg-white rounded-2xl border border-[#e8e8ea] p-6 shadow-[0_1px_3px_rgba(30,27,75,0.04)]">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-bold text-[#1a1a2e] flex items-center gap-2">
              <Calendar className="w-4 h-4 text-[#2563eb]" /> 课程规划与备课
            </h2>
          </div>

          {/* 获批课时信息 */}
          <div className="flex items-center gap-4 p-4 rounded-xl bg-[#fafbfc] border border-[#f0f0f2] mb-5">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-lg bg-[#eff6ff] flex items-center justify-center">
                <Clock className="w-4 h-4 text-[#2563eb]" />
              </div>
              <div>
                <div className="text-lg font-bold text-[#1a1a2e]">24 次课</div>
                <div className="text-xs text-[#8a8a9e]">已获批</div>
              </div>
            </div>
            <div className="w-px h-10 bg-[#e8e8ea]" />
            <div className="flex gap-5">
              <div>
                <div className="text-sm font-bold text-[#2563eb]">12</div>
                <div className="text-xs text-[#8a8a9e]">理论课</div>
              </div>
              <div>
                <div className="text-sm font-bold text-[#16a34a]">12</div>
                <div className="text-xs text-[#8a8a9e]">实验课</div>
              </div>
            </div>
            <button onClick={() => router.push('/teacher/settings')} className="ml-auto text-xs text-[#078f9b] hover:underline font-medium whitespace-nowrap">
              调整规划
            </button>
          </div>

          {/* 课次筛选 */}
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-4 h-4 text-[#8a8a9e]" />
            {(['all', 'theory', 'lab'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  filter === f
                    ? 'bg-[#2563eb] text-white'
                    : 'bg-[#f5f5f7] text-[#6a6a7e] hover:bg-[#e8e8ea]'
                }`}
              >
                {f === 'all' ? '全部课次' : f === 'theory' ? '理论课' : '实验课'}
              </button>
            ))}
            <span className="ml-auto text-xs text-[#8a8a9e]">{filteredLessons.length} 次课</span>
          </div>

          {/* 课次列表 */}
          <div className="space-y-1.5 max-h-[500px] overflow-y-auto">
            {filteredLessons.map(l => (
              <button key={l.num} onClick={() => router.push(`/learn/python-data-analysis?lecture=${l.num}&tab=doc`)} className="flex w-full items-center gap-3 px-3 py-2.5 rounded-lg text-left hover:bg-[#f1fbfa] transition-colors">
                <span className="text-xs font-bold text-[#8a8a9e] w-8 text-center">{l.num}</span>
                <span className="flex-1 text-sm text-[#1a1a2e] truncate">{l.title}</span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                  l.type === 'theory' ? 'bg-[#eff6ff] text-[#2563eb]' : 'bg-[#f0fdf4] text-[#16a34a]'
                }`}>
                  {l.type === 'theory' ? '理论' : '实验'}
                </span>
                <span className="text-xs text-[#c8c8d2] w-24 text-right">{l.date}</span>
                <ExternalLink className="h-3.5 w-3.5 shrink-0 text-[#9ab0b3]" />
              </button>
            ))}
          </div>
        </div>

        {/* 右栏：课程规则配置 */}
        <div className="bg-white rounded-2xl border border-[#e8e8ea] p-6 shadow-[0_1px_3px_rgba(30,27,75,0.04)] h-fit">
          <h2 className="font-bold text-[#1a1a2e] mb-4 flex items-center gap-2">
            <Settings2 className="w-4 h-4 text-[#2563eb]" /> 课程规则配置
          </h2>
          <div className="space-y-4">
            {RULES.map((r, i) => (
              <div key={i} className="pb-4 border-b border-[#f0f0f2] last:border-0 last:pb-0">
                <div className="text-xs text-[#8a8a9e] mb-1">{r.label}</div>
                <div className="text-sm font-medium text-[#1a1a2e]">{r.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 上传资料弹窗 */}
      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowUpload(false)}>
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md mx-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-[#1a1a2e]">上传课程资料</h2>
              <button onClick={() => setShowUpload(false)} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
                <X className="w-4 h-4 text-[#8a8a9e]" />
              </button>
            </div>

            {uploadDone ? (
              <div className="text-center py-8">
                <CheckCircle2 className="w-12 h-12 text-[#16a34a] mx-auto mb-3" />
                <p className="text-sm font-bold text-[#1a1a2e]">上传成功</p>
                <p className="text-xs text-[#8a8a9e] mt-1">{uploadForm.fileName} 已添加到 {uploadForm.type}</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[#6a6a7e] mb-1.5 block">资料类型</label>
                  <select
                    value={uploadForm.type}
                    onChange={e => setUploadForm({ ...uploadForm, type: e.target.value })}
                    className="w-full px-3 py-2.5 rounded-lg border border-[#e0e0e8] text-sm outline-none focus:border-[#2563eb] bg-white"
                  >
                    {MATERIAL_TYPES.map(t => <option key={t.name} value={t.name}>{t.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-[#6a6a7e] mb-1.5 block">选择文件 *</label>
                  <input
                    ref={fileInputRef}
                    type="file"
                    onChange={handleFileChange}
                    className="w-full text-sm text-[#6a6a7e] file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-[#eff6ff] file:text-[#2563eb] hover:file:bg-[#dbeafe] file:cursor-pointer"
                  />
                  {selectedFile && (
                    <p className="text-xs text-[#16a34a] mt-2 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> 已选择：{selectedFile.name}
                    </p>
                  )}
                </div>
              </div>
            )}

            {!uploadDone && (
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowUpload(false)}
                  className="flex-1 py-2.5 rounded-lg border border-[#e0e0e8] text-sm text-[#6a6a7e] hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleUpload}
                  disabled={!selectedFile}
                  className="flex-1 py-2.5 rounded-lg bg-[#2563eb] text-white text-sm font-medium hover:bg-[#1d4ed8] disabled:opacity-40 transition-colors"
                >
                  确认上传
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
