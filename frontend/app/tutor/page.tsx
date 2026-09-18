'use client';
import { useState } from 'react';
import { Send, AlertTriangle, CheckCircle, Lightbulb } from 'lucide-react';
import { api, type AgentSource } from '@/lib/api';

type TutorMessage = {
  role: 'user' | 'ai';
  text: string;
  sources?: AgentSource[];
  relatedLabs?: AgentSource[];
};

function cleanTutorText(text: string) {
  return String(text || '')
    .replace(/<think\b[^>]*>[\s\S]*?<\/think>/gi, '')
    .replace(/<analysis\b[^>]*>[\s\S]*?<\/analysis>/gi, '')
    .replace(/<(?:think|analysis)\b[^>]*>[\s\S]*$/gi, '')
    .replace(/^\s*(?:一句话说|简单来说|简而言之|概括来说|总的来说)[，,：:]?\s*/, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

const TOPICS = ['Python基础', 'NumPy数组操作', 'Pandas数据处理', '数据清洗', 'Matplotlib可视化', 'Seaborn统计图', '数据ETL管道', 'Scikit-learn入门', 'SQL与数据库', '数据分析实战'];

export default function TutorPage() {
  const [input, setInput] = useState('');
  const [topic, setTopic] = useState(() => {
    try { return localStorage.getItem('tutor_topic') || 'Pandas数据处理'; } catch { return 'Pandas数据处理'; }
  });
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<TutorMessage[]>([
    { role: 'ai', text: `我是 AI 辅导 Agent，当前上下文：【${topic}】。我会严格依据课程资料和实验手册回答，并标注实际引用来源。若资料没有覆盖你的问题，我会直接说明。请开始提问。` }
  ]);

  const send = async (nextQuestion?: string) => {
    const question = (nextQuestion ?? input).trim();
    if (!question || loading) return;
    setMessages(prev => [...prev, { role: 'user', text: question }]);
    setInput('');
    setLoading(true);

    try {
      const history = messages.slice(-6).map(message => ({
        role: message.role === 'ai' ? 'assistant' : 'user',
        content: message.text,
      }));
      const reply = await api.generateTutor(question, topic, history);
      void api.createNote({ title: `AI导学问题：${question}`, content: cleanTutorText(reply.answer), category: 'wrong_question' }).catch(() => {});
      setMessages(prev => [...prev, {
        role: 'ai',
        text: cleanTutorText(reply.answer),
        sources: reply.sources,
        relatedLabs: reply.related_labs,
      }]);
    } catch {
      // Fallback local response
      void api.createNote({ title: `AI导学问题：${question}`, content: 'AI 服务暂时不可用，已记录本次问题，建议稍后结合课程资料复习。', category: 'wrong_question' }).catch(() => {});
      const q = question.toLowerCase();
      let resp = '根据你的实践驱动型学习风格，建议先看代码示例动手运行。需要我生成具体代码吗？';
      if (q.includes('pandas') || q.includes('dataframe')) resp = 'Pandas DataFrame 是二维带标签的数据结构，类似 Excel 表格。常用操作：df.head()查看前几行、df.describe()统计摘要、df[df[\"列\"]>100]条件筛选、df.groupby(\"列\").mean()分组聚合。';
      if (q.includes('numpy') || q.includes('数组')) resp = 'NumPy 数组 (ndarray) 是 Python 数据科学的基础。相比 Python 列表快 50 倍以上。创建：np.array([1,2,3])、np.zeros((3,4))、np.arange(0,10,2)。';
      if (q.includes('清洗') || q.includes('缺失')) resp = '数据清洗是数据分析的第一步。Pandas 中：df.dropna()删除缺失值、df.fillna(0)填充缺失值、df.drop_duplicates()去重、df[\"列\"].astype(\"int\")类型转换。';
      setMessages(prev => [...prev, { role: 'ai', text: resp }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl">
      <div className="text-xs text-[var(--lm-text-tertiary)] mb-2">首页 / AI 答疑</div>
      <h1 className="mb-1 text-3xl font-bold text-[#0b1419]">AI 智能辅导</h1>
      <p className="text-sm text-[var(--lm-text-secondary)] mb-6">多模态答疑 · 基于画像个性化解答</p>

      <div className="grid lg:grid-cols-[1fr_300px] gap-6">
        <div className="overflow-hidden rounded-xl border border-[#83caca] bg-white shadow-[var(--lm-shadow)]">
          <div className="flex items-center gap-2 border-b border-[#b9d8d9] bg-[#effcfc] px-5 py-4 text-sm font-semibold">
            <span className="h-2 w-2 rounded-full bg-[#10c7b4]" /> 在线 · 上下文：
            <select
              value={topic}
              onChange={e => { setTopic(e.target.value); localStorage.setItem('tutor_topic', e.target.value); }}
              className="cursor-pointer rounded-lg border border-[#83caca] bg-white px-3 py-1 text-sm outline-none focus:border-[#08a9d2]"
            >
              {TOPICS.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="max-h-[520px] space-y-4 overflow-y-auto bg-white p-5">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-xs font-semibold ${msg.role === 'user' ? 'bg-[#078fc3] text-white' : 'bg-gradient-to-br from-[#22d8c8] to-[#08a9d2] text-white'}`}>
                  {msg.role === 'user' ? '李' : 'AI'}
                </div>
                <div className={`max-w-[85%] rounded-xl border px-4 py-3 text-sm leading-6 ${msg.role === 'user' ? 'border-[#078fc3] bg-[#078fc3] text-white' : 'border-[#b9e3df] bg-[#ecfbf9] text-[#18343a]'}`}>
                  {cleanTutorText(msg.text)}
                  {!!msg.sources?.length && (
                    <div className="mt-3 space-y-1.5">
                      <div className="text-xs font-semibold text-[#078f98]">引用来源</div>
                      {msg.sources.slice(0, 3).map((source, si) => (
                        <div key={`${source.title}-${si}`} className="rounded-lg bg-white/70 px-2.5 py-1.5 text-xs text-[var(--lm-text-secondary)]">
                          {source.title}
                          <span className="ml-1 text-[var(--lm-text-tertiary)]">· {source.category}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {!!msg.relatedLabs?.length && (
                    <div className="mt-2 text-xs text-[var(--lm-text-secondary)]">
                      关联实验：{msg.relatedLabs.slice(0, 2).map(lab => lab.title).join('、')}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-2.5">
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-[#22d8c8] to-[#08a9d2] text-xs font-semibold text-white">AI</div>
                <div className="rounded-xl border border-[#b9e3df] bg-[#ecfbf9] px-4 py-3 text-sm text-[var(--lm-text-secondary)]">正在检索课程资料...</div>
              </div>
            )}
          </div>
          <div className="flex gap-3 border-t border-[#b9d8d9] bg-[#f7fdfd] p-4">
            <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} className="flex-1 rounded-lg border border-[#9bcfd0] bg-white px-4 py-3 text-sm outline-none focus:border-[#08a9d2] focus:ring-2 focus:ring-[#c9f4f1]" placeholder="描述你的问题..." />
            <button aria-label="发送问题" onClick={() => send()} disabled={loading} className="rounded-lg bg-gradient-to-r from-[#08a9d2] to-[#12cdbd] px-5 py-3 text-white shadow-sm disabled:opacity-60"><Send className="w-4 h-4" /></button>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-[#83caca] bg-white p-5 shadow-[var(--lm-shadow)]">
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-1.5"><Lightbulb className="w-3.5 h-3.5" /> 你可能想问</h4>
            {['DataFrame和Series有什么区别？','怎么处理缺失值最有效？','groupby之后怎么聚合多个列？','Python列表和NumPy数组性能差多少？'].map((q, i) => (
              <div key={i} className="cursor-pointer border-b border-[#e1f0f0] px-2 py-3 text-sm text-[var(--lm-text-secondary)] transition-colors last:border-0 hover:bg-[#ecfbf9] hover:text-[#078f98]" onClick={() => send(q)}>{q}</div>
            ))}
          </div>
          <div className="rounded-xl border border-[#83caca] bg-white p-5 shadow-[var(--lm-shadow)]">
            <h4 className="text-sm font-semibold mb-3">薄弱点</h4>
            {[
              { title: '数据清洗：缺失值处理', acc: '58%', level: 'danger' },
              { title: 'Pandas分组聚合', acc: '65%', level: 'warning' },
              { title: 'NumPy数组操作', acc: '78%', level: 'success' },
            ].map((w, i) => (
              <div key={i} className={`mb-2 border-l-4 p-3 text-sm ${w.level === 'danger' ? 'border-[#e45b5b] bg-[#fff5f5]' : w.level === 'warning' ? 'border-[#e4a735] bg-[#fffaf0]' : 'border-[#10b7a5] bg-[#effaf8]'}`}>
                <div className="font-semibold">{w.title} — 正确率 {w.acc}</div>
                <div className="text-xs opacity-75 mt-0.5">{w.level === 'danger' ? '建议完成 3 道专项练习' : w.level === 'warning' ? '建议完成 1 个实战案例' : '掌握良好，可进阶练习'}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
