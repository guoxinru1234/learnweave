'use client';

import { useEffect, useState, useRef } from 'react';
import { api } from '@/lib/api';
import { Plus, Edit2, Trash2, Search, Download, X, ChevronDown, ChevronRight } from 'lucide-react';

type Note = {
  id: number;
  lecture_id: number;
  category: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
};

function formatNoteContent(content: string): { text: string; data?: any } {
  try {
    const data = JSON.parse(content);
    if (data?.question) return { text: data.question, data };
  } catch { /* 普通笔记文本 */ }
  return { text: content };
}

const CATEGORIES = [
  { value: 'course', label: '课程笔记', color: 'bg-[#eef3ff] text-[#3156b8] border-[#d7e1ff]' },
  { value: 'personal', label: '个人笔记', color: 'bg-[#edf7f4] text-[#356b5e] border-[#d5e9e3]' },
  { value: 'business', label: '项目笔记', color: 'bg-[#f4f1fa] text-[#65517f] border-[#e2d9ef]' },
  { value: 'meeting', label: '会议记录', color: 'bg-[#faf5ea] text-[#8a642e] border-[#eadfc9]' },
];

const CATEGORY_ICONS: Record<string, string> = {
  course: '📖',
  personal: '👤',
  business: '💼',
  meeting: '📋',
};

interface NoteSectionProps {
  lectureId: number;
  compact?: boolean;
}

export default function NoteSection({ lectureId, compact = false }: NoteSectionProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [showEditor, setShowEditor] = useState(false);
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('course');
  const [isSaving, setIsSaving] = useState(false);
  const [expandedNoteId, setExpandedNoteId] = useState<number | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const fetchNotes = async () => {
    setLoading(true);
    try {
      const params: any = {};
      // 只有 lectureId 不为 0 时才添加 lecture_id 参数
      // lectureId === 0 表示"全部笔记"，不传 lecture_id
      if (lectureId !== 0) {
        params.lecture_id = lectureId;
      }
      if (searchTerm.trim()) params.q = searchTerm.trim();
      if (selectedCategory) params.category = selectedCategory;
      const data = await api.getNotes(params);
      setNotes(data);
    } catch (e) {
      console.error('Failed to fetch notes', e);
    } finally {
      setLoading(false);
    }
  };

  // 当 lectureId 变化、搜索词变化、分类变化时重新获取
  useEffect(() => {
    fetchNotes();
  }, [lectureId, searchTerm, selectedCategory]);

  const handleSave = async () => {
    if (!content.trim()) return;
    setIsSaving(true);
    try {
      if (editingNote) {
        await api.updateNote(editingNote.id, {
          title: title.trim() || '无标题笔记',
          content,
          category,
        });
        await fetchNotes();
        resetEditor();
      } else {
        await api.createNote({
          lecture_id: lectureId,
          title: title.trim() || '无标题笔记',
          content,
          category,
        });
        await fetchNotes();
        resetEditor();
      }
    } catch (e) {
      console.error('Failed to save note', e);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (noteId: number) => {
    if (!confirm('确定要删除这条笔记吗？')) return;
    try {
      await api.deleteNote(noteId);
      await fetchNotes();
    } catch (e) {
      console.error('Failed to delete note', e);
    }
  };

  const handleEdit = (note: Note) => {
    setEditingNote(note);
    setTitle(note.title);
    setContent(note.content);
    setCategory(note.category || 'course');
    setShowEditor(true);
    setTimeout(() => textareaRef.current?.focus(), 100);
  };

  const resetEditor = () => {
    setShowEditor(false);
    setEditingNote(null);
    setTitle('');
    setContent('');
    setCategory('course');
  };

  const toggleExpand = (noteId: number) => {
    setExpandedNoteId(expandedNoteId === noteId ? null : noteId);
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    if (diff < 172800000) return '昨天';
    return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const getCategoryInfo = (cat: string) => {
    return CATEGORIES.find(c => c.value === cat) || CATEGORIES[0];
  };

  const recentNotes = compact ? notes.slice(0, 3) : notes;

  // ─── 紧凑模式：讲次页面底部 ───
  if (compact) {
    return (
      <div className="mt-6 border-t border-[var(--lm-border)] pt-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-[var(--lm-text-primary)]">📝 快速笔记</h4>
            <span className="text-xs text-[var(--lm-text-tertiary)] bg-[var(--lm-brand-light)] px-2 py-0.5 rounded-full">
              {notes.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => { resetEditor(); setShowEditor(!showEditor); }}
              className="inline-flex items-center gap-1 text-xs font-medium text-[#4f46e5] hover:text-[#4338ca] transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              {showEditor ? '取消' : '添加笔记'}
            </button>
          </div>
        </div>

        {showEditor && (
          <div className="mb-4 rounded-xl border border-[var(--lm-border)] bg-[var(--lm-surface)] p-4 shadow-sm">
            <div className="flex flex-wrap gap-2 mb-3">
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="笔记标题（可选）"
                className="flex-1 min-w-[120px] h-9 rounded-lg border border-[var(--lm-border)] bg-transparent px-3 text-sm outline-none focus:border-[#4f46e5] focus:ring-2 focus:ring-indigo-100"
              />
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="h-9 rounded-lg border border-[var(--lm-border)] bg-transparent px-3 text-sm outline-none focus:border-[#4f46e5] focus:ring-2 focus:ring-indigo-100"
              >
                {CATEGORIES.map(c => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="写笔记... 支持 Markdown 格式"
              rows={3}
              className="w-full resize-none rounded-lg border border-[var(--lm-border)] bg-transparent px-3 py-2 text-sm outline-none focus:border-[#4f46e5] focus:ring-2 focus:ring-indigo-100"
            />
            <div className="flex justify-end gap-2 mt-3">
              <button
                onClick={resetEditor}
                className="px-4 py-1.5 text-sm text-[var(--lm-text-secondary)] hover:bg-[var(--lm-brand-light)] rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={!content.trim() || isSaving}
                className="px-4 py-1.5 text-sm font-medium bg-[#4f46e5] text-white rounded-lg hover:bg-[#4338ca] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {isSaving ? '保存中...' : editingNote ? '更新' : '保存'}
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="py-4 text-center text-sm text-[var(--lm-text-tertiary)]">加载中...</div>
        ) : recentNotes.length === 0 ? (
          <div className="py-4 text-center text-sm text-[var(--lm-text-tertiary)]">
            {searchTerm ? '没有匹配的笔记' : '还没有笔记，添加第一条吧 ✨'}
          </div>
        ) : (
          <ul className="space-y-2">
            {recentNotes.map((note) => {
              const catInfo = getCategoryInfo(note.category);
              return (
                <li
                  key={note.id}
                  className="group flex items-start gap-3 rounded-xl border border-[var(--lm-border)] px-4 py-3 hover:border-[#4f46e5]/30 hover:shadow-sm transition-all"
                >
                  <button
                    onClick={() => toggleExpand(note.id)}
                    className="flex-1 text-left min-w-0"
                  >
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium truncate">{note.title || '无标题笔记'}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border ${catInfo.color}`}>
                        {catInfo.label}
                      </span>
                      <span className="text-xs text-[var(--lm-text-tertiary)] flex-shrink-0">
                        {formatDate(note.updated_at)}
                      </span>
                    </div>
                    <div className="mt-0.5 text-sm text-[var(--lm-text-tertiary)] truncate">
                      {note.content.slice(0, 60)}
                      {note.content.length > 60 && '...'}
                    </div>
                  </button>
                  <div className="flex items-center gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleEdit(note)}
                      className="p-1.5 text-[var(--lm-text-tertiary)] hover:text-[#4f46e5] rounded-lg hover:bg-[var(--lm-brand-light)] transition-colors"
                      title="编辑"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(note.id)}
                      className="p-1.5 text-[var(--lm-text-tertiary)] hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"
                      title="删除"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}

        {notes.length > 3 && (
          <div className="mt-3 text-center">
            <a
              href="/notes"
              className="text-sm text-[#4f46e5] hover:underline inline-flex items-center gap-1"
            >
              查看全部 {notes.length} 条笔记 →
            </a>
          </div>
        )}
      </div>
    );
  }

  // ─── 完整模式：独立笔记管理页 ───
  return (
    <div className="mx-auto max-w-6xl">
      {/* 头部 */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#078f9b]">Knowledge workspace</div>
          <h1 className="text-3xl font-semibold text-[#171b24]">我的笔记</h1>
          <p className="mt-2 text-sm text-[#707784]">整理课程要点、实践记录与个人思考。</p>
        </div>
        <button
          onClick={() => { resetEditor(); setShowEditor(!showEditor); }}
          className="inline-flex items-center gap-2 rounded-md bg-gradient-to-r from-[#078fc3] to-[#08b8bd] px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
        >
          <Plus className="w-4 h-4" />
          新建笔记
        </button>
      </div>

      {/* 搜索 + 分类筛选 */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--lm-text-tertiary)]" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="搜索笔记内容..."
            className="h-11 w-full rounded-md border border-[#c8e0e1] bg-white pl-10 pr-4 text-sm outline-none transition-colors focus:border-[#08b8bd] focus:ring-2 focus:ring-[#dff7f5]"
          />
        </div>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="h-11 cursor-pointer appearance-none rounded-md border border-[#c8e0e1] bg-white px-4 pr-8 text-sm outline-none transition-colors focus:border-[#08b8bd] focus:ring-2 focus:ring-[#dff7f5]"
        >
          <option value="">全部分类</option>
          {CATEGORIES.map(c => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
        {selectedCategory && (
          <button
            onClick={() => setSelectedCategory('')}
            className="h-11 px-4 text-sm text-[var(--lm-text-tertiary)] hover:text-[#4f46e5] transition-colors"
          >
            清除筛选
          </button>
        )}
      </div>

      {/* 编辑器 */}
      {showEditor && (
        <div className="mb-6 rounded-md border border-[#dfe3ea] bg-white p-5 shadow-[var(--lm-shadow)]">
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="笔记标题（可选）"
              className="flex-1 min-w-[150px] h-10 rounded-lg border border-[var(--lm-border)] bg-transparent px-3 text-sm outline-none focus:border-[#4f46e5] focus:ring-2 focus:ring-indigo-100"
            />
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="h-10 rounded-lg border border-[var(--lm-border)] bg-transparent px-3 text-sm outline-none focus:border-[#4f46e5] focus:ring-2 focus:ring-indigo-100"
            >
              {CATEGORIES.map(c => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
            <button
              onClick={resetEditor}
              className="text-[var(--lm-text-tertiary)] hover:text-red-500 transition-colors p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="写笔记... 支持 Markdown 格式"
            rows={6}
            className="w-full resize-none rounded-md border border-[#c8e0e1] bg-white px-4 py-3 text-sm leading-relaxed outline-none transition-colors focus:border-[#08b8bd] focus:ring-2 focus:ring-[#dff7f5]"
          />
          <div className="flex justify-end gap-3 mt-4">
            <button
              onClick={resetEditor}
              className="rounded-md px-5 py-2 text-sm font-medium text-[var(--lm-text-secondary)] transition-colors hover:bg-[#f2f4f7]"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              disabled={!content.trim() || isSaving}
              className="rounded-md bg-gradient-to-r from-[#078fc3] to-[#08b8bd] px-5 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSaving ? '保存中...' : editingNote ? '更新笔记' : '保存笔记'}
            </button>
          </div>
        </div>
      )}

      {/* 笔记列表 */}
      {loading ? (
        <div className="py-16 text-center text-[var(--lm-text-tertiary)]">加载中...</div>
      ) : notes.length === 0 ? (
        <div className="py-16 text-center">
          <div className="text-4xl mb-3">📝</div>
          <div className="text-[var(--lm-text-secondary)]">
            {searchTerm || selectedCategory ? '没有匹配的笔记' : '还没有笔记，开始创建第一条吧 ✨'}
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {notes.map((note) => {
            const catInfo = getCategoryInfo(note.category);
            const isExpanded = expandedNoteId === note.id;
            return (
              <div
                key={note.id}
                className="group rounded-md border border-[#dfe3ea] bg-white transition-colors hover:border-[#b9c7ed] hover:bg-[#fcfdff]"
              >
                <div className="flex items-start gap-4 p-4">
                  {/* 分类图标 */}
                  <div className="hidden">
                    {CATEGORY_ICONS[note.category] || '📌'}
                  </div>

                  <div className="mt-1 h-8 w-1 flex-shrink-0 bg-[#08b8bd]" />

                  <button
                    onClick={() => toggleExpand(note.id)}
                    className="flex-1 text-left min-w-0"
                  >
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-[var(--lm-text-primary)]">
                        {note.title || '无标题笔记'}
                      </span>
                      <span className={`border px-2 py-0.5 text-xs ${catInfo.color}`}>
                        {catInfo.label}
                      </span>
                      <span className="text-xs text-[var(--lm-text-tertiary)] flex-shrink-0">
                        {formatDate(note.updated_at)}
                      </span>
                      {note.updated_at !== note.created_at && (
                        <span className="text-xs text-[var(--lm-text-tertiary)] flex-shrink-0">✎ 已编辑</span>
                      )}
                    </div>
                    {isExpanded ? (
                      <div className="mt-3 text-sm text-[var(--lm-text-secondary)] break-words leading-relaxed">
                        {(() => { const parsed = formatNoteContent(note.content); return parsed.data ? <div className="rounded-xl border border-red-100 bg-red-50/50 p-4"><div className="font-semibold text-[#15383f]">{parsed.text}</div>{Array.isArray(parsed.data.options) && <div className="mt-3 grid gap-2">{parsed.data.options.map((option: any, index: number) => <div key={index} className={`rounded-lg border px-3 py-2 ${index === (parsed.data.answer ?? parsed.data.correct_index) ? 'border-green-200 bg-green-50' : 'border-white bg-white'}`}>{String.fromCharCode(65 + index)}. {typeof option === 'string' ? option : option.text || option.label}</div>)}</div>}<div className="mt-3 rounded-lg bg-white p-3 text-sm"><span className="font-semibold text-[#078fbd]">解析：</span>{parsed.data.explanation || '请回顾相关知识点。'}</div></div> : <div className="whitespace-pre-wrap">{parsed.text}</div>; })()}
                      </div>
                    ) : (
                      <div className="mt-1 text-sm text-[var(--lm-text-tertiary)] truncate">
                        {formatNoteContent(note.content).text.slice(0, 120)}
                        {formatNoteContent(note.content).text.length > 120 && '...'}
                      </div>
                    )}
                  </button>

                  <div className="flex items-center gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleEdit(note)}
                      className="rounded-md p-2 text-[var(--lm-text-tertiary)] transition-colors hover:bg-[#eef3ff] hover:text-[#315efb]"
                      title="编辑"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(note.id)}
                      className="rounded-md p-2 text-[var(--lm-text-tertiary)] transition-colors hover:bg-red-50 hover:text-red-500"
                      title="删除"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 底部统计 */}
      {notes.length > 0 && (
        <div className="mt-6 text-center text-xs text-[var(--lm-text-tertiary)]">
          共 {notes.length} 条笔记
        </div>
      )}
    </div>
  );
}
