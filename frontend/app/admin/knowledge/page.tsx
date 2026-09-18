'use client';
import { useState, useEffect } from 'react';
import { Database, FileText, Layers, Clock, AlertTriangle, CheckCircle, Search, BookOpen, HardDrive, BarChart3, Shield } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export default function AdminKnowledgePage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/knowledge/assets`).then(r => r.json()).then(d => { setStats(Array.isArray(d) ? { assets: d } : d); }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const totalDocs = stats?.assets?.length || 0;
  const totalChunks = stats?.counts?.chunks || 0;

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2"><Database className="w-6 h-6 text-indigo-500" />知识库管理</h1>
          <p className="text-sm text-gray-400 mt-1">文档索引 · Chunk 切分 · 向量化状态</p>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { l:'文档数量', v: totalDocs || '--', icon: <FileText className="w-5 h-5" />, color: 'from-indigo-50 to-indigo-100/50 border-indigo-100' },
          { l:'Chunk 数量', v: totalChunks || '--', icon: <Layers className="w-5 h-5" />, color: 'from-blue-50 to-blue-100/50 border-blue-100' },
          { l:'索引状态', v: totalDocs > 0 ? '已就绪' : '待建立', icon: <CheckCircle className="w-5 h-5" />, color: totalDocs > 0 ? 'from-emerald-50 to-emerald-100/50 border-emerald-100' : 'from-amber-50 to-amber-100/50 border-amber-100' },
          { l:'最后更新', v: '--', icon: <Clock className="w-5 h-5" />, color: 'from-violet-50 to-violet-100/50 border-violet-100' },
        ].map((s, i) => (
          <div key={i} className={`bg-gradient-to-br ${s.color} rounded-2xl border p-5`}>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white shadow-sm mb-3">{s.icon}</div>
            <div className="text-2xl font-bold text-gray-800">{s.v}</div>
            <div className="text-sm text-gray-500">{s.l}</div>
          </div>
        ))}
      </div>

      {/* 知识库架构说明 */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-indigo-500" />知识库架构
          </h2>
          <div className="space-y-4">
            {[
              { step: 1, title: '文档采集', desc: '课程讲义、教材、参考资料的 PDF/HTML/Markdown 格式导入', icon: <FileText className="w-4 h-4" />, color: 'bg-indigo-50 text-indigo-600 border-indigo-200' },
              { step: 2, title: '文本切分 (Chunking)', desc: '按段落/标题切分为语义完整的 chunk，每个 512-1024 tokens', icon: <Layers className="w-4 h-4" />, color: 'bg-blue-50 text-blue-600 border-blue-200' },
              { step: 3, title: '向量化嵌入 (Embedding)', desc: 'DeepSeek Embedding 模型将 chunk 转为高维向量存入 ChromaDB', icon: <Database className="w-4 h-4" />, color: 'bg-violet-50 text-violet-600 border-violet-200' },
              { step: 4, title: '混合检索 (Hybrid RAG)', desc: 'BM25 关键词 + 向量语义检索 + 重排序，确保相关性和覆盖率', icon: <Search className="w-4 h-4" />, color: 'bg-emerald-50 text-emerald-600 border-emerald-200' },
            ].map(item => (
              <div key={item.step} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className={`flex h-8 w-8 items-center justify-center rounded-full border-2 ${item.color} text-xs font-bold`}>{item.step}</div>
                  {item.step < 4 && <div className="w-0.5 flex-1 bg-gray-100 mt-1" />}
                </div>
                <div className="pb-4 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {item.icon}
                    <h3 className="text-sm font-semibold text-gray-800">{item.title}</h3>
                  </div>
                  <p className="text-xs text-gray-400">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-indigo-500" />存储信息
            </h2>
            <div className="space-y-3">
              {[
                { l:'向量数据库', v:'ChromaDB (本地)' },
                { l:'嵌入模型', v:'DeepSeek Embedding' },
                { l:'检索方式', v:'BM25 + 向量 + Rerank' },
                { l:'Chunk 大小', v:'512-1024 tokens' },
                { l:'Overlap', v:'128 tokens' },
              ].map(item => (
                <div key={item.l} className="flex items-center justify-between py-1.5">
                  <span className="text-sm text-gray-500">{item.l}</span>
                  <span className="text-sm font-medium text-gray-700">{item.v}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gradient-to-br from-indigo-50 to-violet-50 rounded-2xl border border-indigo-100 p-5">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-indigo-500" />
              <span className="text-xs font-semibold text-indigo-700">RAG 质量保障</span>
            </div>
            <p className="text-xs text-indigo-500 leading-relaxed">
              每条回答附带证据溯源，标注来源 chunk ID 和置信度评分，支持管理端查阅审核。
            </p>
          </div>
        </div>
      </div>

      {(!stats || !stats.assets?.length) && !loading && (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 shadow-sm text-center">
          <Database className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-400 mb-1">暂无知识库数据</p>
          <p className="text-xs text-gray-300">导入课程文档后将在此处显示知识库资产状态</p>
        </div>
      )}
    </div>
  );
}
