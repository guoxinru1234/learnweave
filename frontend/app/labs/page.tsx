'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';  // 新增
import { Database, Eye, FileText, FlaskConical, Layers, Search, X } from 'lucide-react';
import { api, type DatasetAsset, type KnowledgePoint, type LabAsset, type LabDetail } from '@/lib/api';

export default function LabsPage() {
  const router = useRouter();  // 新增
  const [labs, setLabs] = useState<LabAsset[]>([]);
  const [datasets, setDatasets] = useState<DatasetAsset[]>([]);
  const [points, setPoints] = useState<KnowledgePoint[]>([]);
  const [selectedLab, setSelectedLab] = useState<LabDetail | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<DatasetAsset | null>(null);
  const [category, setCategory] = useState('all');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    Promise.all([api.getLabs(), api.getDatasets(), api.getKnowledgePoints()])
      .then(([labData, datasetData, pointData]) => {
        if (!active) return;
        setLabs(labData.labs || []);
        setDatasets(datasetData.datasets || []);
        setPoints(pointData.knowledge_points || []);
      })
      .catch(() => {
        if (active) setError('实验资产暂时无法同步，请确认后端服务已启动。');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const categories = useMemo(() => ['all', ...Array.from(new Set(labs.map(lab => lab.category)))], [labs]);
  const filteredLabs = useMemo(() => labs.filter(lab => {
    const categoryMatched = category === 'all' || lab.category === category;
    const q = query.trim().toLowerCase();
    const queryMatched = !q || lab.title.toLowerCase().includes(q) || lab.topics.join(' ').toLowerCase().includes(q);
    return categoryMatched && queryMatched;
  }), [category, labs, query]);

  // ===== 修改这里：点击实验卡片跳转到工作台 =====
  const openLab = (lab: LabAsset) => {
    router.push(`/labs/${lab.id}`);
  };

  const openDataset = (dataset: DatasetAsset) => {
    setSelectedLab(null);
    setDetailError('');
    setSelectedDataset(dataset);
  };

  const filterByPoint = (point: KnowledgePoint) => {
    setQuery(point.name);
    setCategory('all');
    setSelectedLab(null);
    setSelectedDataset(null);
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl">
      <div className="text-xs text-[var(--lm-text-tertiary)] mb-2">首页 / 实验中心</div>
      <div className="flex flex-wrap justify-between items-start gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold">实验中心</h1>
          <p className="text-sm text-[var(--lm-text-secondary)] mt-1">实验手册、案例、数据集和知识点统一接入课程资产库</p>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-[var(--lm-border)] bg-[var(--lm-surface)] px-3 py-2">
          <Search className="w-4 h-4 text-[var(--lm-text-tertiary)]" />
          <input
            value={query}
            onChange={event => setQuery(event.target.value)}
            className="w-[220px] bg-transparent text-sm outline-none"
            placeholder="搜索实验或知识点"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { icon: FlaskConical, value: labs.length, label: '实验/案例资产', color: 'text-[#4f46e5]', bg: 'bg-[var(--lm-brand-light)]' },
          { icon: Database, value: datasets.length, label: '数据集文件', color: 'text-[#2563eb]', bg: 'bg-[var(--lm-info-bg)]' },
          { icon: Layers, value: points.length, label: '知识点', color: 'text-[#16a34a]', bg: 'bg-[var(--lm-success-bg)]' },
          { icon: FileText, value: labs.reduce((sum, lab) => sum + lab.chunk_count, 0), label: '可检索文本块', color: 'text-[#d97706]', bg: 'bg-[var(--lm-warning-bg)]' },
        ].map((item, index) => (
          <div key={index} className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-4">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-xl ${item.bg} ${item.color} flex items-center justify-center`}>
                <item.icon className="w-5 h-5" />
              </div>
              <div>
                <div className="text-2xl font-bold">{item.value}</div>
                <div className="text-sm text-[var(--lm-text-secondary)]">{item.label}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 mb-6">{error}</div>}

      <div className="grid lg:grid-cols-[220px_1fr_300px] gap-6">
        <aside className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-4 h-fit">
          <h3 className="text-sm font-semibold mb-3">资产分类</h3>
          <div className="space-y-1">
            {categories.map(item => (
              <button
                key={item}
                onClick={() => setCategory(item)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${category === item ? 'bg-[#4f46e5] text-white' : 'hover:bg-[var(--lm-brand-light)] text-[var(--lm-text-secondary)]'}`}
              >
                {item === 'all' ? '全部资产' : item}
              </button>
            ))}
          </div>
        </aside>

        <section className="space-y-3">
          {loading ? (
            <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-8 text-center text-sm text-[var(--lm-text-secondary)]">正在同步实验资产...</div>
          ) : filteredLabs.length ? filteredLabs.map(lab => (
            <button
              key={lab.id}
              type="button"
              data-testid={`lab-card-${lab.id}`}
              onClick={() => openLab(lab)}
              className={`w-full text-left bg-[var(--lm-surface)] rounded-2xl border-2 border-black dark:border-white p-5 transition-all hover:shadow-md hover:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                <div>
                  <div className="font-semibold text-[var(--lm-text)]">{lab.title}</div>
                  <div className="text-xs text-[var(--lm-text-secondary)] mt-1">{lab.source_path}</div>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-[var(--lm-brand-light)] text-[#4f46e5] font-medium">{lab.category}</span>
              </div>
              <div className="flex flex-wrap gap-2 mb-4">
                {lab.topics.slice(0, 5).map(topic => (
                  <span key={topic} className="text-xs px-2 py-1 rounded-full bg-[var(--lm-info-bg)] text-[#2563eb]">{topic}</span>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div><span className="text-[var(--lm-text-tertiary)]">关联讲次</span><br /><span className="font-semibold">{Array.isArray(lab.lecture_ids) ? lab.lecture_ids.join(', ') : (lab.lecture_ids || '-')}</span></div>
                <div><span className="text-[var(--lm-text-tertiary)]">文本块</span><br /><span className="font-semibold">{lab.chunk_count}</span></div>
                <div><span className="text-[var(--lm-text-tertiary)]">字符数</span><br /><span className="font-semibold">{lab.text_chars}</span></div>
              </div>
              <div className="mt-4 flex items-center gap-2 text-sm font-medium text-[#4f46e5]">
                <Eye className="w-4 h-4" />
                进入实验 →
              </div>
            </button>
          )) : (
            <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-8 text-center text-sm text-[var(--lm-text-secondary)]">没有匹配的实验资产。</div>
          )}
        </section>

        <aside className="space-y-4">
          <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-4">
            {selectedDataset ? (
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <h3 className="text-sm font-semibold">数据集详情</h3>
                    <div className="text-base font-bold mt-1">{selectedDataset.title}</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedDataset(null)}
                    className="w-8 h-8 rounded-lg border border-[var(--lm-border)] flex items-center justify-center hover:bg-[var(--lm-brand-light)]"
                    aria-label="关闭数据集详情"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="space-y-2 text-sm">
                  <div><span className="text-[var(--lm-text-tertiary)]">来源：</span>{selectedDataset.source_path}</div>
                  <div><span className="text-[var(--lm-text-tertiary)]">格式：</span>{selectedDataset.suffix}</div>
                  <div><span className="text-[var(--lm-text-tertiary)]">字符数：</span>{selectedDataset.text_chars}</div>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {selectedDataset.topics.map(topic => (
                    <span key={topic} className="text-xs px-2 py-1 rounded-full bg-[var(--lm-info-bg)] text-[#2563eb]">{topic}</span>
                  ))}
                </div>
              </div>
            ) : (
              <div>
                <h3 className="text-sm font-semibold mb-2">💡 提示</h3>
                <p className="text-sm text-[var(--lm-text-secondary)] leading-6">
                  点击实验卡片进入「实验工作台」，在代码编辑器中完成实验任务。
                </p>
                <div className="mt-3 p-3 rounded-xl bg-[var(--lm-brand-light)] text-sm">
                  <span className="font-medium">🎯 实验工作台支持：</span>
                  <ul className="mt-1 space-y-1 text-[var(--lm-text-secondary)]">
                    <li>• 代码编辑器（Python）</li>
                    <li>• 运行代码并查看结果</li>
                    <li>• 分步骤完成任务</li>
                    <li>• 智能批改</li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-4">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Database className="w-4 h-4" /> 数据集</h3>
            {datasets.slice(0, 5).map(dataset => (
              <button
                key={dataset.id}
                type="button"
                onClick={() => openDataset(dataset)}
                className="w-full text-left py-2 border-b border-[var(--lm-border)] last:border-0 hover:text-[#4f46e5]"
              >
                <div className="text-sm font-medium">{dataset.title}</div>
                <div className="text-xs text-[var(--lm-text-tertiary)]">{dataset.suffix} · {dataset.text_chars} chars</div>
              </button>
            ))}
          </div>

          <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-4">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Layers className="w-4 h-4" /> 高频知识点</h3>
            {points.slice(0, 8).map(point => (
              <button
                key={point.id}
                type="button"
                onClick={() => filterByPoint(point)}
                className="w-full flex items-center gap-2 py-2 text-left hover:text-[#4f46e5]"
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{point.name}</div>
                  <div className="text-xs text-[var(--lm-text-tertiary)]">讲次 {Array.isArray(point.lecture_ids) ? point.lecture_ids.join(', ') : (point.lecture_ids || '-')}</div>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-[var(--lm-success-bg)] text-[#16a34a]">{point.asset_count}</span>
              </button>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}