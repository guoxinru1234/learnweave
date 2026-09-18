"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, BookOpen, FlaskConical, FileText, Database, Lightbulb, X, Upload, CheckCircle2, FolderOpen, AlertCircle } from "lucide-react";

type Asset = {
  id: string;
  title: string;
  category: string;
  topics?: string[];
  lecture_id?: number;
  chunk_count?: number;
  source_path?: string;
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";
const CATEGORY_ICONS: Record<string, any> = {
  lecture: BookOpen, lab: FlaskConical, case: Lightbulb,
  exercise: FileText, manual: FileText, dataset: Database,
};
const CATEGORY_NAMES: Record<string, string> = {
  lecture: "课程讲义", lab: "实验指导", case: "案例资料", exercise: "练习题",
  manual: "参考资料", dataset: "数据集", faq: "常见问题", answer: "参考答案",
};
const COVER_STYLES: Record<string, { accent: string; soft: string; label: string }> = {
  lecture: { accent: "#078f9b", soft: "#e8fbfa", label: "COURSE" },
  lab: { accent: "#2563a8", soft: "#eaf3fb", label: "LAB" },
  case: { accent: "#d05f48", soft: "#fff1ed", label: "CASE" },
  exercise: { accent: "#9a6b12", soft: "#fff8df", label: "PRACTICE" },
  manual: { accent: "#52646f", soft: "#eef3f4", label: "REFERENCE" },
  dataset: { accent: "#18835d", soft: "#e9f8f1", label: "DATA" },
  faq: { accent: "#7655a5", soft: "#f3eef9", label: "FAQ" },
  answer: { accent: "#39734c", soft: "#edf7ef", label: "ANSWER" },
};
const MORANDI_PALETTE = [
  { accent: "#718b8b", soft: "#e7ecea" },
  { accent: "#8797a5", soft: "#e9edf0" },
  { accent: "#9a858b", soft: "#eee8e9" },
  { accent: "#9b9078", soft: "#efede6" },
  { accent: "#7f927e", soft: "#e8ede7" },
  { accent: "#8d82a0", soft: "#ece9f0" },
  { accent: "#a38272", soft: "#f0e9e5" },
  { accent: "#72879d", soft: "#e7ebef" },
  { accent: "#9a8f9e", soft: "#eeeaf0" },
  { accent: "#768f89", soft: "#e6ecea" },
  { accent: "#a18e72", soft: "#f0ece4" },
  { accent: "#8290a0", soft: "#e9ecf0" },
];

function assetPalette(asset: Asset) {
  const value = [...asset.id].reduce((sum, char, index) => sum + char.charCodeAt(0) * (index + 1), 0);
  return MORANDI_PALETTE[value % MORANDI_PALETTE.length];
}

function assetNumber(asset: Asset) {
  const value = [...asset.id].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return String((value % 97) + 1).padStart(2, "0");
}

function AssetCover({ asset }: { asset: Asset }) {
  const categoryStyle = COVER_STYLES[asset.category] || COVER_STYLES.manual;
  const palette = assetPalette(asset);
  const style = { ...categoryStyle, ...palette };
  return (
    <div className="relative mx-auto aspect-[3/4] w-[84%] min-w-40">
      <div className="absolute bottom-[-5px] left-1.5 right-[-5px] top-1.5 bg-[#cfd8d7] shadow-[5px_8px_16px_rgba(25,54,58,0.18)]" />
      <div className="absolute inset-0 overflow-hidden border border-black/10" style={{ backgroundColor: style.soft }}>
        <div className="relative flex h-full flex-col px-5 pb-4 pt-4">
          <div className="flex items-start justify-between text-[7px] font-medium text-[#263b43]">
            <span>职业教育课程配套教材</span>
            <span>计算机与数据技术系列</span>
          </div>
          <div className="relative mt-5 h-[38%]">
            <div className="absolute left-[19%] top-[23%] h-[46%] w-[62%] border-[3px] bg-[#e9eef0] shadow-[4px_5px_0_#aab2b3]" style={{ borderColor: style.accent }}>
              <div className="m-1 h-[76%] bg-[#39474d] p-1.5">
                {[72,90,58,82,68].map((width, i) => <div key={i} className="mb-1 h-[2px]" style={{ width: `${width}%`, opacity: .5 + i * .07, backgroundColor: style.accent }} />)}
              </div>
              <div className="mx-auto h-3 w-8 bg-[#8ba0b4]" />
            </div>
            <div className="absolute left-[5%] top-[5%] h-[36%] w-[36%] -rotate-6 border-2 bg-[#435158] p-1 shadow-[3px_3px_0_#a3abad]" style={{ borderColor: style.accent }}>
              {[80,54,68].map((width, i) => <div key={i} className="mb-1 h-[2px]" style={{ width: `${width}%`, backgroundColor: style.accent }} />)}
            </div>
            <div className="absolute right-[1%] top-[2%] h-[38%] w-[34%] rotate-6 border-2 bg-[#435158] p-1 shadow-[3px_3px_0_#a3abad]" style={{ borderColor: style.accent }}>
              {[62,86,48].map((width, i) => <div key={i} className="mb-1 h-[2px] bg-[#d2bec2]" style={{ width: `${width}%` }} />)}
            </div>
            <div className="absolute bottom-[2%] left-[33%] h-[18%] w-[36%] skew-x-[-18deg] border border-[#8b9aa8] bg-[#dde5e7]">
              <div className="m-1 grid grid-cols-7 gap-[1px]">{Array.from({length: 21}).map((_, i) => <span key={i} className="h-[2px] bg-[#96a8af]" />)}</div>
            </div>
            <div className="absolute bottom-[6%] right-[13%] h-3 w-5 rounded-[50%] border border-[#245aa7] bg-[#dfe8ed]" />
            <div className="absolute left-[10%] top-[42%] h-10 w-[2px] rotate-[18deg] bg-[#1c4e9c]" />
            <div className="absolute right-[10%] top-[44%] h-11 w-[2px] -rotate-[18deg] bg-[#1c4e9c]" />
          </div>
          <div className="mt-1 text-center">
            <p className="text-[13px] font-semibold tracking-[0.03em]" style={{ color: style.accent }}>{CATEGORY_NAMES[asset.category] || "课程资料"}</p>
            <h3 className="mx-auto mt-2 line-clamp-3 max-w-[92%] text-[17px] font-bold leading-[1.35] text-[#22282b]">{asset.title}</h3>
            <p className="mt-2 text-[10px] font-medium" style={{ color: style.accent }}>课程知识库版 · {assetNumber(asset)}</p>
          </div>
          <div className="mt-auto text-center">
            <p className="line-clamp-1 text-[7px] text-[#6f7779]">{asset.topics?.slice(0, 3).join(" · ") || "理论 · 实践 · 案例 · 综合训练"}</p>
            <div className="mt-2 border-t border-[#d7dcdd] pt-2 text-[7px] font-medium text-[#3c474a]">LearnWeave 教学资源中心</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function KnowledgeBasePage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState<Asset | null>(null);
  const [chunks, setChunks] = useState<any[]>([]);
  const [chunksLoading, setChunksLoading] = useState(false);

  const openAsset = async (asset: Asset) => {
    setSelected(asset);
    setChunksLoading(true);
    try {
      const r = await fetch(`${API}/api/knowledge/asset/${asset.id}/chunks`);
      const d = await r.json();
      setChunks(d.chunks || []);
    } catch { setChunks([]); }
    finally { setChunksLoading(false); }
  };

  const [stats, setStats] = useState<any>(null);
  useEffect(() => {
    fetch(`${API}/api/knowledge/assets`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(d => {
        const nextAssets = Array.isArray(d) ? d : Array.isArray(d.assets) ? d.assets : [];
        setAssets(nextAssets);
        setLoadError("");
        if (d?.counts) setStats(d.counts);
      })
      .catch(() => { setAssets([]); setLoadError("知识库目录加载失败，请稍后重试"); })
      .finally(() => setLoading(false));
  }, []);

  const search = useCallback(async () => {
    if (!query.trim()) { setResults([]); return; }
    setSearching(true);
    try {
      const r = await fetch(`${API}/api/knowledge/search?q=${encodeURIComponent(query)}`);
      const d = await r.json();
      setResults(d.results || []);
    } finally { setSearching(false); }
  }, [query]);

  const filtered = filter === "all" ? assets : assets.filter(a => a.category === filter);
  const categories = [...new Set(assets.map(a => a.category))];
  useEffect(() => {
    if (!loading && filter !== "all" && !categories.includes(filter)) setFilter("all");
  }, [categories, filter, loading]);

  // 上传状态
  const [showUpload, setShowUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadDone, setUploadDone] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadCategory, setUploadCategory] = useState("manual");
  const [uploadTopics, setUploadTopics] = useState("");
  const [uploadError, setUploadError] = useState("");
  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setUploadError("");
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', uploadTitle);
      formData.append('category', uploadCategory);
      formData.append('topics', uploadTopics);
      const r = await fetch(`${API}/api/knowledge/upload`, { method: 'POST', body: formData });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "上传失败");
      if (d.success && d.asset) {
        setAssets(prev => [d.asset, ...prev]);
        setUploadDone(true);
        setTimeout(() => {
          setUploadDone(false); setShowUpload(false); setSelectedFile(null); setUploading(false);
          setUploadTitle(""); setUploadTopics(""); setUploadCategory("manual");
        }, 1400);
      }
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "上传失败，请检查文件后重试");
      setUploading(false);
    }
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl">
      <div className="text-xs text-[var(--lm-text-tertiary)] mb-2">首页 / 知识库</div>
      <h1 className="text-2xl font-bold mb-1">知识库管理</h1>
      <p className="text-sm text-[var(--lm-text-secondary)] mb-6">
        {stats ? `${stats.assets} 份资料 · ${stats.chunks} 文本块 · ${Object.keys(stats.by_category || {}).length} 个类别` : `${assets.length} 份资料`} · ChromaDB 向量检索 + 关键词混检
      </p>

      {/* Search + Upload */}
      <div className="flex gap-3 mb-6">
        <div className="flex-1 flex items-center gap-2 bg-[var(--lm-surface)] rounded-xl border border-[var(--lm-border)] px-4 py-3">
          <Search className="w-4 h-4 text-gray-400" />
          <input value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && search()}
            placeholder="搜索知识库..." className="flex-1 bg-transparent outline-none text-sm" />
        </div>
        <button onClick={search} disabled={searching}
          className="px-6 py-3 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
          {searching ? "搜索中..." : "搜索"}
        </button>
        <button onClick={() => setShowUpload(true)}
          className="flex items-center gap-1.5 px-4 py-3 rounded-xl border border-[#2563eb] text-[#2563eb] text-sm font-medium hover:bg-[#eff6ff] transition-colors">
          <Upload className="w-4 h-4" /> 上传资料
        </button>
      </div>

      {/* Search Results */}
      {results.length > 0 && (
        <div className="mb-6 bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-4">
          <h3 className="font-semibold text-sm mb-3">搜索结果 ({results.length})</h3>
          {results.map((r, i) => (
            <div key={i} className="mb-3 p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900">
              <p className="text-sm font-medium text-indigo-900 dark:text-indigo-200">{r.title || r.id}</p>
              <p className="text-xs text-indigo-600 dark:text-indigo-400 mt-1 line-clamp-2">{r.content?.slice(0, 200)}</p>
              <span className="text-xs text-indigo-400 mt-1 inline-block">相关度: {((r.score || 0.5) * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      )}

      {/* Category Filter */}
      <div className="flex gap-2 mb-4 flex-wrap">
        <button onClick={() => setFilter("all")}
          className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${filter === "all" ? "bg-indigo-600 text-white" : "bg-gray-100 dark:bg-gray-800 text-gray-600 hover:bg-gray-200"}`}>
          全部 ({assets.length})
        </button>
        {categories.map(cat => (
          <button key={cat} onClick={() => setFilter(cat)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors capitalize ${filter === cat ? "bg-indigo-600 text-white" : "bg-gray-100 dark:bg-gray-800 text-gray-600 hover:bg-gray-200"}`}>
            {CATEGORY_NAMES[cat] || cat} ({assets.filter(a => a.category === cat).length})
          </button>
        ))}
      </div>

      {/* Asset Grid */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">加载中...</div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {filtered.map(asset => {
            return (
              <div key={asset.id} onClick={() => openAsset(asset)}
                className="overflow-hidden bg-[var(--lm-surface)] rounded-lg border border-[var(--lm-border)] hover:-translate-y-0.5 hover:shadow-md transition-all cursor-pointer">
                <div className="border-b border-[var(--lm-border)] bg-[#eef4f3] px-3 py-6"><AssetCover asset={asset} /></div>
                <div className="p-4">
                  <div className="min-w-0 min-h-24">
                    <h3 className="font-semibold text-[15px] leading-6 line-clamp-2">{asset.title}</h3>
                    <span className="mt-1 block text-xs text-[var(--lm-text-tertiary)]">{CATEGORY_NAMES[asset.category] || asset.category}</span>
                    {asset.topics && asset.topics.length > 0 && (
                      <div className="flex gap-1 mt-2 flex-wrap">
                        {asset.topics.slice(0, 2).map(t => (
                          <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500">{t}</span>
                        ))}
                      </div>
                    )}
                    {asset.chunk_count && (
                      <span className="text-xs text-indigo-500 mt-2 block">{asset.chunk_count} 文本块</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <p>{loadError || (assets.length ? "当前分类暂无资料" : "知识库中暂无资料")}</p>
          {assets.length > 0 && filter !== "all" && <button onClick={() => setFilter("all")} className="mt-3 text-sm font-medium text-[#078f9b]">查看全部资料</button>}
        </div>
      )}

      {/* Asset Detail Modal */}
      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setSelected(null)}>
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 bg-white dark:bg-gray-900 border-b p-4 flex items-center justify-between rounded-t-2xl">
              <div>
                <h2 className="font-bold text-lg">{selected.title}</h2>
                <span className="text-xs text-gray-500 capitalize">{selected.category} · {chunks.length} 个文本块</span>
              </div>
              <button onClick={() => setSelected(null)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-4 space-y-3">
              {chunksLoading ? (
                <div className="text-center py-8 text-gray-400">加载中...</div>
              ) : chunks.length === 0 ? (
                <div className="text-center py-8 text-gray-400">暂无可预览内容</div>
              ) : (
                chunks.map((c, i) => (
                  <div key={i} className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700">
                    <div className="text-xs text-gray-400 mb-2">文本块 #{c.chunk_index + 1}</div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">{c.text?.slice(0, 800)}</p>
                    {c.topics && (
                      <div className="flex gap-1 mt-3 flex-wrap">
                        {c.topics.map((t: string) => <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">{t}</span>)}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
      {/* 上传弹窗 */}
      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowUpload(false)}>
          <div className="bg-white rounded-lg shadow-2xl p-6 w-full max-w-lg mx-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <div><h2 className="text-lg font-bold text-[#18343a]">上传课程资料</h2><p className="mt-1 text-sm text-[#667f83]">解析后将进入课程检索与资源生成依据</p></div>
              <button onClick={() => setShowUpload(false)} className="p-1.5 rounded-lg hover:bg-gray-100"><X className="w-4 h-4 text-[#8a8a9e]" /></button>
            </div>
            {uploadDone ? (
              <div className="text-center py-8">
                <CheckCircle2 className="w-12 h-12 text-[#16a34a] mx-auto mb-3" />
                <p className="text-sm font-bold">上传成功</p>
                <p className="text-xs text-[#8a8a9e] mt-1">{selectedFile?.name} 已添加到知识库</p>
              </div>
            ) : (
              <div className="space-y-4">
                <label className="flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-[#8ed6d3] bg-[#f7fdfd] px-5 text-center hover:bg-[#eefafa]">
                  <FolderOpen className="h-7 w-7 text-[#078f9b]" /><span className="mt-3 text-sm font-semibold text-[#18343a]">选择要接入知识库的文件</span>
                  <span className="mt-1 text-xs text-[#667f83]">支持 PDF、DOCX、TXT、Markdown、CSV、JSON、Python</span>
                  <input type="file" accept=".pdf,.docx,.txt,.md,.csv,.json,.py" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) { setSelectedFile(f); setUploadTitle(f.name.replace(/\.[^.]+$/, "")); setUploadError(""); } }} />
                </label>
                {selectedFile && <div className="flex items-center justify-between rounded-lg border border-[#c8e5e4] px-4 py-3"><div className="min-w-0"><p className="truncate text-sm font-medium text-[#18343a]">{selectedFile.name}</p><p className="mt-0.5 text-xs text-[#667f83]">{(selectedFile.size / 1024).toFixed(1)} KB</p></div><CheckCircle2 className="h-5 w-5 shrink-0 text-[#0f9f78]" /></div>}
                <div className="grid gap-4 sm:grid-cols-2">
                  <div><label className="mb-1.5 block text-xs font-semibold text-[#526b70]">资料名称</label><input value={uploadTitle} onChange={e => setUploadTitle(e.target.value)} placeholder="例如：Pandas 实验指导" className="w-full rounded-lg border border-[#c8dddd] px-3 py-2.5 text-sm outline-none focus:border-[#08b8bd]" /></div>
                  <div><label className="mb-1.5 block text-xs font-semibold text-[#526b70]">资料分类</label><select value={uploadCategory} onChange={e => setUploadCategory(e.target.value)} className="w-full rounded-lg border border-[#c8dddd] bg-white px-3 py-2.5 text-sm outline-none focus:border-[#08b8bd]">{Object.entries(CATEGORY_NAMES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
                </div>
                <div><label className="mb-1.5 block text-xs font-semibold text-[#526b70]">知识标签</label><input value={uploadTopics} onChange={e => setUploadTopics(e.target.value)} placeholder="使用逗号分隔，例如：Pandas，DataFrame，数据清洗" className="w-full rounded-lg border border-[#c8dddd] px-3 py-2.5 text-sm outline-none focus:border-[#08b8bd]" /></div>
                {uploadError && <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{uploadError}</div>}
              </div>
            )}
            {!uploadDone && (
              <div className="flex gap-3 mt-6">
                <button onClick={() => setShowUpload(false)} className="flex-1 py-2.5 rounded-lg border border-[#c8dddd] text-sm text-[#526b70] hover:bg-[#f4fafa]">取消</button>
                <button onClick={handleUpload} disabled={!selectedFile || uploading} className="flex-1 py-2.5 rounded-lg bg-[#078f9b] text-white text-sm font-medium hover:bg-[#067b85] disabled:opacity-40">{uploading ? '解析并接入中...' : '上传并接入知识库'}</button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
