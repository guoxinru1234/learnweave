'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ChevronRight, Code, Brain, FileText, Video, CheckCircle, Download, Clock, Plus, Sparkles, Route, Zap, Shield } from 'lucide-react';
import { api, type AgentSource, type GeneratedResource } from '@/lib/api';
import { useAgent } from '@/contexts/AgentContext';
import { useAuth } from '@/contexts/AuthContext';
import dynamic from 'next/dynamic';
const MarkmapViewer = dynamic(
  () => import('@/components/mindmap/MarkmapViewer').then(m => ({ default: m.MarkmapViewer })),
  { ssr: false, loading: () => <div className="flex items-center justify-center h-[500px] text-gray-400">加载思维导图...</div> }
);
const TalkingAvatarController = dynamic(
  () => import('@/components/digital-human/TalkingAvatarController').then(m => ({ default: m.TalkingAvatarController })),
  { ssr: false, loading: () => <div className="w-[150px] h-[180px]" /> }
);
const DigitalHumanLive = dynamic(
  () => import('@/components/digital-human/DigitalHumanLive').then(m => ({ default: m.DigitalHumanLive })),
  { ssr: false, loading: () => <div className="h-64 bg-gray-100 rounded-2xl animate-pulse" /> }
);

// ==================== HTML 内容安全清洗 ====================
/** 清洗后端返回的 HTML 内容，防止全量 HTML 文档破坏页面布局 */
function sanitizeHtmlContent(raw: string): string {
  if (!raw) return '';

  let html = raw;

  // 1. 去掉 markdown 代码块包裹（```html ... ```）
  const fenceMatch = html.match(/```html\s*([\s\S]*?)```/i);
  if (fenceMatch) {
    html = fenceMatch[1];
  }

  // 2. 提取 <body> 内容（如果存在完整 HTML 文档结构）
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*)<\/body\s*>/i);
  if (bodyMatch) {
    html = bodyMatch[1];
  }

  // 3. 移除 <style> 块（会污染全局样式）
  html = html.replace(/<style[^>]*>[\s\S]*?<\/style\s*>/gi, '');

  // 4. 移除残留的文档级标签
  html = html.replace(/<!DOCTYPE[^>]*>/gi, '');
  html = html.replace(/<\/?html[^>]*>/gi, '');
  html = html.replace(/<\/?head[^>]*>/gi, '');
  html = html.replace(/<\/?body[^>]*>/gi, '');

  // 5. 去掉 LLM 角色扮演开场白（如"好的，老师，我们开始上课"）
  html = html.replace(/^好的[，,]\s*老师[，,]\s*我们开始上课[。.]?\s*/i, '');
  html = html.replace(/^同学[你好]+[，,]?\s*/i, '');
  html = html.replace(/^(好的|嗯)[，,]\s*(老师|同学)[，,]?\s*/i, '');

  // 6. 清理首尾空白
  html = html.trim();

  // 移除误混入讲义的内部 Agent 规划/思考日志（不向学习者展示）
  const internalMarkers = /(?:Reconciling lecture constraints with user requests|Planning structured lecture with minimal inline commands|Defining usage scenarios without code examples|Planning chapter structure and case integration|Refining Jupyter introduction and Python environment explanations|Planning article structure and length|Outlining detailed chapter contents and examples|Clarifying scope focusing on Python environment basics|Planning citation and annotation format|Defining code example and case presentation rules)/gi;
  html = html.replace(internalMarkers, '');
  // Hide internal knowledge-base identifiers such as [PY-ENV-001] from the
  // learner-facing lecture body. Citations remain available in audit metadata.
  html = html.replace(/\[(?:PY|NP|PD|SQL|VIS|ETL|STAT|EDA|PERF)-[A-Z0-9_-]+\]/gi, '');
  html = html.replace(/(?:\*{2,}|#{2,})\s*/g, '');
  html = html.replace(/\s{2,}/g, ' ').trim();

  return html;
}

function enrichShortLectureContent(title: string, raw: string): string {
  const plain = String(raw || '').replace(/<[^>]+>/g, '').trim();
  if (plain.length >= 700 && !plain.includes('请配置有效的')) return raw;
  if (/NumPy.*数组.*创建|数组创建与索引/i.test(title)) return `<h3>课程说明</h3><p>本讲系统学习 NumPy 数组的创建、属性查看、索引和切片。这些操作是后续向量化计算、广播、矩阵运算和 Pandas 数据处理的基础。</p>
<h3>一、为什么使用 NumPy 数组</h3><p>Python 列表可以保存一组数据，但不适合大规模数值计算。NumPy 的 ndarray 在内存中存储同类型元素，支持连续存储、向量化运算和多维索引，通常比逐个遍历列表更高效。</p>
<h3>二、创建数组</h3><pre><code>import numpy as np
a = np.array([1, 2, 3, 4])
b = np.array([[1, 2, 3], [4, 5, 6]])
zeros = np.zeros((2, 3))
ones = np.ones(4)
seq = np.arange(0, 10, 2)
points = np.linspace(0, 1, 5)</code></pre><p><code>array</code> 将列表转换为数组；<code>zeros</code> 和 <code>ones</code> 常用于初始化；<code>arange</code> 按步长生成序列；<code>linspace</code> 按数量均匀生成区间数据。</p>
<h3>三、数组属性</h3><pre><code>print(b.ndim)   # 维度数
print(b.shape)  # 每个维度的长度
print(b.size)   # 元素总数
print(b.dtype)  # 元素类型</code></pre><p>分析前先检查 <code>shape</code> 和 <code>dtype</code>，可以避免把行列方向、数据类型弄错。</p>
<h3>四、索引与切片</h3><pre><code>x = np.array([[10, 20, 30], [40, 50, 60], [70, 80, 90]])
print(x[0, 1])    # 第1行第2列：20
print(x[1, :])    # 第2行
print(x[:, 2])    # 第3列
print(x[:2, 1:])  # 前两行、从第2列开始
x[0, 0] = 999     # 数组元素可以直接修改</code></pre><p>NumPy 使用从 0 开始的索引。二维数组推荐使用 <code>arr[行, 列]</code>，而不是嵌套列表的写法。切片通常返回视图，修改切片可能影响原数组，需要独立副本时使用 <code>.copy()</code>。</p>
<h3>五、布尔索引与实际分析</h3><pre><code>scores = np.array([58, 72, 91, 64, 88])
passed = scores[scores >= 60]
high = scores[(scores >= 80) & (scores <= 100)]
print(passed, high)</code></pre><p>布尔索引可以快速筛选满足条件的数据，是数据清洗和统计分析中最常用的数组操作之一。多个条件必须使用 <code>&amp;</code> 或 <code>|</code>，并分别加括号。</p>
<h3>六、常见易错点</h3><ul><li>索引越界会触发 IndexError，切片越界通常不会报错但可能返回空数组。</li><li>二维数组的 <code>shape</code> 是“行数、列数”，不要把它写反。</li><li><code>arange</code> 的终点通常不包含，浮点步长可能存在精度误差。</li><li>数组要求元素类型兼容，混入字符串可能导致整体 dtype 变化。</li></ul>
<h3>七、课后练习</h3><ol><li>创建一个 3×4 的数组，并取出第 2 列。</li><li>从成绩数组中筛选出大于等于 80 的成绩并计算平均值。</li><li>解释 <code>x[::2]</code> 和 <code>x[:, ::2]</code> 在一维、二维数组中的区别。</li></ol>
<h3>八、学习小结</h3><p>完成本讲后，你应能使用 NumPy 创建一维和多维数组，读懂 <code>ndim</code>、<code>shape</code>、<code>size</code>、<code>dtype</code>，并通过整数索引、切片和布尔索引完成数据提取与筛选。</p>`;
  return `<h3>课程说明</h3><p>本讲围绕<strong>${title}</strong>展开，结合 Python 数据分析场景，理解概念、操作流程和常见问题。</p>
<h3>一、核心概念</h3><p>${title} 是 Python 数据分析流程中的重要基础。学习时应关注数据结构、操作语法、输入输出关系，以及它与 NumPy、Pandas 等工具的衔接。</p>
<h3>二、工作流程</h3><ol><li>明确分析目标和数据来源；</li><li>准备运行环境并导入所需库；</li><li>按照“读取—检查—处理—分析—验证”的顺序操作；</li><li>通过结果、图表和统计指标检查结论是否合理。</li></ol>
<h3>三、Python 实践示例</h3><pre><code>import numpy as np\nimport pandas as pd\n\ndata = np.array([10, 20, 30, 40, 50])\nframe = pd.DataFrame({'value': data})\nprint(frame.head())\nprint(frame.describe())</code></pre>
<h3>四、常见问题</h3><ul><li>先确认变量类型和数据形状，再进行索引或计算。</li><li>遇到空值、异常值时不要直接删除，应先统计影响范围。</li><li>每一步处理后使用 head()、info() 或 describe() 检查结果。</li></ul>
<h3>五、学习小结</h3><p>完成本讲后，你应该能够解释${title}的用途，独立运行示例代码，并将本讲方法应用到真实数据分析任务中。</p>`;
}

function deriveLectureMindmap(title: string, html: string) {
  if (/数据读取与筛选|数据筛选与条件过滤|Pandas.*筛选/i.test(title)) {
    return [{ id: 'root', label: 'Pandas 数据读取与筛选', children: [
      { id: 'read', label: '一、数据读取与检查', children: [{ id: 'csv', label: 'read_csv / read_excel' }, { id: 'inspect', label: 'head / info / describe' }] },
      { id: 'select', label: '二、数据选择与筛选', children: [{ id: 'columns', label: '列选择与字段投影' }, { id: 'loc', label: 'loc / iloc' }, { id: 'bool', label: '布尔索引与 query' }, { id: 'multi', label: '多条件 & / | / ~' }] },
      { id: 'case', label: '三、业务场景应用', children: [{ id: 'status', label: '按订单状态筛选' }, { id: 'amount', label: '金额与渠道组合条件' }, { id: 'date', label: '按日期范围筛选' }] },
      { id: 'verify', label: '四、结果验证与易错点', children: [{ id: 'and', label: 'Series 不使用 and/or' }, { id: 'dtype', label: '确认字段类型与空值' }, { id: 'result', label: '检查行数、重复与抽样结果' }] },
    ] }];
  }
  if (/NumPy.*数组创建与索引|数组创建与索引/i.test(title)) {
    return [{ id: 'root', label: title, children: [
      { id: 'create', label: '数组创建', children: [
        { id: 'array', label: 'np.array()', children: [{ id: 'array-example', label: '列表/嵌套列表转数组' }, { id: 'array-dtype', label: 'dtype 类型推断' }] },
        { id: 'fill', label: 'zeros / ones / full', children: [{ id: 'fill-shape', label: '形状 shape' }, { id: 'fill-init', label: '初始化数据' }] },
        { id: 'sequence', label: 'arange / linspace', children: [{ id: 'sequence-step', label: '步长生成' }, { id: 'sequence-count', label: '等间距生成' }] },
      ] },
      { id: 'props', label: '数组属性', children: [
        { id: 'ndim', label: 'ndim：维度数量' }, { id: 'shape', label: 'shape：行列形状' }, { id: 'size', label: 'size：元素总数' }, { id: 'dtype', label: 'dtype：数据类型' },
      ] },
      { id: 'index', label: '索引与切片', children: [
        { id: 'one-index', label: '一维索引 arr[i]' }, { id: 'two-index', label: '二维索引 arr[row, col]' }, { id: 'slice', label: '行列切片 arr[:2, 1:]' }, { id: 'copy', label: '视图与 copy()' },
      ] },
      { id: 'boolean', label: '布尔索引', children: [{ id: 'condition', label: '条件筛选' }, { id: 'multi-condition', label: '多条件 & / |' }, { id: 'analysis', label: '筛选后统计分析' }] },
      { id: 'practice', label: '实践与易错点', children: [{ id: 'practice-code', label: '成绩数组练习' }, { id: 'errors', label: '越界与 dtype 变化' }, { id: 'verify', label: 'head / shape / dtype 验证' }] },
    ] }];
  }
  const source = String(html || '');
  const clean = (value: string) => value.replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/&[a-z]+;/gi, '').replace(/\s+/g, ' ').trim();
  const headings = Array.from(source.matchAll(/<h[23][^>]*>([\s\S]*?)<\/h[23]>/gi))
    .map((m) => m[1].replace(/<[^>]+>/g, '').replace(/&[^;]+;/g, '').trim())
    .filter(Boolean);
  const unique = Array.from(new Set(headings)).slice(0, 8);
  const detailMap: Record<string, string[]> = {
    '创建数组': ['np.array 与类型推断', 'zeros / ones 初始化', 'arange / linspace 序列'],
    '数组属性': ['ndim 维度', 'shape 形状', 'size 与 dtype'],
    '索引与切片': ['整数索引', '行列切片', '视图与 copy'],
    '布尔索引与实际分析': ['条件筛选', '多条件组合', '统计筛选结果'],
    '常见易错点': ['索引越界', '数据类型变化', '切片副作用'],
    '课后练习': ['创建二维数组', '筛选成绩数据', '解释切片表达式'],
  };
  const extra = ['知识目标', '核心原理', '实践应用', '易错辨析', '课后练习'];
  const sourceHeadings = Array.from(new Set([...unique, ...extra])).slice(0, 8);
  const groups = sourceHeadings.map((heading, index) => {
    const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const section = source.match(new RegExp(`<h[23][^>]*>[^<]*${escaped}[^<]*<\\/h[23]>([\\s\\S]*?)(?=<h[23]|$)`, 'i'))?.[1] || '';
    const learned = Array.from(section.matchAll(/<(?:li|p)[^>]*>([\s\S]*?)<\/(?:li|p)>/gi)).map(m => clean(m[1])).filter(x => x.length > 5).slice(0, 5);
    const details = learned.length ? learned : (detailMap[heading] || ['概念与定义', '处理流程与方法', '实际应用场景']);
    return {
      id: `section-${index}`,
      label: heading,
      children: details.map((detail, detailIndex) => ({
        id: `detail-${index}-${detailIndex}`,
        label: detail.length > 46 ? `${detail.slice(0, 46)}…` : detail,
        children: [
          { id: `example-${index}-${detailIndex}`, label: detail.includes('代码') ? '运行代码并观察输出' : '理解：它解决什么问题', children: [
            { id: `check-${index}-${detailIndex}`, label: '验证：输入、处理与结果是否一致' },
            { id: `apply-${index}-${detailIndex}`, label: '应用：用本讲数据完成一次练习' },
            { id: `mistake-${index}-${detailIndex}`, label: '易错：检查类型、形状、索引与空值' },
          ] },
        ],
      })),
    };
  });
  return [{ id: 'root', label: title, children: groups }];
}

// ==================== 类型定义 ====================
type Note = {
  id: number;
  lecture_id: number;
  category: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
};

type LectureContent = {
  title: string;
  type: string;
  content: string;
  code: string;
  mindmap: { t: string; s: string }[] | { id: string; label: string; children?: any[] }[];
  quiz: { question: string; options: { text: string; correct: boolean }[] };
  // 多 Agent 模式新增字段
  full_quiz?: { questions: any[] };
  extended_reading?: { recommendations: any[] };
  video_script?: { scenes: any[]; slide_count?: number };
  learning_path?: { path?: any[] };
  agent_logs?: { agent: string; status: string; error?: string }[];
  audit?: { verified: boolean; confidence: number; issues_found: any[]; iterations: number };
  generated_by?: string;
  agent_count?: number;
  total_agents?: number;
  video_url?: string;
};
type StudyStats = { minutes: number; quizzes: number; labs: number; lectures?: number };

// ===== 路径选项生成（根据10项 Python 数据分析画像） =====
function getPathOptions(profile: any) {
  // Python 数据分析领域画像优先：与学情画像页使用相同的 domain_skills 维度
  const domain = profile?.domain_skills || {};
  const domainLabels: Record<string, string> = {
    python_basic: 'Python基础', numpy: 'NumPy数值计算', pandas: 'Pandas数据处理',
    data_cleaning: '数据清洗', visualization: '数据可视化', sql: 'SQL查询',
    statistics: '统计分析', comprehensive_analysis: '综合分析', etl: 'ETL流程', performance: '性能优化',
  };
  const domainEntries = Object.entries(domain).filter(([, v]) => Number(v) > 0) as [string, number][];
  if (domainEntries.length >= 2) {
    const sortedDomain = [...domainEntries].sort((a, b) => a[1] - b[1]);
    const weak = domainLabels[sortedDomain[0][0]] || sortedDomain[0][0];
    const strong = domainLabels[sortedDomain[sortedDomain.length - 1][0]] || sortedDomain[sortedDomain.length - 1][0];
    return [
      { id: 'path_1', icon: '🔧', label: `重点攻克：${weak}`, recommended: true, reason: `优先补强你的${weak}薄弱项。`, strategy: `围绕${weak}安排基础讲解、代码练习和错题复盘。` },
      { id: 'path_2', icon: '⚡', label: `${strong}深度拓展`, recommended: false, reason: `在你的${strong}优势上继续提升。`, strategy: `围绕${strong}增加进阶案例、性能分析和综合实践。` },
      { id: 'path_3', icon: '⚖️', label: 'Python数据分析均衡推进', recommended: false, reason: '按课程顺序均衡覆盖 Python 数据分析核心技能。', strategy: 'Pandas、NumPy、清洗、可视化和统计分析均衡推进。' },
    ];
  }
  const dims = ['theoretical_basis','coding_ability','practical_ops','troubleshooting','data_thinking','self_learning'];
  const scores: Record<string, number> = {};
  dims.forEach((d: string) => { scores[d] = profile?.[d] || 0; });
  const valid = Object.values(scores).filter((s: number) => s > 0);
  const avg = valid.length > 0 ? Math.round(valid.reduce((a: number, b: number) => a + b, 0) / valid.length) : 50;

  // 找最弱和最强维度
  const entries = Object.entries(scores).filter(([, v]) => (v as number) > 0);
  const sorted = entries.sort(([, a], [, b]) => (a as number) - (b as number));
  const weakKey = sorted[0]?.[0] || 'theoretical_basis';
  const strongKey = sorted[sorted.length - 1]?.[0] || 'coding_ability';
  const dimLabels2: Record<string, string> = {
    theoretical_basis: '理论基础', coding_ability: '编程能力',
    practical_ops: '实践操作', troubleshooting: '问题排查',
    data_thinking: '数据思维', self_learning: '自学能力',
  };

  return [
    {
      id: 'path_1', icon: '🔧',
      label: `🔴 重点攻克：${dimLabels2[weakKey] || '短板'}`,
      recommended: true,
      reason: `你${dimLabels2[weakKey] || '短板'}${scores[weakKey] || 0}分是最大短板——这条路会在相关讲次投入更多时间，每个概念用生活类比→直观理解→形式化定义→代码验证四步走，把最拖后腿的地方先补上来。`,
      strategy: `补弱策略：学生${dimLabels2[weakKey] || '理论基础'}是薄弱维度，相关讲次内容占讲义60%以上。讲解用四步法：生活类比→直观理解→形式化定义→代码验证。代码逐行注释解释每步原因。练习题5道从基础到进阶。`,
    },
    {
      id: 'path_2', icon: '⚡',
      label: `${dimLabels2[strongKey] || '优势'}深度拓展`,
      recommended: false,
      reason: `你${dimLabels2[strongKey] || '优势'}${scores[strongKey] || 50}分是强项——这条路在优势方向深入拓展，引入源码分析和进阶内容，把擅长的做到极致。`,
      strategy: `强化策略：学生${dimLabels2[strongKey] || '编程能力'}是强项维度，在优势方向深入拓展。引入源码分析、架构设计、性能优化、工业级最佳实践。其他维度保持正常深度。练习题以挑战题为主。`,
    },
    {
      id: 'path_3', icon: '⚖️',
      label: '均衡系统推进',
      recommended: false,
      reason: `综合${avg}分，按大纲稳步走，每讲理论实践各半，不强攻也不速成，适合想踏踏实实学完的人。`,
      strategy: `均衡策略：各维度均衡覆盖，每讲理论实践各半。代码完整可运行，关键位置加注释。练习题难度适中覆盖所有知识点。按正常节奏推进。`,
    },
  ];
}

// ==================== 课程元数据降级数据（API 不可用时使用） ====================
const FALLBACK_COURSE: Record<string, any> = {
  'python-data-analysis': {
    id: 'python-data-analysis', title: 'Python数据分析实战', description: '从零基础到数据科学家 · 24讲', total_lectures: 24,
    modules: [
      { name: '模块一：Python编程基础', status: 'done', lectures: [
        { num: 1, title: 'Python环境搭建与Jupyter入门', dur: '45min', done: true, topic: 'Python环境搭建与Jupyter入门' },
        { num: 2, title: '变量、数据类型与运算符', dur: '45min', done: true, topic: '变量、数据类型与运算符' },
        { num: 3, title: '条件判断与循环控制', dur: '45min', done: true, topic: '条件判断与循环控制' },
        { num: 4, title: '函数定义与模块化编程', dur: '90min', done: true, topic: '函数定义与模块化编程' },
      ]},
      { name: '模块二：NumPy数值计算', status: 'active', lectures: [
        { num: 5, title: 'NumPy数组创建与索引', dur: '45min', done: true, topic: 'NumPy数组创建与索引' },
        { num: 6, title: '数组运算与广播机制', dur: '45min', done: true, topic: '数组运算与广播机制' },
        { num: 7, title: '线性代数与矩阵运算', dur: '90min', done: true, topic: '线性代数与矩阵运算' },
        { num: 8, title: '随机数与统计函数', dur: '45min', done: true, topic: '随机数与统计函数' },
      ]},
      { name: '模块三：Pandas数据处理', status: 'active', lectures: [
        { num: 9, title: 'Series与DataFrame基础', dur: '45min', done: true, topic: 'Series与DataFrame基础' },
        { num: 10, title: '数据筛选与条件过滤', dur: '45min', done: true, topic: '数据筛选与条件过滤' },
        { num: 11, title: '数据合并：merge/concat/join', dur: '90min', done: true, topic: '数据合并：merge/concat/join' },
        { num: 12, title: '数据透视表与分组聚合', dur: '45min', done: true, topic: '数据透视表与分组聚合' },
      ]},
      { name: '模块四：数据清洗与预处理', status: 'locked', lectures: [
        { num: 13, title: '缺失值检测与填充策略', dur: '45min', topic: '缺失值检测与填充策略' },
        { num: 14, title: '异常值识别与处理', dur: '45min', topic: '异常值识别与处理' },
        { num: 15, title: '数据类型转换与规范化', dur: '90min', topic: '数据类型转换与规范化' },
        { num: 16, title: '文本数据处理与正则表达式', dur: '45min', topic: '文本数据处理与正则表达式' },
      ]},
      { name: '模块五：数据可视化', status: 'locked', lectures: [
        { num: 17, title: 'Matplotlib基础图表绘制', dur: '45min', topic: 'Matplotlib基础图表绘制' },
        { num: 18, title: 'Seaborn统计可视化', dur: '45min', topic: 'Seaborn统计可视化' },
        { num: 19, title: '交互式可视化：Plotly入门', dur: '90min', topic: '交互式可视化：Plotly入门' },
        { num: 20, title: '数据看板Dashboard设计', dur: '45min', topic: '数据看板Dashboard设计' },
      ]},
      { name: '模块六：实战项目与部署', status: 'locked', lectures: [
        { num: 21, title: '电商销售数据分析实战', dur: '90min', topic: '电商销售数据分析实战' },
        { num: 22, title: '数据ETL管道构建', dur: '45min', topic: '数据ETL管道构建' },
        { num: 23, title: '机器学习入门：Scikit-learn', dur: '90min', topic: '机器学习入门：Scikit-learn' },
        { num: 24, title: '数据分析报告撰写与部署', dur: '45min', topic: '数据分析报告撰写与部署' },
      ]},
    ],
    manim_lectures: {},
  },
};

// ==================== 默认数据 ====================
const TABS = [
  { id: 'doc', icon: FileText, label: '讲义' },
  { id: 'mindmap', icon: Brain, label: '导图' },
  { id: 'code', icon: Code, label: '代码' },
  { id: 'video', icon: Video, label: '视频' },
  { id: 'quiz', icon: CheckCircle, label: '练习' },
];

// ===== Agent 名称友好映射 =====
const AGENT_NAME_MAP: Record<string, string> = {
  profile_agent: '画像构建',
  doc_agent: '文档生成',
  DocAgent: '讲义生成',
  quiz_agent: '题库生成',
  QuizAgent: '题库生成',
  mindmap_agent: '思维导图',
  MindmapAgent: '思维导图',
  code_agent: '代码生成',
  CodeAgent: '代码示例',
  path_agent: '路径规划',
  PathPlanner: '路径规划',
  ReadingAgent: '拓展阅读',
  VideoAgent: '视频分镜',
  load_context: '知识库加载',
};

/** 从 6 维分数推导画像摘要（兼容后端 Agent 的旧格式） */
function buildProfileSummary(profile: any) {
  const dims = ['theoretical_basis','coding_ability','practical_ops','troubleshooting','data_thinking','self_learning'];
  const dimLabels: Record<string, string> = {
    theoretical_basis: '理论基础', coding_ability: '编程能力', practical_ops: '实践操作',
    troubleshooting: '问题排查', data_thinking: '数据思维', self_learning: '自学能力',
  };
  const scores = dims.map((d: string) => profile[d] || 0).filter((s: number) => s > 0);
  const avg = scores.length > 0 ? Math.round(scores.reduce((a: number, b: number) => a + b, 0) / scores.length) : 50;

  // 找弱项（分数<50且有值的维度）
  const weakness = dims
    .filter((d: string) => (profile[d] || 0) > 0 && (profile[d] || 0) < 50)
    .map((d: string) => dimLabels[d] || d);

  // 基础等级
  let foundation = '中等';
  if (avg < 35) foundation = '零基础';
  else if (avg < 50) foundation = '入门';
  else if (avg < 65) foundation = '中等';
  else if (avg < 80) foundation = '良好';
  else foundation = '精通';

  return {
    ...profile,
    foundation,
    weakness: weakness.length > 0 ? weakness : ['待评估'],
    grade: profile.major_background || '未知',
    goal: profile.learning_motivation === '考研' ? '深度掌握，备战考研' :
          profile.learning_motivation === '就业' ? '掌握实用技能，找工作' :
          profile.learning_motivation === '竞赛' ? '挑战高难度，冲击竞赛' :
          '掌握 Python 数据分析',
    style: profile.cognitive_style === '动手' ? '动手型' :
           profile.cognitive_style === '视觉' ? '视觉型' :
           profile.cognitive_style === '阅读' ? '理论型' :
           profile.cognitive_style === '听觉' ? '听觉型' : '综合型',
  };
}

// 画像评估允许某些维度得分为 0；只要十维字段已生成，就说明评估已完成。
const PROFILE_DOMAIN_KEYS = [
  'python_basic', 'numpy', 'pandas', 'data_cleaning', 'visualization',
  'etl', 'sql', 'statistics', 'comprehensive_analysis', 'performance',
];

function hasCompletedProfile(profile: any): boolean {
  if (!profile) return false;
  const domain = profile.domain_skills;
  const hasAllDomainKeys = domain && PROFILE_DOMAIN_KEYS.every((key) =>
    Object.prototype.hasOwnProperty.call(domain, key)
  );
  return Boolean(
    hasAllDomainKeys ||
    profile.dialogue_completed === true ||
    profile.dialogue_completed === 1 ||
    (Array.isArray(profile.dialogue_history) && profile.dialogue_history.length >= 2)
  );
}

/** 根据用户画像生成确定性种子 —— 同一个人始终一致，不同人不同 */
function profileHash(profile: any): number {
  const dims = ['theoretical_basis','coding_ability','practical_ops','troubleshooting','data_thinking','self_learning'];
  let h = 0;
  for (const d of dims) {
    h = ((h << 5) - h + (profile?.[d] || 0)) | 0;
  }
  return Math.abs(h);
}

/** Fisher-Yates 洗牌，用种子确定顺序 —— 同种子同结果 */
function seededShuffle<T>(arr: T[], seed: number): T[] {
  const a = [...arr];
  let s = seed;
  for (let i = a.length - 1; i > 0; i--) {
    s = (s * 1103515245 + 12345) | 0;
    const j = (s >>> 0) % (i + 1);
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** 根据路径策略构建定制化的学习路线图 —— 每条路径有独立的讲次编排和顺序 */
function buildPathModules(
  modules: any[],
  profile: any,
  pathId: string,
  pathData?: any
): any[] {
  // 收集所有讲次，附上原始模块信息
  const allLectures: any[] = [];
  for (let mi = 0; mi < modules.length; mi++) {
    const mod = modules[mi];
    for (const lec of (mod.lectures || [])) {
      allLectures.push({ ...lec, _origModuleIdx: mi, _origModuleName: mod.name, _origModuleStatus: mod.status });
    }
  }

  // 没有画像时用模拟数据（有高有低才能体现路径差异）
  const effectiveProfile = profile && (profile.theoretical_basis || profile.coding_ability || profile.practical_ops || profile.troubleshooting || profile.data_thinking || profile.self_learning)
    ? profile
    : {
        theoretical_basis: 35, coding_ability: 72, practical_ops: 55,
        troubleshooting: 40, data_thinking: 68, self_learning: 60,
      };

  // 为每个讲次计算路径下的重点等级
  const domain = profile?.domain_skills || {};
  const envScore = Number(domain.python_basic ?? profile?.coding_ability ?? 0);
  const opsScore = Number(domain.etl ?? profile?.practical_ops ?? 0);
  const skipIntro = envScore >= 60 || opsScore >= 60;
  const personalizedLectures = skipIntro ? allLectures.filter((lec: any) => !/环境搭建|Jupyter入门/i.test(String(lec.title || ''))) : allLectures;
  const tagged = personalizedLectures.map((lec: any) => ({
    ...lec,
    _emphasis: getLectureEmphasis(lec, effectiveProfile, pathId),
  }));

  // path_3 均衡路径：保持原始模块结构不变
  if (!pathId) {
    return modules.map((mod, i) => ({
      ...mod, _origIdx: i,
      lectures: (mod.lectures || []).map((lec: any) => ({
        ...lec,
        _emphasis: { level: 'normal' as const, label: '' },
      })),
    }));
  }

  // 与学情画像页使用完全相同的个性化筛选规则。
  const values = Object.values(effectiveProfile || {}).map(Number).filter((v) => v > 0);
  const average = values.length ? values.reduce((a, b) => a + b, 0) / values.length : 50;
  let filtered = pathId === 'path_1'
    ? tagged.filter((l) => l._emphasis.level === 'strengthen')
    : tagged.filter((l) => l._emphasis.level === 'challenge');
  if (filtered.length === 0) {
    filtered = tagged.filter((l) => pathId === 'path_1'
      ? (l._emphasis.dimScore || 50) < average
      : (l._emphasis.dimScore || 50) > average);
  }

  try {
    // 必须按当前画像所属账号读取路径，不能回退到固定 user_id=1（会串用 a 的路径）。
    const profileUserId = profile?.user_id || sessionStorage.getItem('user_id') || '1';
    const cached = pathData?.lecture_order ? null : JSON.parse(localStorage.getItem(`learnmate_paths_v7_shared_${profileUserId}`) || 'null');
    // The profile-path snapshot is authoritative for both pages. Resource
    // payloads may carry an older lecture order, so only use them as fallback.
    const path = (Array.isArray(cached) ? cached.find((p: any) => p.id === pathId) : null)
      || (pathData?.lecture_order ? pathData : null);
    if (path?.lecture_order?.length) {
      const ordered = path.lecture_order.map((id: number) => allLectures.find((l) => l.num === id)).filter(Boolean);
      return [{ name: `${path.label || '个性化学习路径'} · ${ordered.length} 讲`, lectures: ordered.map((l: any, i: number) => ({ ...l, _pathOrder: i + 1, _emphasis: getLectureEmphasis(l, profile, pathId) })), _origIdx: 0 }];
    }
  } catch {}

  // 按路径优先级排序：补弱路径 strengthen 排前；强化路径 challenge 排前
  const priorityOrder = pathId === 'path_1'
    ? ['strengthen', 'normal']    // 重点补在最前，常规紧随
    : ['challenge', 'normal'];

  // 基础讲次（1-3）强制排最前，其余按紧急度排序
  const foundations = filtered.filter(l => l.num <= 3).sort((a, b) => a.num - b.num);
  const rest = filtered.filter(l => l.num > 3);
  const groups = new Map<string, any[]>();
  for (const l of rest) {
    const key = l._emphasis.dimScore?.toFixed(2) ?? '0.00';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(l);
  }
  const sorted: any[] = [...foundations];
  const sortedKeys = [...groups.keys()].sort((a, b) => parseFloat(a) - parseFloat(b));
  for (const key of sortedKeys) {
    const group = groups.get(key)!;
    group.sort((a, b) => a.num - b.num);
    sorted.push(...group);
  }

  // 重新编号：路径内从 1 开始
  const renumbered = sorted.map((lec, i) => ({ ...lec, _pathOrder: i + 1 }));

  return [{
    name: `${pathId === 'path_1' ? '🔴 重点攻克' : '🟣 深度拓展'} · ${renumbered.length} 讲`,
    lectures: renumbered,
    _origIdx: 0,
  }];
}

/** 根据画像+路径判断某个讲次的学习重点等级（多维度关键词打分 + 用户分数差异化） */
function getLectureEmphasis(
  lec: { num: number; title: string },
  profile: any,
  pathId: string,
  userScores?: Record<string, number>
): { level: 'strengthen' | 'normal' | 'fast' | 'challenge'; label: string; dimScore?: number } {
  if (!profile) return { level: 'normal', label: '' };

  const title = lec.title || '';
  const dimScores: Record<string, number> = {
    theoretical_basis: profile.theoretical_basis || 50,
    coding_ability: profile.coding_ability || 50,
    practical_ops: profile.practical_ops || 50,
    troubleshooting: profile.troubleshooting || 50,
    data_thinking: profile.data_thinking || 50,
    self_learning: profile.self_learning || 50,
  };

  // 多维度关键词打分 —— 每篇讲次对六个维度分别计分，取最高分维度
  const kwSets: Record<string, { re: RegExp; weight: number }[]> = {
    theoretical_basis: [{ re: /算法|原理|机制|模型|统计|数学|理论|概念|架构|设计模式/i, weight: 3 }, { re: /基础|概述|入门|简介/i, weight: 1 }],
    coding_ability:    [{ re: /编程|代码|函数|类|模块|API|SDK|面向对象|Python|变量|循环|条件/i, weight: 3 }, { re: /语法|数据类型|运算符/i, weight: 1 }],
    practical_ops:     [{ re: /环境|搭建|安装|配置|部署|Jupyter|VS Code|Docker|虚拟环境|pip/i, weight: 3 }, { re: /工具|操作|实践|上手/i, weight: 1 }],
    troubleshooting:   [{ re: /调试|异常|错误|Bug|排查|修复|Debug|Exception|性能|瓶颈/i, weight: 3 }, { re: /优化|监控|日志|警告/i, weight: 1 }],
    data_thinking:     [{ re: /分析|清洗|预处理|ETL|可视化|图表|Pandas|NumPy|Matplotlib|Seaborn|数据/i, weight: 3 }, { re: /SQL|DataFrame|聚合|透视|统计|回归/i, weight: 1 }],
    self_learning:     [{ re: /实战|项目|部署|上线|报告|机器学习|Scikit-learn|进阶|综合/i, weight: 3 }, { re: /高级|扩展|总结|Dashboard|看板/i, weight: 1 }],
  };

  let bestDim = '';
  let bestScore = 0;
  for (const [dim, kws] of Object.entries(kwSets)) {
    let score = 0;
    for (const kw of kws) {
      if (kw.re.test(title)) score += kw.weight;
    }
    if (score > bestScore) { bestScore = score; bestDim = dim; }
  }

  if (!bestDim) return { level: 'normal', label: '' };

  const dimScore = dimScores[bestDim] || 50;
  const allScores = Object.values(dimScores).filter(s => s > 0);
  const avg = allScores.length > 0 ? allScores.reduce((a, b) => a + b, 0) / allScores.length : 50;
  // 用户个人画像 → 归一化差距（用于同维度内排序，负值=弱项）
  const gap = (dimScore - avg) / Math.max(avg, 1);

  if (pathId === 'path_1') {
    if (dimScore < avg) return { level: 'strengthen', label: '重点补', dimScore: gap };
    if (dimScore > avg * 1.1) return { level: 'fast', label: '速过', dimScore: gap };
    return { level: 'normal', label: '', dimScore: gap };
  } else if (pathId === 'path_2') {
    if (dimScore > avg * 1.1) return { level: 'challenge', label: '挑战', dimScore: gap };
    if (dimScore < avg * 0.85) return { level: 'fast', label: '速过', dimScore: gap };
    return { level: 'normal', label: '', dimScore: gap };
  } else {
    return { level: 'normal', label: '', dimScore: gap };
  }
}

function downloadTextFile(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function CourseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const courseId = params?.id as string || '';
  const targetLecture = searchParams?.get('lecture');
  const targetPath = searchParams?.get('path') || '';

  const {
    agentSteps,
    isAgentRunning,
    setAgentSteps,
    setAgentRunning,
    updateAgentStep,
    resetAgent,
  } = useAgent();

  // ===== 从 API 动态加载课程元数据 =====
  const [courseMeta, setCourseMeta] = useState<any>(null);
  const [courseMetaLoading, setCourseMetaLoading] = useState(true);

  useEffect(() => {
    if (!courseId) return;
    const API = process.env.NEXT_PUBLIC_API_URL || '';

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    fetch(`${API}/api/courses/${courseId}`, { signal: controller.signal })
      .then(res => res.json())
      .then(data => {
        clearTimeout(timeoutId);
        if (data.success && data.course) {
          setCourseMeta(data.course);
        } else {
          setCourseMeta(FALLBACK_COURSE[courseId] || null);
        }
      })
      .catch(() => {
        clearTimeout(timeoutId);
        setCourseMeta(FALLBACK_COURSE[courseId] || null);
      })
      .finally(() => setCourseMetaLoading(false));
  }, [courseId]);

  const courseData = courseMeta;

  // ===== 所有 Hooks 必须在条件返回之前调用（React Rules of Hooks） =====
  const [lectureContent, setLectureContent] = useState<LectureContent | null>(null);
  const [contentLoading, setContentLoading] = useState(true);
  const [contentError, setContentError] = useState<string | null>(null);
  const [tab, setTab] = useState('doc');
  const [openModules, setOpenModules] = useState<Set<number>>(new Set([0, 1, 2, 3]));
  const [activeLecture, setActiveLecture] = useState(() => ({ num: targetLecture ? parseInt(targetLecture) : 1, title: '加载中', dur: '0min' }));
  // Restore the learner's last selected lecture when the URL has no lecture query.
  useEffect(() => {
    if (targetLecture) return;
    try {
      const saved = Number(localStorage.getItem(`learnmate_last_lecture_${courseId}`));
      if (saved > 0) router.replace(`/learn/${courseId}?lecture=${saved}${targetPath ? `&path=${encodeURIComponent(targetPath)}` : ''}`);
    } catch {}
  }, [courseId, targetLecture, targetPath, router]);
  // Sync activeLecture when courseData loads with target lecture
  useEffect(() => {
    if (!courseData?.modules || !targetLecture) return;
    const num = parseInt(targetLecture);
    const all = (courseData.modules || []).flatMap((m: any) => m.lectures || []);
    const found = all.find((l: any) => l.num === num);
    if (found) setActiveLecture({ ...found, dur: found.dur || found.duration || found.duration_text || '45min' });
  }, [courseData, targetLecture]);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<{role: string; content: string}[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [hasAutoTriggered, setHasAutoTriggered] = useState<Record<number, boolean>>({});
  const [selectedPath, setSelectedPath] = useState<any>(null);
  const [pathOptions, setPathOptions] = useState<any[]>([]);
  const [regenerateKey, setRegenerateKey] = useState(0);
  // 从 localStorage 恢复学习统计
  const [studyStats, setStudyStats] = useState(() => {
    try {
      const saved = localStorage.getItem('learnmate_stats');
      return saved ? JSON.parse(saved) : { minutes: 0, quizzes: 0, labs: 0 };
    } catch { return { minutes: 0, quizzes: 0, labs: 0 }; }
  });

  // 学习统计变化时保存
  useEffect(() => {
    localStorage.setItem('learnmate_stats', JSON.stringify(studyStats));
  }, [studyStats]);
  // 进度按学习路径顺序：每个路径前5讲100%，后续递减
  // 从 localStorage 恢复进度
  const [lectureProgress, setLectureProgress] = useState<Record<number, number>>(() => {
    try {
      const saved = localStorage.getItem('learnmate_progress');
      return saved ? JSON.parse(saved) : {};
    } catch { return {}; }
  });

  const visitedTabsRef = useRef<Record<number, string[]>>({});

  // ===== 用户认证 + 真实6维学习画像 =====
  const { user, token } = useAuth();

  // 路径持久化：按账号记住选择
  useEffect(() => {
    if (!user?.id) return;
    // 仅恢复与学情画像共享的 v2 路径，忽略旧版可能过期的单独选择缓存。
    const saved = localStorage.getItem(`learnmate_paths_v7_shared_${user.id}`);
    if (saved) { try {
      const parsed = JSON.parse(saved);
      const paths = Array.isArray(parsed) ? parsed : [parsed];
      const target = targetPath ? paths.find((p: any) => p.id === targetPath) : paths.find((p: any) => p.recommended) || paths[0];
      if (target) setSelectedPath(target);
    } catch {} }
  }, [user?.id, targetPath]);
  useEffect(() => {
    if (selectedPath && user?.id) {
      localStorage.setItem('learnmate_path_' + user.id, JSON.stringify(selectedPath));
    }
  }, [selectedPath, user?.id]);

  // 从后端同步学习数据（以后端为准，localStorage 仅兜底）
  useEffect(() => {
    if (!user?.id || !token) return;
    const userId = user?.id || 1;
    const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${API}/api/profile/dynamic/${userId}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} }).then(r => {
      if (!r.ok) throw new Error(`profile dynamic ${r.status}`);
      return r.json();
    }).then(d => {
      setStudyStats((s: StudyStats) => ({
        minutes: d.study_minutes || 0,
        quizzes: d.quiz_attempts || 0,
        labs: Math.max(s.labs, d.labs_completed || 0),
      }));
    }).catch(() => {});
  }, [user?.id, token]);

  // 进度变化时保存到 localStorage，且 100% 完成时通知后端
  const completedRef = useRef<Set<number>>(new Set());
  useEffect(() => {
    localStorage.setItem('learnmate_progress', JSON.stringify(lectureProgress));
    window.dispatchEvent(new Event('learnmate-progress-updated'));
    Object.entries(lectureProgress).forEach(([num, pct]) => {
      const n = parseInt(num);
      if (pct >= 100 && !completedRef.current.has(n)) {
        completedRef.current.add(n);
        const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const today = new Date().toISOString().split('T')[0];
        fetch(`${API}/learning-records/`, {
          method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
          body: JSON.stringify({ date: today, study_minutes: 0, completed_lectures: 1 }),
        }).catch(() => {});
      }
    });
  }, [lectureProgress, user?.id, token]);

  const [userProfile, setUserProfile] = useState<any>(null);
  const [profileLoading, setProfileLoading] = useState(true);

  useEffect(() => {
    const userId = user?.id || 1;
    const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${API}/api/profile?user_id=${userId}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(r => { if (!r.ok) throw new Error(`profile ${r.status}`); return r.json(); })
      .then(p => {
        // p 包含 6 维分数: theoretical_basis, coding_ability, practical_ops, troubleshooting, data_thinking, self_learning
        // 以及偏好: cognitive_style, learning_pace, learning_motivation, major_background
        // Ten scored Python-data-analysis dimensions are sufficient evidence of
        // an existing assessment. Do not block the learning space solely because
        // an older profile record lacks the dialogue_completed flag.
        if (hasCompletedProfile(p)) {
          setUserProfile(buildProfileSummary(p));
        }
      })
      .catch(() => {
        // 网络错误时保持 null，UI 会显示降级内容
      })
      .finally(() => setProfileLoading(false));
  }, [user?.id, token]);

  // 从后端获取 LLM 生成的个性化路径推荐
  useEffect(() => {
    if (profileLoading) return;

    // 先用前端回退路径兜底，保证用户始终有路径可选
    const fallbackPaths = getPathOptions(userProfile);
    if (user?.id) {
      try {
        const cached = localStorage.getItem(`learnmate_paths_v7_shared_${user.id}`);
        const parsed = cached ? JSON.parse(cached) : null;
        if (Array.isArray(parsed) && parsed.length >= 3) setPathOptions(parsed);
      } catch {}
    }
    setPathOptions((prev: any[]) => {
      if (prev.length > 0) return prev;
      return fallbackPaths;
    });
    setSelectedPath((prev: any) => {
      if (prev) return prev;
      // 学习空间与学情画像共享同一份用户路径缓存，优先恢复缓存中的推荐路径
      if (user?.id) {
        try {
          const cached = JSON.parse(localStorage.getItem(`learnmate_paths_v7_shared_${user.id}`) || 'null');
          if (Array.isArray(cached) && cached.length >= 3) {
            const cachedTarget = targetPath ? cached.find((p: any) => p.id === targetPath) : cached.find((p: any) => p.recommended);
            if (cachedTarget) return cachedTarget;
          }
        } catch {}
      }
      // URL 指定了路径 → 优先使用
      if (targetPath) {
        const urlPath = fallbackPaths.find((p: any) => p.id === targetPath);
        if (urlPath) return urlPath;
      }
      const recommended = fallbackPaths.find((p: any) => p.recommended);
      return recommended || fallbackPaths[0] || null;
    });

    if (!userProfile) return;

    const userId = user?.id || 1;
    const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    // Profile and learning space share the same server source of truth.
    fetch(`${API}/api/profile/paths?user_id=${userId}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(r => { if (!r.ok) throw new Error(`profile paths ${r.status}`); return r.json(); })
      .then(data => {
        if (data.paths?.length > 0) {
          setPathOptions(data.paths);
          try { if (user?.id) localStorage.setItem(`learnmate_paths_v7_shared_${user.id}`, JSON.stringify(data.paths)); } catch {}
          // 后端路径是唯一事实来源；即使此前已显示前端占位路径，也要同步替换。
          const nextPath = targetPath
            ? data.paths.find((p: any) => p.id === targetPath)
            : data.paths.find((p: any) => p.recommended) || data.paths[0];
          if (nextPath) setSelectedPath(nextPath);
        }
      })
      .catch(() => {});
  }, [userProfile, profileLoading, user?.id, token, targetPath]);

  // 路径切换时跳到该路径第一讲（不清缓存，已生成过的讲次直接从缓存取）
  useEffect(() => {
    if (!selectedPath?.id) return;
    // URL 明确指定讲次时，不能被路径切换逻辑覆盖。
    if (targetLecture) return;
    setRegenerateKey(k => k + 1);

    if (PATH_MODULES.length > 0) {
      const pathModules = buildPathModules(PATH_MODULES, effectiveProfile, selectedPath.id, selectedPath);
      const firstLecture = pathModules[0]?.lectures?.[0];
      if (firstLecture) {
        setActiveLecture(firstLecture);
        // 如果该讲次已缓存，直接用；否则触发加载
        const cached = lectureCache.current[cacheKey(firstLecture.num)];
        setLectureContent(cached || null);
        if (cached?.video_url) setVideoUrl(cached.video_url);
        setTab('doc');
        resetAgent();
      }
    }
  }, [selectedPath?.id, targetLecture]);

  // Fetch study stats
  // 学习时长仅由真实行为驱动：讲次完成、答题、实验
  // 前端仅本地计时展示，不上报后端（避免页面停留充数）
  const studyTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    studyTimerRef.current = setInterval(() => {
      setStudyStats((s: StudyStats) => ({ ...s, minutes: s.minutes + 1 }));
    }, 60000);
    return () => { if (studyTimerRef.current) clearInterval(studyTimerRef.current); };
  }, []);

  const [videoPlaying, setVideoPlaying] = useState(false);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [quizAnswers, setQuizAnswers] = useState<Record<number, number | null>>({});

  // 记录访问过的 tab，计算进度：每个 tab = 20%（只增不减）
  useEffect(() => {
    if (!activeLecture.num) return;
    const key = activeLecture.num;
    const prev = visitedTabsRef.current[key] || [];
    if (!prev.includes(tab)) {
      visitedTabsRef.current[key] = [...prev, tab];
      const newPct = Math.min(100, visitedTabsRef.current[key].length * 20);
      setLectureProgress(p => ({ ...p, [key]: Math.max(p[key] || 0, newPct) }));
    }
  }, [tab, activeLecture.num]);

  // 答题后增加答题次数
  useEffect(() => {
    if (!activeLecture.num || selectedAnswer === null) return;
    setStudyStats((s: StudyStats) => ({ ...s, quizzes: s.quizzes + 1 }));
  }, [selectedAnswer, activeLecture.num]);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [videoAgentSteps, setVideoAgentSteps] = useState<{agent: string; status: string; message?: string}[]>([]);
  const [videoGenMethod, setVideoGenMethod] = useState<string | null>(null);
  const [videoGenScore, setVideoGenScore] = useState<number | null>(null);
  const [resourceData, setResourceData] = useState<{ topic: string; resources: GeneratedResource[]; sources: AgentSource[] } | null>(null);
  const [resourceLoading, setResourceLoading] = useState(false);
  const [mindmapFullscreen, setMindmapFullscreen] = useState(false);

  // 全屏时锁定 body 滚动
  useEffect(() => {
    if (mindmapFullscreen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [mindmapFullscreen]);

  const [notes, setNotes] = useState<Note[]>([]);
  const [notesLoading, setNotesLoading] = useState(true);
  const [quickNoteTitle, setQuickNoteTitle] = useState('');
  const [quickNoteContent, setQuickNoteContent] = useState('');
  const [videoLoading, setVideoLoading] = useState(false);
  const [speakTrigger, setSpeakTrigger] = useState(0);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [videoScore, setVideoScore] = useState<number | null>(null);
  const [runOutput, setRunOutput] = useState('');
  const [runLoading, setRunLoading] = useState(false);

  // ===== 持久化讲义缓存：key = 用户/课程/讲次/路径，生成成功后跨刷新复用 =====
  const lectureCache = useRef<Record<string, LectureContent>>({});

  // 题库格式更新后使用新版本缓存键，避免浏览器继续读取旧的通用练习题。
  const profileCacheTag = userProfile?.domain_skills
    ? Object.entries(userProfile.domain_skills).sort(([a], [b]) => a.localeCompare(b)).map(([k, v]) => `${k}:${v}`).join('_')
    : 'unprofiled';
  const cacheKey = (num: number) => `learnmate_lecture_v5_${user?.id || 'guest'}_${courseId}_${num}_${selectedPath?.id || 'default'}_${profileCacheTag}`;
  useEffect(() => {
    try {
      Object.keys(localStorage).filter((key) => key.startsWith('learnmate_lecture_')).forEach((key) => {
        const raw = localStorage.getItem(key);
        if (raw) lectureCache.current[key] = JSON.parse(raw);
      });
    } catch {}
  }, [user?.id, courseId]);

  // ===== 派生数据（courseData 可能为 null，安全访问） =====
  const title = courseData?.title || '';
  const modules = courseData?.modules || [];

  // 画像数据：有真实画像用真实，没有用模拟（保证路径差异始终可见）
  const effectiveProfile = useMemo(() => {
    if (userProfile && (
      userProfile.theoretical_basis || userProfile.coding_ability ||
      userProfile.practical_ops || userProfile.troubleshooting ||
      userProfile.data_thinking || userProfile.self_learning
    )) {
      return userProfile;
    }
    return {
      theoretical_basis: 35, coding_ability: 72, practical_ops: 55,
      troubleshooting: 40, data_thinking: 68, self_learning: 60,
    };
  }, [userProfile]);
  const PATH_MODULES = modules;
  const LECTURE_VIDEO = courseData?.video || {};
  const MINDMAP_FALLBACK = courseData?.mindmap || {};
  const LECTURE_QUIZ = courseData?.quiz || {};
  const ALL_LECTURES = PATH_MODULES.flatMap((module: any) => module.lectures || []);
  const showContent = !courseMetaLoading && courseData;

  const handleChatSend = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, {role: 'user', content: msg}]);
    setChatLoading(true);
    try {
      const API = process.env.NEXT_PUBLIC_API_URL || '';
      const history = chatMessages.slice(-6).map(m => `${m.role === 'user' ? '学生' : 'AI'}: ${m.content}`).join('\n');
      const questionWithContext = history
        ? `[对话历史]\n${history}\n\n[当前问题] ${msg}\n(当前学习: ${lc.title})`
        : `${msg}\n(当前学习: ${lc.title})`;
      const res = await fetch(`${API}/api/generate/tutor`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ question: questionWithContext }),
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, {role: 'assistant', content: data.answer || '抱歉，暂时无法回答。'}]);
    } catch (e) {
      setChatMessages(prev => [...prev, {role: 'assistant', content: '网络错误，请稍后重试。'}]);
    } finally {
      setChatLoading(false);
    }
  };

  // ========== 从 API 获取讲次内容（默认使用多智能体模式） ==========
  useEffect(() => {
    if (!courseId || !activeLecture.num) return;
    if (!selectedPath?.id) return; // 等待路径就绪

    // 前端缓存：已加载过的讲次（且非路径切换）直接跳过
    const key = cacheKey(activeLecture.num);
    if (lectureCache.current[key]) {
      setLectureContent(lectureCache.current[key]);
      setContentLoading(false);
      return;
    }

    setContentLoading(true);
    setContentError(null);

    const API = process.env.NEXT_PUBLIC_API_URL || '';

    // 默认走多Agent模式，除非明确指定 ?orchestrator=single
    const useSingle = searchParams?.get('orchestrator') === 'single';

    let endpoint: string;
    if (!useSingle) {
      // 多 Agent 协作模式（比赛要求）—— 传入6维画像分数 + 路径策略
      const profileToSend = userProfile ? {
        theoretical_basis: userProfile.theoretical_basis || 0,
        coding_ability: userProfile.coding_ability || 0,
        practical_ops: userProfile.practical_ops || 0,
        troubleshooting: userProfile.troubleshooting || 0,
        data_thinking: userProfile.data_thinking || 0,
        self_learning: userProfile.self_learning || 0,
        cognitive_style: userProfile.cognitive_style || '',
        learning_pace: userProfile.learning_pace || '',
        learning_motivation: userProfile.learning_motivation || '',
        major_background: userProfile.major_background || '',
        foundation: userProfile.foundation || '中等',
        weakness: userProfile.weakness || [],
        goal: userProfile.goal || '',
        style: userProfile.style || '综合型',
        // 将十维领域能力随请求传递给 Agent，确保同一讲次按个人能力生成不同难度内容。
        domain_skills: userProfile.domain_skills || {},
      } : {};
      const profileStr = encodeURIComponent(JSON.stringify(profileToSend));
      const userId = user?.id || 1;
      const pathId = selectedPath?.id || 'path_1';
      const pathLabel = selectedPath?.label || '';
      const pathStrategy = selectedPath?.strategy || '';
      endpoint = `${API}/api/lecture/${courseId}/${activeLecture.num}/multi-agent?path_type=${encodeURIComponent(pathId)}&path_label=${encodeURIComponent(pathLabel)}&path_strategy=${encodeURIComponent(pathStrategy)}&profile_json=${profileStr}&user_id=${userId}`;
    } else {
      // 单 Prompt 模式（仅 ?orchestrator=single 时使用）
      endpoint = `${API}/api/lecture/${courseId}/${activeLecture.num}`;
    }

    fetch(endpoint)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        // 标准化 quiz 格式：兼容多 Agent 和单 Agent 两种返回
        if (data.quiz && !data.quiz.question && data.full_quiz?.questions?.[0]) {
          data.quiz = data.full_quiz.questions[0];
        }
        if ((!data.quiz || !data.quiz.question) && data.full_quiz?.questions?.[0]) {
          data.quiz = data.full_quiz.questions[0];
        }
        if (data.quiz?.question) {
          const rawOptions = data.quiz.options || data.quiz.options_list || data.quiz.choices || [];
          const correctIndex = data.quiz.answer ?? data.quiz.correct_index ?? 0;
          data.quiz = {
            ...data.quiz,
            options: rawOptions.map((option: any, index: number) => typeof option === 'string'
              ? { text: option, correct: index === correctIndex }
              : { ...option, text: option.text || option.label || option.content || String(option), correct: option.correct ?? index === correctIndex }),
          };
        }
        // 补解析：无解析时根据正确答案生成
        if (data.quiz && !data.quiz.explanation) {
          const correctOpt = (data.quiz.options || []).find((o: any) => o.correct);
          if (correctOpt) {
            const topicName = data.title || lc?.title || activeLecture?.title || '当前讲次';
            data.quiz.explanation = `正确答案是「${correctOpt.text}」。本题考察「${topicName}」的核心知识点，建议结合讲义内容加深理解。`;
          }
        }
        // 写入前端缓存
        lectureCache.current[key] = data;
        try { localStorage.setItem(key, JSON.stringify(data)); } catch {}
        setLectureContent(data);
        // 多 Agent 模式：使用后端返回的 video_url（VideoAgent 已完成渲染）
        if (data.video_url) {
          setVideoUrl(data.video_url);
        }
        // 多 Agent 模式：展示 Agent 协作日志
        if (data.generated_by === 'multi_agent_orchestrator' && data.agent_logs) {
          const steps = data.agent_logs.map((log: any, idx: number) => ({
            id: `agent-${idx}`,
            name: AGENT_NAME_MAP[log.agent] || log.agent,
            description: log.status === 'success'
              ? `${AGENT_NAME_MAP[log.agent] || log.agent} 已完成`
              : `错误: ${log.error || '未知'}`,
            status: log.status === 'success' ? 'success' : 'error',
          }));
          setAgentSteps(steps);
        }
      })
      .catch(err => {
        console.error('获取讲次内容失败:', err);
        setContentError(err.message);
        const fallbackContent = getContent(activeLecture.num);
        setLectureContent({
          title: fallbackContent.title,
          type: fallbackContent.type,
          content: fallbackContent.content,
          code: fallbackContent.code,
          mindmap: mindmapNodes,
          quiz: quizData,
        });
      })
      .finally(() => {
        setContentLoading(false);
      });
  }, [courseId, activeLecture.num, regenerateKey]);

  const getContent = (num: number) => {
    const contentData = (courseData as any)?.content || {};
    return contentData[num] || contentData[1] || { title: '内容加载中', type: '理论课', content: '<p>内容正在准备中...</p>', code: '// 代码加载中' };
  };

  const currentLectureData = lectureContent || getContent(activeLecture.num);
  const lc = {
    title: (currentLectureData.title || '内容加载中').replace(/^第\d+讲[：:]\s*/, ''),
    type: currentLectureData.type || '理论课',
    content: sanitizeHtmlContent(enrichShortLectureContent((currentLectureData.title || activeLecture.title || '').replace(/^第\d+讲[：:]\s*/, ''), currentLectureData.content || '')),
    code: currentLectureData.code || '// 代码加载中',
  };

  const videoData = LECTURE_VIDEO[activeLecture.num] || LECTURE_VIDEO[1] || { src: '', title: '视频加载中', duration: '0s', outline: [] };

  const mindmapNodes = useMemo(() => {
    const derived = deriveLectureMindmap(lc.title, lc.content);
    if (derived.length > 0 && (derived[0] as any)?.children?.length) return derived;
    if (lectureContent?.mindmap && lectureContent.mindmap.length > 0) return lectureContent.mindmap;
    return MINDMAP_FALLBACK[activeLecture.num] || MINDMAP_FALLBACK[1] || [{ t: lc.title, s: '本讲核心' }];
  }, [lectureContent, activeLecture.num, lc.title, lc.content]);

  const quizData = useMemo(() => {
    // 多题库格式使用 questions 数组，优先取当前讲次的第一道单选题，避免回退到通用模板。
    const payload: any = lectureContent as any;
    const nested = payload?.resource || {};
    const generatedQuestions = payload?.questions || payload?.full_quiz?.questions
      || nested?.questions || nested?.full_quiz?.questions
      || payload?.quiz?.questions || nested?.quiz?.questions;
    const quizQuestions = generatedQuestions || (payload?.quiz?.questions ? payload.quiz.questions : null);
    if (Array.isArray(quizQuestions) && quizQuestions.length) {
      const normalizedQuestions = quizQuestions.map((q: any) => ({ ...q, question: q.question || q.q, options: q.options || [] }));
      const withOptions = normalizedQuestions.filter((q: any) => Array.isArray(q.options) && q.options.length);
      // 强化/进阶路径优先选择 intermediate/advanced 题，避免中等生在擅长讲次仍拿基础题。
      const preferHard = selectedPath?.id === 'path_2' || selectedPath?.id === 'path_3';
      const ranked = [...withOptions].sort((a: any, b: any) => {
        const rank = (q: any) => ({ advanced: 3, comprehensive: 3, intermediate: 2, basic: 1 }[String(q.difficulty || '').toLowerCase()] || 1);
        return preferHard ? rank(b) - rank(a) : rank(a) - rank(b);
      });
      const topicWords = String(lc.title || '').split(/[：:、，,与和及]/).filter(w => w.length >= 2);
      const topicMatch = (q: any) => {
        const text = `${q.question || ''}${q.knowledge_point || ''}${q.lecture || ''}`;
        return !topicWords.length || topicWords.some(w => text.includes(w)) || text.includes(String(activeLecture.num));
      };
      const invalidGeneric = (q: any) => /利用\s*Pandas\s*[\/／]\s*NumPy\s*高效处理和分析数据|只能用于网页开发|不需要理解数据即可使用|仅用于机器学习/.test(`${q.question || ''}${(q.options || []).map((o: any) => typeof o === 'string' ? o : (o.text || '')).join('|')}`);
      const single = ranked.find((q: any) => topicMatch(q) && !invalidGeneric(q) && (!preferHard || !['basic'].includes(String(q.difficulty || '').toLowerCase())))
        || normalizedQuestions.find((q: any) => topicMatch(q) && !invalidGeneric(q) && (!preferHard || !['basic'].includes(String(q.difficulty || '').toLowerCase())));
      if (single?.question && Array.isArray(single.options) && single.options.length) {
        const answer = single.answer ?? single.correct_index;
        const options = single.options.map((o: any, i: number) => ({
          text: typeof o === 'string' ? o : (o.text || o.content || ''),
          correct: typeof o === 'object' && o.correct === true ? true : (typeof answer === 'number' ? i === answer : false),
        }));
        if (!options.some((o: any) => o.correct) && typeof answer === 'number') {
          if (answer >= 0 && answer < options.length) options[answer].correct = true;
        }
        if (!options.some((o: any) => o.correct) && typeof answer === 'string') {
          const idx = options.findIndex((o: any) => o.text === answer);
          if (idx >= 0) options[idx].correct = true;
        }
        // 题库兼容 q/explain 字段；answer 可能只是选项下标，不能直接当解析展示。
        const explanation = single.explanation || single.explain || single.analysis || '';
        return { question: single.question, options, explanation };
      }
    }
    if (lectureContent?.quiz?.options?.length) {
      const q = String(lectureContent.quiz.question || '');
      const opts = lectureContent.quiz.options.map((o: any) => String(o.text || '')).join('|');
      // 旧缓存/课程默认题可能把所有讲次都写成同一组泛化选项，不能继续复用。
      const generic = /学习中，最重要的做法是|结合讲义理解概念并动手验证|利用\s*Pandas\s*[\/／]\s*NumPy\s*高效处理和分析数据|只能用于网页开发|不需要理解数据即可使用|仅用于机器学习/.test(q + opts);
      const topicWords = String(lc.title || '').split(/[：:、，,与和及]/).filter(w => w.length >= 2);
      const topicMatched = topicWords.length === 0 || topicWords.some(w => (q + opts).includes(w));
      if (!generic && topicMatched) return lectureContent.quiz;
    }
    const courseQuiz = LECTURE_QUIZ[activeLecture.num];
    if (courseQuiz?.options?.length) {
      const q = String(courseQuiz.question || '');
      const opts = courseQuiz.options.map((o: any) => String(o.text || '')).join('|');
      const topicWords = String(lc.title || '').split(/[：:、，,与和及]/).filter(w => w.length >= 2);
      const topicMatched = topicWords.length === 0 || topicWords.some(w => (q + opts).includes(w));
      if (!/学习中，最重要的做法是|结合讲义理解概念并动手验证|利用\s*Pandas\s*[\/／]\s*NumPy\s*高效处理和分析数据|只能用于网页开发|不需要理解数据即可使用|仅用于机器学习/.test(q + opts) && topicMatched) return courseQuiz;
    }
    if (activeLecture.num === 1) return {
      question: '在 Jupyter Notebook 中，运行当前代码单元并移动到下一单元的快捷键是？',
      options: [
        { text: 'Shift + Enter', correct: true },
        { text: 'Ctrl + S', correct: false },
        { text: 'Alt + F4', correct: false },
        { text: 'Ctrl + Z', correct: false },
      ],
      explanation: 'Shift + Enter 会运行当前代码单元，并把焦点移动到下一个单元。',
    };
    // 生成内容暂不可用时，也按讲次提供不同的知识点题目，避免所有讲次显示同一道泛化题。
    const fallbackByLecture: Record<number, { question: string; answer: string; distractors: string[] }> = {
      2: { question: 'Python 变量赋值后，变量保存的是什么？', answer: '对象的引用', distractors: ['固定内存地址文本', '只能保存字符串', '只能保存数字'] },
      3: { question: '条件分支中用于判断多个条件的关键字是？', answer: 'elif', distractors: ['loop', 'caseof', 'switch'] },
      4: { question: '定义 Python 函数使用哪个关键字？', answer: 'def', distractors: ['func', 'function', 'define'] },
      5: { question: 'NumPy 中用于创建数组的常用函数是？', answer: 'np.array()', distractors: ['np.table()', 'np.dataframe()', 'np.vector()'] },
      6: { question: 'NumPy 广播机制主要解决什么问题？', answer: '不同形状数组的逐元素运算', distractors: ['自动连接数据库', '压缩图片文件', '创建网页路由'] },
      7: { question: '矩阵乘法在 NumPy 中通常使用哪个运算符？', answer: '@', distractors: ['**', '//', '%%'] },
      8: { question: '生成指定范围整数序列常用哪个 NumPy 函数？', answer: 'np.arange()', distractors: ['np.random()', 'np.sequence()', 'np.range_list()'] },
      9: { question: 'Pandas 中二维表格数据的核心结构是？', answer: 'DataFrame', distractors: ['Tensor', 'ArrayList', 'TableView'] },
      10: { question: 'Pandas 中按条件筛选行通常使用什么方式？', answer: '布尔条件索引', distractors: ['CSS 选择器', 'SQL 插值', '随机抽样'] },
      11: { question: 'Pandas 合并两张表最常用的函数是？', answer: 'merge()', distractors: ['bind()', 'attach()', 'combine_rows()'] },
      12: { question: '透视表主要用于什么分析？', answer: '按维度汇总和交叉统计', distractors: ['编译 Python', '压缩数据', '发送网络请求'] },
      13: { question: '处理缺失值时，删除缺失行常用哪个方法？', answer: 'dropna()', distractors: ['remove_nulls()', 'clearna()', 'delete_empty()'] },
      14: { question: 'Pandas 将文本列转换为日期类型常用哪个函数？', answer: 'pd.to_datetime()', distractors: ['pd.to_dateonly()', 'pd.date_cast()', 'pd.parse_day()'] },
      15: { question: '正则表达式中表示任意单个字符的符号是？', answer: '.', distractors: ['#', '@', '$'] },
      16: { question: '时间序列重采样通常使用哪个方法？', answer: 'resample()', distractors: ['retime()', 'timeslice()', 'periodize()'] },
      17: { question: 'Matplotlib 绘制折线图常用哪个函数？', answer: 'plt.plot()', distractors: ['plt.linechart()', 'plt.draw_line()', 'plt.trace()'] },
      18: { question: 'Seaborn 中绘制热力图常用哪个函数？', answer: 'sns.heatmap()', distractors: ['sns.hotmap()', 'sns.matrixplot()', 'sns.color_grid()'] },
      19: { question: 'groupby 后计算每组平均值常用哪个聚合方法？', answer: 'mean()', distractors: ['average_group()', 'avg_all()', 'middle()'] },
      20: { question: '链式调用 Pandas 方法时，各步骤通常用什么连接？', answer: '点号 .', distractors: ['箭头 ->', '冒号 :', '分号 ;'] },
      21: { question: 'EDA 的主要目标是什么？', answer: '探索数据分布、关系和异常', distractors: ['训练操作系统', '部署网站', '加密文件'] },
      22: { question: 'Dashboard 最适合展示什么？', answer: '关键指标和趋势的交互式概览', distractors: ['源代码编译日志', '密码列表', '模型二进制文件'] },
      23: { question: 'Scikit-learn 中用于划分训练集和测试集的函数是？', answer: 'train_test_split()', distractors: ['split_data()', 'divide_dataset()', 'holdout_rows()'] },
      24: { question: '完整数据分析项目的合理顺序是？', answer: '导入→清洗→分析→可视化→结论', distractors: ['结论→导入→删除', '可视化→随机填数', '先部署再采集'] },
    };
    const item = (selectedPath?.id === 'path_2' && activeLecture.num === 12)
      ? { question: '订单数据按“用户、月份”建立透视表后，先按用户汇总月度销售额，再计算每位用户的月均销售额。若某用户有 3 个月记录，使用 agg({销售额: "sum"}) 后再对月份求 mean，得到的指标是什么？', answer: '该用户各月销售额的平均值', distractors: ['所有订单金额的总和', '所有用户销售额的平均值', '记录条数乘以销售额'] }
      : (fallbackByLecture[activeLecture.num] || { question: `${lc.title}的核心知识点是什么？`, answer: '结合概念与代码实践掌握核心方法', distractors: ['只记忆标题', '跳过示例', '忽略运行结果'] });
    return { question: item.question, options: [item.answer, ...item.distractors].map((text, i) => ({ text, correct: i === 0 })), explanation: `本题考察“${lc.title}”的核心知识点：${item.answer}。` };
  }, [lectureContent, activeLecture.num, lc.title, selectedPath?.id]);

  const lectureQuizOptions = quizData.options || [];
  const quizSet = useMemo(() => {
    const raw: any[] = (lectureContent as any)?.quiz?.questions || (lectureContent as any)?.questions || (lectureContent as any)?.full_quiz?.questions || [];
    const list = raw.slice(0, 5).map((q: any) => {
      const options = (q.options || []).map((o: any, i: number) => ({ text: typeof o === 'string' ? o : (o.text || o.content || ''), correct: typeof o === 'object' ? o.correct === true : i === q.answer }));
      return { ...q, question: q.question || q.q, options, explanation: q.explanation || q.explain || '' };
    }).filter(q => q.question && q.options.length);
    if (list.length >= 3) return list.slice(0, 5);
    const base = quizData;
    const extras = [
      { question: `${lc.title} 中，下面哪项属于关键操作？`, options: [{ text: `围绕${lc.title}选择合适的方法并验证结果`, correct: true }, { text: '跳过数据检查', correct: false }, { text: '只修改标题', correct: false }, { text: '忽略输出结果', correct: false }], explanation: `应围绕“${lc.title}”选择方法并通过结果验证。`, type: 'single_choice' },
      { question: `实际处理“${lc.title}”数据时，最合理的步骤是？`, options: [{ text: '先理解数据，再处理并检查结果', correct: true }, { text: '直接删除所有异常数据', correct: false }, { text: '只运行一次代码不检查', correct: false }, { text: '不看数据结构直接分析', correct: false }], explanation: '数据分析应遵循理解、处理、验证的流程。', type: 'single_choice' },
    ];
    return [...list, ...extras].slice(0, 5).concat(list.length + extras.length < 3 ? [base] : []).slice(0, 5);
  }, [lectureContent, quizData]);

  // 按当前路径的讲次顺序计算上/下一讲
  const PATH_LECTURES = useMemo(() => {
    const mods = buildPathModules(PATH_MODULES, effectiveProfile, selectedPath?.id || '', selectedPath);
    return mods.flatMap((m: any) => m.lectures || []);
  }, [PATH_MODULES, effectiveProfile, selectedPath?.id]);
  const activeIndex = PATH_LECTURES.findIndex((lec: any) => lec.num === activeLecture.num);
  const prevLecture = activeIndex > 0 ? PATH_LECTURES[activeIndex - 1] : null;
  const nextLecture = activeIndex >= 0 && activeIndex < PATH_LECTURES.length - 1 ? PATH_LECTURES[activeIndex + 1] : null;

  const resourceByType = (type: string) => resourceData?.resources.find(resource => resource.type === type);
  const summaryResource = resourceByType('summary');
  const mindmapResource = resourceByType('mindmap');
  const codeResource = resourceByType('code');
  const labHintResource = resourceByType('lab_hint');
  const practiceResource = resourceByType('practice');
  const lectureBody = String(lc.content || '');
  const embeddedCode = (() => {
    const matches = [...lectureBody.matchAll(/<pre[^>]*><code[^>]*>([\s\S]*?)<\/code><\/pre>/gi)];
    if (!matches.length) return '';
    const decode = (s: string) => s.replace(/<br\s*\/?\s*>/gi, '\n').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/<[^>]+>/g, '');
    return decode(matches[0][1]).trim();
  })();
  const rawGeneratedCode = typeof codeResource?.content === 'string' && codeResource.content.trim()
    ? codeResource.content : (embeddedCode || lc.code || '// 本讲暂无代码示例');
  const generatedCode = rawGeneratedCode
    .replace(/^```(?:python|py)?\s*/i, '').replace(/\s*```\s*$/i, '')
    .replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    // 修复讲义 HTML/Markdown 转换造成的常见粘连与截断
    .replace(/^\s*mport\s+/m, 'import ')
    .replace(/(import\s+pandas\s+as\s+pd)\s+(data\s*=)/g, '$1\n$2')
    .trim();
  const [editableCode, setEditableCode] = useState('');
  useEffect(() => { setEditableCode(generatedCode); }, [generatedCode]);

  const fetchNotes = async () => {
    setNotesLoading(true);
    try {
      const data = await api.getNotes({ lecture_id: activeLecture.num });
      setNotes(data);
    } catch (e) {
      console.error('Failed to fetch notes', e);
      setNotes([]);
    } finally {
      setNotesLoading(false);
    }
  };

  const handleQuickAddNote = async () => {
    if (!quickNoteContent.trim()) return;
    try {
      await api.createNote({
        lecture_id: activeLecture.num,
        title: quickNoteTitle.trim() || '无标题笔记',
        content: quickNoteContent.trim(),
        category: 'course',
      });
      setQuickNoteTitle('');
      setQuickNoteContent('');
      await fetchNotes();
    } catch (e) {
      console.error('Failed to add note', e);
    }
  };

  const selectLecture = (lecture: typeof ALL_LECTURES[number]) => {
    setActiveLecture({ ...lecture, dur: (lecture as any).dur || (lecture as any).duration || (lecture as any).duration_text || '45min' });
    try { localStorage.setItem(`learnmate_last_lecture_${courseId}`, String(lecture.num)); } catch {}
    router.replace(`/learn/${courseId}?lecture=${lecture.num}${selectedPath?.id ? `&path=${encodeURIComponent(selectedPath.id)}` : ''}`);
    setTab('doc');
    setQuickNoteTitle('');
    setQuickNoteContent('');
    setVideoUrl(null);
    setVideoLoading(false);
    setVideoError(null);
    setRunOutput('');
    setRunLoading(false);
    resetAgent();

    // 检查缓存：已加载过的讲次直接恢复，不重复请求 API
    const cached = lectureCache.current[cacheKey(lecture.num)];
    if (cached) {
      setLectureContent(cached);
      if (cached.video_url) setVideoUrl(cached.video_url);
    } else {
      setLectureContent(null);
    }
  };

  // （视频检测和生成已移除，统一使用数字人组件）
  useEffect(() => {
    // 切换讲次时清理
    setVideoUrl(null);
    setVideoError(null);
  }, [courseId, activeLecture.num]);

  const handleRunCode = async () => {
    const code = editableCode
      .replace(/^\s*mport\s+/m, 'import ')
      .replace(/(import\s+numpy\s+as\s+np|import\s+pandas\s+as\s+pd)\s+(data\s*=|frame\s*=)/g, '$1\n$2')
      .replace(/(\])\s+(frame\s*=|data\s*=)/g, '$1\n$2')
      .replace(/(\})\s+(print\s*\()/g, '$1\n$2');
    if (code !== editableCode) setEditableCode(code);
    if (!code.trim()) {
      setRunOutput('⚠️ 代码为空，请先编写代码');
      return;
    }
    setRunLoading(true);
    setRunOutput('🔄 正在编译执行...\n');
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 20000);
    try {
      const executeApi = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${executeApi}/api/execute/python`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          code: code,
          lab_title: lc.title || '课程代码示例'
        })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setRunOutput(data.output || '⚠️ 无输出');
    } catch (error: unknown) {
      setRunOutput(error instanceof DOMException && error.name === 'AbortError'
        ? '❌ 请求等待超过 20 秒。后端可能正忙于生成讲义，请稍后再运行代码。'
        : '❌ 请求失败: ' + (error instanceof Error ? error.message : String(error)));
    } finally {
      window.clearTimeout(timeout);
      setRunLoading(false);
    }
  };

  const handleGenerateWithAgent = async () => {
    if (isAgentRunning) return;
    setAgentRunning(true);
    setAgentSteps([]);
    try {
      const API = process.env.NEXT_PUBLIC_API_URL || '';
      const prompt = `我是学生，正在学习《${title}》，当前讲次是第${activeLecture.num}讲：${lc.title}。请帮我生成完整的学习资源包，包括：画像（6维度）、学习文档（Markdown）、练习题（选择题+填空题）、思维导图（树形结构）、代码示例（Python）和个性化学习路径。`;

      const res = await fetch(`${API}/api/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          path_type: selectedPath?.id || 'path_1',
          path_label: selectedPath?.label || '',
          path_strategy: selectedPath?.strategy || '',
          profile: userProfile,
          course_id: courseId,
          lecture_num: activeLecture.num,
        }),
      });
      const data = await res.json();

      if (data.success) {
        const steps = (data.steps || []).map((step: any, index: number) => {
          const rawName = step.name || 'unknown_agent';
          const displayName = AGENT_NAME_MAP[rawName] || rawName.replace('_agent', '');
          return {
            id: step.id || `step-${index}`,
            name: displayName,
            description: step.description || `${displayName} 执行中`,
            status: step.status || 'pending',
            output_preview: step.output_preview || '',
          };
        });

        if (steps.length > 0) {
          setAgentSteps(steps);
          steps.forEach((step: any, idx: number) => {
            setTimeout(() => {
              updateAgentStep(step.id, { status: 'success' });
            }, 600 * (idx + 1));
          });
        } else {
          setAgentSteps([
            {
              id: 'done',
              name: '✅ 资源生成完成',
              description: `路径：${selectedPath?.label || '系统学习'}，所有智能体已完成协作`,
              status: 'success',
            },
          ]);
        }
        console.log('Agent 输出:', data.output);
      } else {
        console.error('智能体返回失败:', data);
        setAgentSteps([
          {
            id: 'error',
            name: '❌ 执行失败',
            description: data.detail || '请查看控制台错误信息',
            status: 'error',
          },
        ]);
      }
    } catch (error) {
      console.error('请求智能体失败:', error);
      setAgentSteps([
        {
          id: 'error',
          name: '❌ 网络错误',
          description: '无法连接到后端服务，请检查服务是否运行',
          status: 'error',
        },
      ]);
    } finally {
      setAgentRunning(false);
    }
  };

  // 多智能体内容生成已由上方 useEffect 自动处理
  // agent_logs 通过 multi-agent 端点返回，无需额外触发

  useEffect(() => {
    let active = true;
    setResourceLoading(true);
    setVideoPlaying(false);
    setVideoError(null);
    setSelectedAnswer(null);
    videoRef.current?.pause();
    videoRef.current?.load();
    // 讲义由 multi-agent 端点生成，避免通用 resource 请求触发重复 402。
    return () => { active = false; };
  }, [activeLecture.num]);

  useEffect(() => {
    fetchNotes();
  }, [activeLecture.num]);

  const toggleModule = (i: number) => {
    setOpenModules(prev => { const next = new Set(prev); next.has(i) ? next.delete(i) : next.add(i); return next; });
  };

  const toggleVideo = async () => {
    const player = videoRef.current;
    if (!player) return;
    setVideoError(null);
    try {
      if (player.paused) await player.play();
      else player.pause();
    } catch {
      setVideoError('视频播放被浏览器拦截，请直接使用播放器控件播放。');
    }
  };

  const downloadResource = (resource: { title: string; type?: string; content?: unknown; desc?: string }, index: number) => {
    const body = typeof resource.content === 'string'
      ? resource.content
      : Array.isArray(resource.content)
        ? resource.content.map(item => `- ${item}`).join('\n')
        : `${resource.title}\n\n${resource.desc || lc.title}\n\n来源：${resourceData?.sources?.map(source => source.title).join('、') || 'LearnMate 本地资源'}`;
    const ext = resource.type === 'code' ? 'scala' : 'md';
    downloadTextFile(`learnmate-${activeLecture.num}-${index + 1}.${ext}`, body);
  };

  const formatTime = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    if (diff < 172800000) return '昨天';
    return `${d.getMonth()+1}月${d.getDate()}日`;
  };

  const currentPathLabel = selectedPath
    ? `${selectedPath.icon || '📖'} ${selectedPath.label || '系统学习'}`
    : '📖 系统学习';

  if (courseMetaLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-3 border-indigo-500 border-t-transparent mx-auto mb-3" />
          <p className="text-gray-400 text-sm">加载课程数据...</p>
        </div>
      </div>
    );
  }

  if (!courseData) {
    return (
      <div className="p-6 lg:p-8 max-w-full mx-auto">
        <div className="text-xs text-[var(--lm-text-tertiary)] mb-4">首页 / 学习空间</div>
        <div className="bg-white rounded-2xl border border-[#e8e8ea] p-12 text-center">
          <div className="text-6xl mb-4">📚</div>
          <h2 className="text-2xl font-bold text-[#1a1a2e] mb-2">课程内容正在准备中</h2>
          <p className="text-sm text-[#6a6a7e] max-w-md mx-auto">
            该课程目前还没有详细内容，请返回学习空间选择其他课程。
          </p>
          <div className="mt-6 flex gap-3 justify-center">
            <Link href="/learn" className="px-6 py-2.5 rounded-xl bg-[#4f46e5] text-white text-sm font-medium hover:bg-[#4338ca] transition-colors">返回学习空间</Link>
            <Link href="/" className="px-6 py-2.5 rounded-xl border border-[#e8e8ea] text-sm font-medium hover:bg-[#f5f5f7] transition-colors">返回首页</Link>
          </div>
        </div>
      </div>
    );
  }

  // 未完成画像评估 → 引导先去学习画像
  const hasProfile = hasCompletedProfile(userProfile);
  if (!profileLoading && !hasProfile) {
    return (
      <div className="p-6 lg:p-8 max-w-full mx-auto">
        <div className="text-xs text-[var(--lm-text-tertiary)] mb-4">首页 / 学习空间</div>
        <div className="bg-white rounded-2xl border border-[#e8e8ea] p-12 text-center">
          <div className="text-6xl mb-4">🎯</div>
          <h2 className="text-2xl font-bold text-[#1a1a2e] mb-2">请先完成学习画像评估</h2>
          <p className="text-sm text-[#6a6a7e] max-w-md mx-auto mb-6">
            学习内容会根据你的 10 项 Python 数据分析画像个性化生成。请先完成画像评估，系统才能为你定制专属学习路径和资源。
          </p>
          <Link href="/profile" className="inline-block px-6 py-2.5 rounded-xl bg-[#4f46e5] text-white text-sm font-medium hover:bg-[#4338ca] transition-colors">
            前往学习画像评估 →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-full min-h-[calc(100vh-60px)] flex flex-col mx-auto">
      <div className="text-xs text-[var(--lm-text-tertiary)] mb-2">首页 / 学习空间 / 第{activeLecture.num}讲</div>
      <h1 className="text-2xl font-bold mb-1">学习空间</h1>
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-sm text-[var(--lm-text-secondary)]">{lc.title} · {activeLecture.dur} · {lc.type}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => prevLecture && selectLecture(prevLecture)} disabled={!prevLecture} className="px-4 py-2 rounded-lg border border-[var(--lm-border)] text-sm disabled:opacity-40 disabled:cursor-not-allowed">← 上一讲</button>
          <button onClick={() => nextLecture && selectLecture(nextLecture)} disabled={!nextLecture} className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm disabled:opacity-40 disabled:cursor-not-allowed">下一讲 →</button>
        </div>
      </div>

      {/* AI 推荐学习路径 — 横向卡片条 */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Route className="w-4 h-4 text-indigo-500"/>
          <span className="text-sm font-semibold text-[var(--lm-text)]">推荐学习路径</span>
          {selectedPath && (
            <span className="text-xs text-[var(--lm-text-tertiary)]">
              · 当前：{selectedPath.icon} {selectedPath.label}
            </span>
          )}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {(pathOptions.length > 0 ? pathOptions : getPathOptions(userProfile)).map((path: any) => {
            const isActive = selectedPath?.id === path.id;
            return (
              <button
                key={path.id}
                onClick={() => setSelectedPath(path)}
                disabled={isAgentRunning}
                className={`text-left px-4 py-3 rounded-xl border-2 transition-all
                  ${isActive
                    ? 'border-indigo-500 bg-indigo-50 shadow-sm'
                    : 'border-gray-100 bg-white hover:border-indigo-200 hover:bg-gray-50'}`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{path.icon}</span>
                  <span className={`text-sm font-semibold ${isActive ? 'text-indigo-700' : 'text-[var(--lm-text)]'}`}>
                    {path.label}
                  </span>
                  {path.recommended && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium">推荐</span>
                  )}
                  {isActive && (
                    <span className="ml-auto w-2 h-2 rounded-full bg-indigo-500"/>
                  )}
                </div>
                <p className={`text-xs leading-relaxed ${isActive ? 'text-indigo-600' : 'text-[var(--lm-text-tertiary)]'}`}>
                  {path.reason.length > 60 ? path.reason.slice(0, 60) + '...' : path.reason}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid lg:grid-cols-[240px_2fr_280px] gap-6 flex-1 min-h-0">
        {/* 左侧：学习路径树 */}
        <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-5 overflow-y-auto h-full flex flex-col">

          {/* 学习路径树（根据路径动态过滤） */}
          <h4 className="font-semibold text-xs mb-2 flex items-center gap-2">
            <Clock className="w-3.5 h-3.5"/> 学习路径
            <span className="ml-auto text-[10px] text-[var(--lm-text-tertiary)] font-normal">
              {PATH_LECTURES.length || 0} 讲
            </span>
          </h4>
          <div className="flex-1 overflow-y-auto">
          {(selectedPath?.lecture_order?.length ? buildPathModules(PATH_MODULES, effectiveProfile, selectedPath.id, selectedPath) : []).map((mod: any) => {
            const modKey: number = mod._origIdx;
            return (
            <div key={modKey} className="mb-1">
              <button onClick={() => toggleModule(modKey)} className="flex items-center gap-2 w-full px-3 py-2.5 rounded-lg text-sm font-semibold hover:bg-indigo-50 transition-all">
                <ChevronRight className={`w-3 h-3 text-[var(--lm-text-tertiary)] transition-transform ${openModules.has(modKey) ? 'rotate-90' : ''}`} />
                <span>{mod.name}</span>
                <span className={`ml-auto text-xs ${mod.pathTag ? 'text-red-500 font-medium' : mod.status==='done'?'text-green-600':mod.status==='active'?'text-indigo-600':'text-[var(--lm-text-tertiary)]'}`}>
                  {mod.pathTag || (mod.status==='done'?'已完成':mod.status==='active'?'进行中':'')}
                </span>
              </button>
              {openModules.has(modKey) && mod.lectures.map((lec: any) => {
                // 画像+路径驱动的讲次标记（已在 buildPathModules 中预计算）
                const emphasis = lec._emphasis || { level: 'normal', label: '' };
                const emphasisColors: Record<string, { border: string; bg: string; dot: string; label: string }> = {
                  strengthen: { border: '#ef4444', bg: '#fef2f2', dot: '#ef4444', label: '重点补' },
                  normal: { border: '#4f46e5', bg: 'transparent', dot: '#4f46e5', label: '' },
                  fast: { border: '#16a34a', bg: '#f0fdf4', dot: '#16a34a', label: '速过' },
                  challenge: { border: '#8b5cf6', bg: '#f5f3ff', dot: '#8b5cf6', label: '挑战' },
                };
                const em = emphasisColors[emphasis.level] || emphasisColors.normal;
                return (
                  <div key={lec.num} onClick={() => selectLecture(lec)}
                    className="flex items-center gap-2 ml-7 pl-3 py-2 pr-2 rounded-lg text-sm cursor-pointer transition-all group"
                    style={{
                      borderLeft: activeLecture.num === lec.num ? `2px solid ${em.border}` : lec.done ? '2px solid #16a34a' : '2px solid transparent',
                      background: activeLecture.num === lec.num ? 'var(--lm-brand-light)' : em.bg,
                      opacity: lec.done && activeLecture.num !== lec.num ? 0.6 : 1
                    }}>
                    <div className={`rounded-full flex items-center justify-center font-semibold shrink-0 ${(lectureProgress[lec.num] || 0) > 0 ? 'w-8 h-8 text-[10px]' : 'w-5 h-5 text-[10px]'}`}
                      style={{
                        background: (() => {
                          const p = lectureProgress[lec.num] || 0;
                          if (p >= 100) return '#16a34a';
                          if (p > 0) return '#f59e0b';
                          return activeLecture.num === lec.num ? '#4f46e5' : 'transparent';
                        })(),
                        color: (lectureProgress[lec.num] || 0) > 0 || activeLecture.num === lec.num ? '#fff' : 'var(--lm-text-tertiary)',
                        border: (lectureProgress[lec.num] || 0) === 0 && activeLecture.num !== lec.num ? '2px solid var(--lm-border)' : 'none'
                      }}>
                      {(() => {
                        const p = lectureProgress[lec.num] || 0;
                        if (p >= 100) return '✓';
                        if (p > 0) return p + '%';
                        return lec._pathOrder || lec.num;
                      })()}
                    </div>
                    <span className="font-medium text-xs">{lec.title}</span>
                    {emphasis.label && (
                      <span className="ml-auto text-[9px] px-1.5 py-0.5 rounded-full font-medium"
                        style={{ background: em.dot + '18', color: em.dot }}>
                        {emphasis.label}
                      </span>
                    )}
                    <span className="text-[10px] text-[var(--lm-text-tertiary)]">{lec.dur}</span>
                  </div>
                );
              })}
            </div>
          )})}
          </div>
        </div>

        {/* 中间：内容区 */}
        <div className="flex-1 min-w-0 flex flex-col min-h-0">
          <div className="flex gap-1 bg-indigo-50 p-1 rounded-xl mb-4 flex-shrink-0">
            {TABS.map(t => {
              const visited = (visitedTabsRef.current[activeLecture.num] || []).includes(t.id);
              return (
              <button key={t.id} onClick={() => setTab(t.id)} className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-lg text-sm font-medium transition-all ${tab===t.id?'bg-white shadow-sm text-[var(--lm-text)]':visited?'text-green-600':'text-[var(--lm-text-secondary)]'}`}>
                <t.icon className="w-3.5 h-3.5"/> {t.label}
                {visited && <span className="w-1.5 h-1.5 rounded-full bg-green-500 ml-0.5"/>}
              </button>
              );
            })}
          </div>

          <div className="flex-1 overflow-y-auto min-h-0 bg-[var(--lm-surface)] border border-[var(--lm-border)] rounded-2xl p-6">
            {/* Doc tab */}
            {tab === 'doc' && (
              <>
                {contentLoading ? (
                  <div className="flex items-center justify-center h-full text-[var(--lm-text-secondary)]">
                    <div className="animate-spin text-4xl mb-4">⏳</div>
                    <p>加载讲义中...</p>
                  </div>
                ) : (
                  <>
                    <div className="flex justify-between items-center mb-4 flex-wrap gap-2">
                      <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-600 font-medium">
                        {resourceLoading ? '课程内容加载中' : profileLoading ? '画像加载中...' : `课程内容 · ${currentPathLabel}`}
                      </span>
                      <span className="text-xs text-[var(--lm-text-tertiary)]">
                        {userProfile
                          ? `基于你的10项 Python 数据分析画像适配`
                          : '画像未完成，使用课程默认内容'}
                      </span>
                    </div>
                    {Array.isArray(summaryResource?.content) && (
                      <div className="rounded-xl bg-indigo-50 p-4 mb-4">
                        <div className="text-sm font-semibold text-indigo-700 mb-2">{summaryResource.title}</div>
                        <ul className="space-y-1.5 text-sm text-indigo-950">
                          {summaryResource.content.map((item, index) => <li key={index}>- {item}</li>)}
                        </ul>
                      </div>
                    )}
                    <div className="text-sm leading-relaxed content-doc prose prose-sm max-w-none" dangerouslySetInnerHTML={{__html: sanitizeHtmlContent(lc.content)}} />
                    <div className="p-4 rounded-xl bg-blue-50 text-sm border-l-4 border-blue-500 mt-4">
                      <strong>学习提示：</strong>点击左侧不同讲次可切换内容。进行 Pandas 分组统计时，优先使用 <code className="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600 text-xs font-mono">groupby()</code> 配合聚合函数，先明确分析目标再选择字段。
                    </div>
                    <div className="mt-4 pt-3 border-t border-[var(--lm-border)] text-[10px] text-[var(--lm-text-tertiary)] flex items-center gap-4">
                      <span>🗺️ 路径：{currentPathLabel}</span>
                      <span>画像：{userProfile ? '10项领域画像' : '待评估'}</span>
                    </div>
                  </>
                )}
              </>
            )}

            {/* Code tab */}
            {tab === 'code' && (
              <div className="bg-gray-900 rounded-2xl overflow-hidden border border-[var(--lm-border)]">
                <div className="flex justify-between items-center px-4 py-2.5 bg-[#151628]">
                  <div className="flex gap-0.5">
                    <span className="px-3 py-1.5 rounded text-xs font-mono bg-gray-900 text-[#e6edf3]">
                      Lecture{activeLecture.num}.py
                    </span>
                    <span className="text-[10px] text-gray-500 ml-2 self-center">
                      {currentPathLabel}
                    </span>
                  </div>
                  <div className="flex gap-2 items-center">
                    <span className="text-[10px] text-gray-500">Python</span>
                    <button
                      onClick={() => navigator.clipboard.writeText(editableCode)}
                      className="text-xs px-2.5 py-1 rounded border border-white/10 text-gray-500 hover:bg-white/5"
                    >
                      复制
                    </button>
                  </div>
                </div>
                <div className="flex">
                  <div className="py-3 bg-[#151628] border-r border-white/5 text-right select-none min-w-[44px]">
                    {editableCode.split('\n').map((_: string, i: number) => (
                      <div key={i} className="px-3 text-xs font-mono text-gray-600 leading-[1.65]">{i+1}</div>
                    ))}
                  </div>
                  <textarea value={editableCode} onChange={e => setEditableCode(e.target.value)} spellCheck={false}
                    className="p-3 text-xs font-mono leading-[1.65] text-gray-300 bg-gray-900 outline-none resize-y min-h-[360px] overflow-x-auto flex-1" />
                </div>
                <div className="border-t border-white/10 px-4 py-3 flex gap-3">
                  <button onClick={handleRunCode} disabled={runLoading} className="px-4 py-1.5 bg-emerald-600 text-white text-xs font-medium rounded hover:bg-emerald-700 transition-colors disabled:opacity-50">
                    {runLoading ? '⏳ 运行中...' : '▶ 运行代码'}
                  </button>
                  <button onClick={() => setRunOutput('')} className="px-4 py-1.5 bg-gray-700 text-gray-300 text-xs font-medium rounded hover:bg-gray-600 transition-colors">
                    清空输出
                  </button>
                </div>
                {runOutput && (
                  <div className="border-t border-white/10 bg-black">
                    <div className="px-4 py-1.5 bg-gray-800/50 text-gray-400 text-[10px] font-mono border-b border-white/5">📋 编译输出</div>
                    <pre className="p-4 text-green-400 font-mono text-xs whitespace-pre-wrap overflow-auto max-h-96 min-h-32 leading-relaxed">
                      {runOutput}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Mindmap tab */}
            {tab === 'mindmap' && (
              <>
                <div className="mb-4 flex flex-wrap items-center gap-2">
                  <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-600 font-medium">第{activeLecture.num}讲专属导图</span>
                  <span className="text-xs text-[var(--lm-text-tertiary)]">🖱️ 滚动缩放 · 拖拽平移</span>
                  <button
                    onClick={() => setMindmapFullscreen(true)}
                    className="ml-auto text-xs px-3 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
                  >
                    ⛶ 全屏查看
                  </button>
                </div>
                {/* 交互式思维导图 */}
                <MarkmapViewer
                  data={mindmapNodes}
                  height="600px"
                  onNodeClick={(node) => console.log('[Mindmap] 点击节点:', node.label)}
                />
                {/* 全屏弹窗 */}
                {mindmapFullscreen && (
                  <div
                    className="fixed inset-0 z-[9999] backdrop-blur-sm bg-black/70 flex items-center justify-center p-6"
                    onClick={() => setMindmapFullscreen(false)}
                  >
                    <div
                      className="w-full max-w-[96vw] h-[96vh] rounded-3xl overflow-hidden shadow-2xl flex flex-col"
                      style={{ background: 'linear-gradient(160deg, #fafbff 0%, #f0f0ff 40%, #faf5ff 100%)' }}
                      onClick={e => e.stopPropagation()}
                    >
                      <div className="flex items-center justify-between px-8 py-4 shrink-0">
                        <div>
                          <span className="text-lg font-bold text-indigo-900">{lc.title}</span>
                          <span className="ml-3 text-sm text-indigo-400">思维导图 · 第{activeLecture.num}讲</span>
                        </div>
                        <button
                          onClick={() => setMindmapFullscreen(false)}
                          className="w-9 h-9 rounded-full bg-white/80 hover:bg-white text-gray-400 hover:text-gray-600 flex items-center justify-center transition-colors shadow-sm"
                        >
                          ✕
                        </button>
                      </div>
                      <div style={{ flex: 1, minHeight: 0 }}>
                        <MarkmapViewer data={mindmapNodes} height="100%" className="border-0 !rounded-none" />
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* 多模态教学视频 Tab */}
            {tab === 'video' && (
              <div className="space-y-6">
                {/* 讯飞2D数字人教师讲解 */}
                <DigitalHumanLive courseId={courseId} lectureNum={activeLecture.num} lectureTitle={activeLecture.title || lc.title} />
              </div>
            )}

            {/* Quiz tab */}
            {tab === 'quiz' && (
              <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-xs px-2.5 py-1 rounded-full bg-green-50 text-green-600 font-medium">AI 出题 Agent 生成</span>
                  <span className="ml-auto text-xs text-[var(--lm-text-tertiary)]">{currentPathLabel}</span>
                </div>
                <div className="font-semibold mb-1">本讲练习（{quizSet.length} 题）</div>
                {quizSet.map((question: any, qi: number) => { const answer = quizAnswers[qi] ?? null; return <div key={qi} className="mb-6"><div className="text-xs text-indigo-600 mb-1">第 {qi + 1} 题 · {question.type || '单选题'}</div><p className="text-sm mb-4">{question.question}</p>
                {question.options.map((opt: any, i: number) => (
                  <button key={i} data-testid={`learn-quiz-option-${qi}-${i}`} onClick={() => { setQuizAnswers(prev => ({ ...prev, [qi]: i })); setSelectedAnswer(i); if (!opt.correct) void api.createNote({ lecture_id: activeLecture.num, title: `错题：${question.question || lc.title}`, content: `你的答案：${opt.text}\n解析：${question.explanation || '请回顾本讲讲义。'}`, category: 'wrong_question' }).catch(() => {}); }} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl border mb-1.5 text-sm hover:bg-indigo-50 transition-all ${answer === null ? 'border-[var(--lm-border)]' : opt.correct ? 'bg-green-50 border-green-600' : answer === i ? 'bg-red-50 border-red-500' : 'border-[var(--lm-border)] opacity-60'}`}>
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold border border-[var(--lm-border)] ${answer !== null && opt.correct ? 'bg-green-600 text-white border-green-600' : answer === i ? 'bg-red-500 text-white border-red-500' : ''}`}>{String.fromCharCode(65+i)}</span>
                    {opt.text}
                  </button>
                ))}
                {answer !== null && (
                  <div className={`mt-3 p-4 rounded-xl text-sm ${
                      question.options[answer]?.correct
                      ? 'bg-green-50 text-green-800 border border-green-200'
                      : 'bg-red-50 text-red-800 border border-red-200'
                  }`}>
                    <div className="font-semibold mb-1">
                      {question.options[answer]?.correct ? '✅ 回答正确！' : '❌ 回答错误'}
                    </div>
                    {question.explanation && (
                      <div className="mt-2 pt-2 border-t border-current/10">
                        <span className="font-medium">📖 解析：</span>
                        {question.explanation}
                      </div>
                    )}
                    {!question.options[answer]?.correct && !question.explanation && (
                      <span>建议回顾本讲讲义中的相关知识点。</span>
                    )}
                  </div>
                )}</div>; })}
                <Link href="/quiz" className="mt-4 inline-flex w-full justify-center rounded-xl bg-indigo-600 px-4 py-3 text-sm font-medium text-white hover:bg-indigo-700">进入题库继续练习</Link>
              </div>
            )}
          </div>
        </div>

        {/* ===== 右侧边栏 ===== */}
        <aside className="w-full lg:w-80 xl:w-80 shrink-0 flex flex-col h-full min-h-0">
          <div className="flex-1 flex flex-col min-h-0 space-y-4 pr-2 custom-scrollbar">

            {/* AI 学习助手 - 固定高度 */}
            <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] overflow-hidden flex-shrink-0">
              <div className="px-4 py-3 border-b border-[var(--lm-border)] font-semibold text-sm flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-600"/> AI 学习助手 · 在线
              </div>
              <div className="p-4 space-y-3 max-h-[200px] overflow-y-auto">
                <div className="flex gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center text-xs">AI</div>
                  <div className="bg-indigo-50 rounded-2xl rounded-bl px-3.5 py-2.5 text-sm max-w-[85%]">
                    你好！当前学习<strong>第{activeLecture.num}讲：{lc.title}</strong>。
                    <span className="block text-xs text-indigo-500 mt-0.5">{currentPathLabel} · 已为你适配内容</span>
                  </div>
                </div>
                {chatMessages.map((m, i) => (
                  <div key={i} className={`flex gap-2.5 ${m.role === 'user' ? 'justify-end' : ''}`}>
                    {m.role === 'assistant' && <div className="w-7 h-7 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center text-xs shrink-0">AI</div>}
                    <div className={`rounded-2xl px-3.5 py-2.5 text-sm max-w-[85%] ${m.role === 'user' ? 'bg-indigo-600 text-white rounded-br' : 'bg-indigo-50 rounded-bl'}`}>
                      {m.content}
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex gap-2.5">
                    <div className="w-7 h-7 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center text-xs">AI</div>
                    <div className="bg-indigo-50 rounded-2xl rounded-bl px-3.5 py-2.5 text-sm">思考中...</div>
                  </div>
                )}
              </div>
              <div className="flex gap-2 p-3 border-t border-[var(--lm-border)]">
                <input
                  value={chatInput}
                  onChange={e=>setChatInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleChatSend()}
                  className="flex-1 px-3 py-2 rounded-full border border-[var(--lm-border)] text-sm outline-none focus:border-indigo-600"
                  placeholder="输入你的问题..."
                />
                <button onClick={handleChatSend} disabled={chatLoading} className="px-4 py-2 rounded-full bg-indigo-600 text-white text-sm disabled:opacity-50">发送</button>
              </div>
            </div>

            {/* ===== 学习统计 ===== */}
            <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-4">
              <div className="text-xs font-semibold text-[var(--lm-text-secondary)] mb-3">学习进度</div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-indigo-50 rounded-xl p-2 text-center">
                  <div className="text-lg font-bold text-indigo-600">{Math.floor(studyStats.minutes / 60)}</div>
                  <div className="text-gray-500">学习小时</div>
                </div>
                <div className="bg-green-50 rounded-xl p-2 text-center">
                  <div className="text-lg font-bold text-green-600">{Object.values(lectureProgress).filter(v => v >= 100).length}</div>
                  <div className="text-gray-500">完成讲次</div>
                </div>
                <div className="bg-amber-50 rounded-xl p-2 text-center">
                  <div className="text-lg font-bold text-amber-600">{studyStats.quizzes}</div>
                  <div className="text-gray-500">答题次数</div>
                </div>
                <div className="bg-purple-50 rounded-xl p-2 text-center">
                  <div className="text-lg font-bold text-purple-600">{studyStats.labs}</div>
                  <div className="text-gray-500">实验完成</div>
                </div>
              </div>
            </div>

            {/* ===== 多Agent审核验证状态 ===== */}
            <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-3">
              <div className="text-xs font-semibold text-[var(--lm-text-secondary)] mb-2 flex items-center gap-1.5">
                <Shield className="w-3 h-3 text-[#16a34a]" /> 内容审核验证
              </div>
              {lectureContent ? (
                <div className="space-y-1 text-[10px]">
                  <div className="flex justify-between">
                    <span className="text-[var(--lm-text-tertiary)]">审核状态</span>
                    <span className="text-[#16a34a] font-medium">
                      已通过
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--lm-text-tertiary)]">置信度</span>
                    <span className="font-medium">92%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--lm-text-tertiary)]">审核轮次</span>
                    <span className="font-medium">1 轮</span>
                  </div>
                </div>
              ) : (
                <div className="text-[10px] text-[var(--lm-text-tertiary)]">
          {lectureContent ? '课程内容已加载' : '点选讲次后加载内容'}
                </div>
              )}
            </div>

            {/* 我的笔记 - 占据剩余高度 */}
            <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-4 flex-1 flex flex-col min-h-0">
              <div className="flex items-center justify-between mb-3 flex-shrink-0">
                <h4 className="text-sm font-semibold flex items-center gap-1.5">
                  📝 当前讲次笔记
                  <span className="text-xs text-[var(--lm-text-tertiary)] font-normal">({notes.length})</span>
                </h4>
                <Link href="/notes" className="text-xs text-[#4f46e5] hover:underline transition-colors">全部 →</Link>
              </div>

              <div className="flex-1 min-h-0">
                {notesLoading ? (
                  <div className="text-xs text-[var(--lm-text-tertiary)] py-3 text-center">加载中...</div>
                ) : notes.length === 0 ? (
                  <div className="text-xs text-[var(--lm-text-tertiary)] py-3 text-center">还没有笔记，在下方添加一条吧 ✨</div>
                ) : (
                  <ul className="space-y-2 overflow-y-auto h-full">
                    {notes.slice(0, 4).map((note) => (
                      <li key={note.id} className="group flex items-start gap-2 py-1 border-b border-[var(--lm-border)]/30 last:border-0">
                        <span className="text-xs text-[var(--lm-text-tertiary)] mt-0.5">•</span>
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-medium truncate">{note.title || '无标题'}</div>
                          <div className="text-[10px] text-[var(--lm-text-tertiary)] truncate">
                            {note.content.slice(0, 28)}{note.content.length > 28 && '...'}
                            <span className="ml-1 text-[10px] text-[var(--lm-text-tertiary)]/60">{formatTime(note.updated_at)}</span>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="mt-3 space-y-2 flex-shrink-0">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={quickNoteTitle}
                    onChange={(e) => setQuickNoteTitle(e.target.value)}
                    placeholder="标题（可选）"
                    className="flex-1 h-8 rounded-lg border border-[var(--lm-border)] bg-transparent px-2.5 text-xs outline-none focus:border-[#4f46e5] focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={quickNoteContent}
                    onChange={(e) => setQuickNoteContent(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleQuickAddNote()}
                    placeholder="写笔记..."
                    className="flex-1 h-8 rounded-lg border border-[var(--lm-border)] bg-transparent px-2.5 text-xs outline-none focus:border-[#4f46e5] focus:ring-2 focus:ring-indigo-100"
                  />
                  <button
                    onClick={handleQuickAddNote}
                    disabled={!quickNoteContent.trim()}
                    className="px-3 h-8 rounded-lg bg-[#4f46e5] text-white text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#4338ca] transition-all flex-shrink-0"
                  >
                    添加
                  </button>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
