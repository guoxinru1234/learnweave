"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import {
  Brain, Target, Sparkles, AlertCircle, Clock, Send, Loader2, CheckCircle,
  ArrowRight, BarChart3, BookOpen, Code, FlaskConical, Search, TrendingUp,
  Lightbulb, Zap, GraduationCap, RefreshCw, Activity, Map
} from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import type { RecommendedLecture } from "@/lib/api";
import * as echarts from "echarts";

// ==================== 常量 ====================
const RADAR_DIMS = [
  { key: "python_basic", label: "Python基础", color: "#818cf8" },
  { key: "numpy", label: "NumPy", color: "#a78bfa" },
  { key: "pandas", label: "Pandas", color: "#22d3ee" },
  { key: "data_cleaning", label: "数据清洗", color: "#fbbf24" },
  { key: "visualization", label: "数据可视化", color: "#34d399" },
  { key: "etl", label: "ETL管道", color: "#f472b6" },
  { key: "sql", label: "SQL", color: "#60a5fa" },
  { key: "statistics", label: "统计分析", color: "#c084fc" },
  { key: "comprehensive_analysis", label: "综合分析", color: "#fb923c" },
  { key: "performance", label: "性能优化", color: "#4ade80" },
];

const TOPICS = [
  "Python基础", "NumPy", "Pandas", "数据清洗", "可视化",
  "环境搭建", "函数编程", "异常处理", "文件IO", "SQL", "ETL", "ML入门"
];

const DIM_DETAIL: Record<string, { desc: string; improve: string }> = {
  theoretical_basis: {
    desc: '理论基础薄弱意味着你对Python核心概念、NumPy数组原理、Pandas数据处理机制理解不够深入，可能只停留在"会调用API"而非"理解原理"层面。',
    improve: '多看讲义中的核心概念和工作原理章节，结合思维导图梳理知识体系；遇到不懂的概念先查Python官方文档再看代码。'
  },
  coding_ability: {
    desc: '编程能力不足说明你对Python/Pandas的API运用不够熟练，写数据处理代码时经常需要查文档或模仿示例。',
    improve: '在实验中心多做动手练习，从简单的DataFrame操作开始逐步过渡到groupby/merge/pivot_table等复杂操作。'
  },
  practical_ops: {
    desc: '实践操作偏弱意味着你在环境搭建、Jupyter使用、数据分析项目实战等动手环节经验不足。',
    improve: '在实验中心完成数据分析项目实验，跟着讲次中的代码示例一行行敲下来运行，遇到报错先尝试自己排查。'
  },
  troubleshooting: {
    desc: '问题排查能力不足意味着遇到报错或数据处理异常时缺乏系统的排查思路，容易卡住。',
    improve: '做完实验后查看错误信息逐行排查；遇到KeyError或TypeError时检查数据类型和列名。'
  },
  data_thinking: {
    desc: '数据思维较弱说明你面对数据问题时缺乏分析框架，不太擅长用DataFrame的方式思考数据处理流程。',
    improve: '多练习Pandas API；尝试用ETL思维方式拆解问题：数据源→清洗→转换→聚合→可视化输出。'
  },
  self_learning: {
    desc: '自学能力不足意味着你可能比较依赖教程和提示，独立探索新技术、查阅官方文档的能力有待提升。',
    improve: '遇到问题时先查Pandas/NumPy官方文档和API说明，而非直接搜答案；保持每天固定的学习时长。'
  },
  python_basic: { desc: 'Python 基础语法、数据类型、流程控制、函数与模块掌握不够扎实。', improve: '① 回顾 Python 基础讲次(第1-4讲) → ② 动手练习变量/循环/函数/文件操作 → ③ 做 5 道基础题巩固。' },
  numpy: { desc: 'NumPy 数组创建、索引切片、广播机制与向量化运算不熟练。', improve: '① 复习 ndarray 创建与索引 → ② 重点练广播机制与向量化 → ③ 用向量化替代循环做练习。' },
  pandas: { desc: 'Pandas 的 Series/DataFrame、数据筛选、groupby 聚合、merge 合并等核心操作掌握不足。', improve: '① 复习 DataFrame 基础 → ② 逐项练 groupby/merge/pivot_table → ③ 做一次完整数据处理练习。' },
  data_cleaning: { desc: '缺失值、重复值、异常值处理和数据类型转换等数据清洗能力偏弱。', improve: '① 学缺失值/重复值/异常值处理 → ② 练 fillna/drop_duplicates → ③ 处理一份真实脏数据。' },
  visualization: { desc: 'Matplotlib/Seaborn 等可视化图表的绘制与解读能力不足。', improve: '① 从折线图/柱状图入手 → ② 掌握 Seaborn 统计图 → ③ 做多子图 Dashboard 练习。' },
  etl: { desc: '数据抽取、转换、加载（ETL）的流程设计能力偏弱。', improve: '① 理解 ETL 概念 → ② 做一个抽取→转换→加载的小流程 → ③ 了解 Airflow 调度。' },
  sql: { desc: 'SQL 查询、窗口函数、索引优化等数据库操作能力不足。', improve: '① 练 SELECT/WHERE/GROUP BY → ② 学窗口函数 → ③ 用 Python 连接数据库实操。' },
  statistics: { desc: '描述统计、概率分布、假设检验等统计分析基础薄弱。', improve: '① 掌握均值/方差/分位数 → ② 学概率分布 → ③ 练 t 检验/卡方检验。' },
  comprehensive_analysis: { desc: '综合运用多种技能完成数据分析项目的能力不足。', improve: '① 拆解一个业务需求 → ② 从采集到清洗到可视化走一遍 → ③ 写一份分析报告。' },
  performance: { desc: '向量化、内存优化、并行处理等性能优化能力偏弱。', improve: '① 学向量化替代循环 → ② 理解数据类型对内存的影响 → ③ 了解 Dask 并行。' },
};

const glassCard = {
  background: '#ffffff',
  borderRadius: '16px',
  border: '1px solid #e5e7eb',
  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
};

// ==================== ECharts 雷达图 ====================
function EChartsRadar({ data }: { data: Record<string, number> }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const vals = RADAR_DIMS.map(d => data[d.key] || 0);
    const avg = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
    chart.setOption({
      tooltip: { trigger: 'item', backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: { color: '#1e1b4b', fontSize: 13 } },
      legend: { bottom: 0, data: ['当前画像'], textStyle: { color: '#444', fontSize: 11 } },
      radar: {
        center: ['50%', '46%'], radius: '62%', shape: 'polygon', splitNumber: 5,
        axisName: { color: '#374151', fontSize: 13 },
        splitArea: { areaStyle: { color: ['rgba(79,70,229,0.01)', 'rgba(79,70,229,0.01)', 'rgba(79,70,229,0.02)', 'rgba(79,70,229,0.02)', 'rgba(79,70,229,0.03)'] } },
        splitLine: { lineStyle: { color: '#e5e7eb' } },
        axisLine: { lineStyle: { color: '#d1d5db' } },
        indicator: RADAR_DIMS.map(d => ({ name: d.label, max: 100 })),
      },
      series: [{
        type: 'radar', name: '当前画像',
        data: [{ value: vals, name: '当前画像' }],
        symbol: 'circle', symbolSize: 6,
        lineStyle: { color: '#818cf8', width: 2 },
        itemStyle: { color: '#818cf8', borderColor: '#fff', borderWidth: 2 },
        areaStyle: { color: 'rgba(129,140,248,0.12)' },
      }],
      graphic: [
        { type: 'text', left: 'center', top: '38%', style: { text: `${avg}`, fill: '#1e1b4b', font: 'bold 26px system-ui', textAlign: 'center' } },
        { type: 'text', left: 'center', top: '49%', style: { text: '综合均分', fill: '#4b5563', font: '11px system-ui', textAlign: 'center' } },
      ],
    });
    const h = () => chart.resize();
    window.addEventListener('resize', h);
    return () => { window.removeEventListener('resize', h); chart.dispose(); };
  }, [data]);
  return <div ref={ref} style={{ height: 380 }} />;
}

// ==================== 知识盲区热力图 ====================
// 主题 → 领域技能映射（10技能域）
const TOPIC_SKILL_MAP: Record<string, string> = {
  'Python基础': 'python_basic', '环境搭建': 'python_basic', '函数编程': 'python_basic',
  '异常处理': 'python_basic', '文件IO': 'python_basic',
  'NumPy': 'numpy', 'Pandas': 'pandas', '数据清洗': 'data_cleaning',
  '可视化': 'visualization', 'SQL': 'sql', 'ETL': 'etl',
  'ML入门': 'comprehensive_analysis',
};

function BlindSpotHeatmap({ profile }: { profile: any }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const ds = profile || {};
    const data = RADAR_DIMS.map((d, i) => {
      const s = ds[d.key] || 0;
      return [i, 0, Math.round(Math.max(8, s))];
    });
    chart.setOption({
      tooltip: { backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: { color: '#1e1b4b', fontSize: 12 } },
      grid: { left: 5, right: 30, top: 5, bottom: 5 },
      xAxis: { type: 'category', data: RADAR_DIMS.map(d => d.label), axisLabel: { rotate: 45, fontSize: 12, color: '#374151' }, axisTick: { show: false }, axisLine: { show: false }, position: 'top' },
      yAxis: { type: 'category', data: [''], show: false },
      visualMap: { min: 0, max: 100, show: true, orient: 'vertical', right: 0, top: 'center', itemWidth: 8, itemHeight: 90, text: ['强', '弱'], textStyle: { color: '#374151', fontSize: 10 }, inRange: { color: ['#dc2626', '#f59e0b', '#22c55e'] } },
      series: [{ type: 'heatmap', data, label: { show: true, color: '#ffffff', fontSize: 12, fontWeight: 'bold' }, emphasis: { itemStyle: { shadowBlur: 8 } }, itemStyle: { borderRadius: 3, borderColor: '#fff', borderWidth: 1 } }],
    });
    const h = () => chart.resize();
    window.addEventListener('resize', h);
    return () => { window.removeEventListener('resize', h); chart.dispose(); };
  }, [profile]);
  return <div ref={ref} style={{ height: 150 }} />;
}

// ==================== 难度匹配曲线 ====================
function DifficultyCurve({ profile }: { profile: any }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const avg = Math.round(RADAR_DIMS.reduce((s, d) => s + (profile[d.key] || 0), 0) / RADAR_DIMS.length);
    const mods = ["环境搭建", "Python基础", "NumPy入门", "NumPy进阶", "Pandas基础", "数据清洗", "可视化", "SQL", "ETL", "机器学习"];
    const diff = [10, 15, 25, 35, 40, 50, 45, 55, 65, 80];
    const bandBottom = mods.map(() => Math.max(0, avg - 20));
    const bandGap = mods.map(() => Math.min(100, avg + 25) - Math.max(0, avg - 20));
    chart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: { color: '#1e1b4b', fontSize: 11 } },
      legend: { data: ['课程难度', '学习者能力', '适配区间'], bottom: 0, textStyle: { fontSize: 12, color: '#374151' } },
      grid: { left: 35, right: 15, top: 15, bottom: 70 },
      xAxis: { type: 'category', data: mods, axisLabel: { rotate: 30, fontSize: 12, color: '#374151' }, axisTick: { show: false } },
      yAxis: { type: 'value', name: '难度/能力', min: 0, max: 100, splitLine: { lineStyle: { color: '#f3f4f6' } }, axisLabel: { fontSize: 9, color: '#374151' } },
      series: [
        { name: '适配区间', type: 'line', data: bandBottom, stack: 'x', lineStyle: { opacity: 0 }, areaStyle: { color: 'transparent' }, symbol: 'none', silent: true },
        { name: '适配区间', type: 'line', data: bandGap, stack: 'x', lineStyle: { color: '#10b981', type: 'dashed', width: 1, opacity: 0.7 }, areaStyle: { color: 'rgba(16,185,129,0.25)' }, symbol: 'none', silent: true },
        { name: '课程难度', type: 'line', data: diff, smooth: true, symbol: 'diamond', symbolSize: 7, lineStyle: { color: '#f87171', width: 2 }, itemStyle: { color: '#f87171' } },
        { name: '学习者能力', type: 'line', data: mods.map(() => avg), symbol: 'circle', symbolSize: 7, lineStyle: { color: '#818cf8', width: 2.5, type: 'dashed' }, itemStyle: { color: '#818cf8' }, markLine: { silent: true, data: [{ yAxis: avg, label: { formatter: `当前 ${avg}`, fontSize: 9 } }], lineStyle: { color: '#818cf8', type: 'dotted' } } },
      ],
    });
    const h = () => chart.resize();
    window.addEventListener('resize', h);
    return () => { window.removeEventListener('resize', h); chart.dispose(); };
  }, [profile]);
  return <div ref={ref} style={{ height: 280 }} />;
}

// ==================== 薄弱面板 ====================
function WeaknessPanel({ weakDims, strategy }: { weakDims: [string, number][]; strategy?: string }) {
  if (!weakDims?.length || weakDims[0][1] === 0) return null;
  const dimKeyMap: Record<string, string> = {
    ...SKILL_LABEL_TO_KEY,
    '理论基础': 'theoretical_basis', '编程能力': 'coding_ability', '实践操作': 'practical_ops',
    '问题排查': 'troubleshooting', '数据思维': 'data_thinking', '自学能力': 'self_learning',
  };
  return (
    <div className="rounded-2xl border p-5" style={{ ...glassCard, background: 'rgba(239,68,68,0.06)', borderColor: 'rgba(239,68,68,0.25)' }}>
      <div className="flex items-center gap-2 mb-4"><AlertCircle className="w-5 h-5" style={{ color: '#f87171' }} /><h3 className="font-bold text-gray-700">薄弱环节 · 需重点加强</h3></div>
      {weakDims.map(([name, score]) => {
        const key = dimKeyMap[name] || '';
        const detail = DIM_DETAIL[key];
        return (
          <div key={name} className="rounded-xl p-4 mb-3" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(239,68,68,0.15)' }}>
            <div className="flex justify-between mb-2"><span className="font-semibold text-gray-700">{name}</span><span className="font-bold" style={{ color: '#f87171' }}>{score}/100</span></div>
            <div className="h-2 rounded-full mb-2" style={{ background: 'rgba(239,68,68,0.15)' }}><div className="h-2 rounded-full transition-all" style={{ width: `${score}%`, background: 'linear-gradient(90deg, #ef4444, #f87171)' }} /></div>
            {detail && <><p className="text-sm text-gray-600">{detail.desc}</p><div className="text-sm mt-1.5" style={{ color: '#078f9b' }}><Lightbulb className="w-4 h-4 inline shrink-0 mr-1" /><strong>补强方案：</strong>{detail.improve}</div></>}
          </div>
        );
      })}
      {strategy && (
        <div className="mt-3 rounded-xl p-4" style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.2)' }}>
          <div className="flex items-center gap-2 mb-1.5"><Brain className="w-4 h-4" style={{ color: '#08a6aa' }} /><span className="text-sm font-semibold text-gray-700">AI 学习方案</span></div>
          <p className="text-sm text-gray-600 leading-relaxed">{strategy}</p>
        </div>
      )}
    </div>
  );
}

// ==================== 偏好标签 ====================
function PreferencesTags({ cognitive, pace, motivation }: { cognitive?: string; pace?: string; motivation?: string }) {
  const tags = [];
  if (cognitive) tags.push({ label: "认知", value: cognitive, bg: 'rgba(59,130,246,0.15)', color: '#93bbfd' });
  if (pace) tags.push({ label: "节奏", value: pace, bg: 'rgba(124,58,237,0.15)', color: '#c4b5fd' });
  if (motivation) tags.push({ label: "动机", value: motivation, bg: 'rgba(16,185,129,0.15)', color: '#6ee7b7' });
  return <div className="flex flex-wrap gap-2">{tags.map(t => <span key={t.label} className="px-3 py-1.5 rounded-full text-xs font-medium" style={{ background: t.bg, color: t.color }}>{t.label}: {t.value}</span>)}</div>;
}

// ==================== 学习路径 ====================
const ALL_LECTURES = [
  { num: 1, title: 'Python环境搭建与Jupyter入门' }, { num: 2, title: '变量、数据类型与运算符' },
  { num: 3, title: '条件判断与循环控制' }, { num: 4, title: '函数定义与模块化编程' },
  { num: 5, title: 'NumPy数组创建与索引' }, { num: 6, title: '数组运算与广播机制' },
  { num: 7, title: '线性代数与矩阵运算' }, { num: 8, title: '随机数与统计函数' },
  { num: 9, title: 'Series与DataFrame基础' }, { num: 10, title: '数据筛选与条件过滤' },
  { num: 11, title: '数据合并：merge/concat/join' }, { num: 12, title: '数据透视表与分组聚合' },
  { num: 13, title: '缺失值检测与填充策略' }, { num: 14, title: '异常值识别与处理' },
  { num: 15, title: '数据类型转换与规范化' }, { num: 16, title: '文本数据处理与正则表达式' },
  { num: 17, title: 'Matplotlib基础图表绘制' }, { num: 18, title: 'Seaborn统计可视化' },
  { num: 19, title: '交互式可视化：Plotly入门' }, { num: 20, title: '数据看板Dashboard设计' },
  { num: 21, title: '电商销售数据分析实战' }, { num: 22, title: '数据ETL管道构建' },
  { num: 23, title: '机器学习入门：Scikit-learn' }, { num: 24, title: '数据分析报告撰写与部署' },
];

function profileHash(scores: Record<string, number>): number {
  const dims = ['python_basic','numpy','pandas','data_cleaning','visualization','etl','sql','statistics','comprehensive_analysis','performance'];
  let h = 0; for (const d of dims) h = ((h << 5) - h + (scores[d] || 0)) | 0; return Math.abs(h);
}

// 技能关键词(把讲次标题映射到技能域)
const SKILL_KEYWORDS: Record<string, { re: RegExp; w: number }[]> = {
  python_basic: [{ re: /Python|变量|函数|循环|条件|数据类型|运算符|模块|包|文件|异常|推导式|生成器/i, w: 3 }],
  numpy: [{ re: /NumPy|数组|广播|向量化|线性代数|矩阵|随机数|ndarray/i, w: 3 }],
  pandas: [{ re: /Pandas|DataFrame|Series|groupby|聚合|透视|merge|concat|join|时间序列|筛选|缺失|loc|iloc|query/i, w: 3 }],
  data_cleaning: [{ re: /清洗|缺失|重复|异常|标准化|归一化|正则|去重/i, w: 3 }],
  visualization: [{ re: /可视化|图表|Matplotlib|Seaborn|Pyecharts|配色|Dashboard|子图/i, w: 3 }],
  etl: [{ re: /ETL|抽取|转换|加载|管道|Airflow|调度/i, w: 3 }],
  sql: [{ re: /SQL|数据库|查询|窗口函数|索引|MySQL|SQLite|SQLAlchemy|ORM/i, w: 3 }],
  statistics: [{ re: /统计|概率|分布|假设检验|回归|相关|AB测试|均值|方差|分位数/i, w: 3 }],
  comprehensive_analysis: [{ re: /实战|业务|RFM|需求|报告|采集|爬虫|Requests|Scrapy|EDA|预测/i, w: 3 }],
  performance: [{ re: /性能|优化|内存|并行|多进程|Dask|部署|Flask|FastAPI|向量化/i, w: 3 }],
};

// 中文技能名 → 技能 key(兼容前端标签 + 后端 DOMAIN_SKILL_LABELS 标签)
const SKILL_LABEL_TO_KEY: Record<string, string> = {
  'Python基础': 'python_basic', 'NumPy': 'numpy', 'Pandas': 'pandas',
  '数据清洗': 'data_cleaning', '数据可视化': 'visualization', '可视化': 'visualization',
  'ETL管道': 'etl', 'ETL数据管道': 'etl',
  'SQL': 'sql', 'SQL与数据库': 'sql',
  '统计分析': 'statistics', '统计': 'statistics',
  '综合分析': 'comprehensive_analysis', '综合数据分析': 'comprehensive_analysis',
  '性能优化': 'performance', '性能优化与部署': 'performance',
};

// 返回某讲次的主导技能 key
function getDominantSkill(lec: { num: number; title: string }): string {
  let bestDim = '', bestScore = 0;
  for (const [dim, kws] of Object.entries(SKILL_KEYWORDS)) {
    let sc = 0;
    for (const kw of kws) if (kw.re.test(lec.title)) sc += kw.w;
    if (sc > bestScore) { bestScore = sc; bestDim = dim; }
  }
  return bestDim;
}

function getEmphasis(lec: { num: number; title: string }, profile: any, pathId: string) {
  const ds: Record<string, number> = { ...(profile || {}) };
  const kwSets: Record<string, { re: RegExp; w: number }[]> = {
    python_basic: [{ re: /Python|变量|函数|循环|条件|数据类型|运算符|模块|包|文件|异常|推导式|生成器/i, w: 3 }],
    numpy: [{ re: /NumPy|数组|广播|向量化|线性代数|矩阵|随机数|ndarray/i, w: 3 }],
    pandas: [{ re: /Pandas|DataFrame|Series|groupby|聚合|透视|merge|concat|join|时间序列|筛选|缺失|loc|iloc|query/i, w: 3 }],
    data_cleaning: [{ re: /清洗|缺失|重复|异常|标准化|归一化|正则|去重/i, w: 3 }],
    visualization: [{ re: /可视化|图表|Matplotlib|Seaborn|Pyecharts|配色|Dashboard|子图/i, w: 3 }],
    etl: [{ re: /ETL|抽取|转换|加载|管道|Airflow|调度/i, w: 3 }],
    sql: [{ re: /SQL|数据库|查询|窗口函数|索引|MySQL|SQLite|SQLAlchemy|ORM/i, w: 3 }],
    statistics: [{ re: /统计|概率|分布|假设检验|回归|相关|AB测试|均值|方差|分位数/i, w: 3 }],
    comprehensive_analysis: [{ re: /实战|业务|RFM|需求|报告|采集|爬虫|Requests|Scrapy|EDA|预测/i, w: 3 }],
    performance: [{ re: /性能|优化|内存|并行|多进程|Dask|部署|Flask|FastAPI|向量化/i, w: 3 }],
  };
  let bestDim = '', bestScore = 0;
  for (const [dim, kws] of Object.entries(kwSets)) { let sc = 0; for (const kw of kws) if (kw.re.test(lec.title)) sc += kw.w; if (sc > bestScore) { bestScore = sc; bestDim = dim; } }
  if (!bestDim) return { level: 'normal' as const, label: '' };
  const s = ds[bestDim] || 50;
  // 绝对阈值(及格线50): <50 弱项, >50 强项(补弱/强化互补,讲次不重叠)
  if (pathId === 'path_1') { if (s < 35) return { level: 'strengthen' as const, label: '重点补弱', dimScore: s }; if (s > 55) return { level: 'fast' as const, label: '速过', dimScore: s }; return { level: 'normal' as const, label: '', dimScore: s }; }
  else { if (s > 55) return { level: 'challenge' as const, label: '进阶挑战', dimScore: s }; if (s < 35) return { level: 'fast' as const, label: '基础巩固', dimScore: s }; return { level: 'normal' as const, label: '', dimScore: s }; }
}

function LearningPathSection({ scores, aiPaths, uid }: { scores: Record<string, number>; aiPaths: any[]; uid: number }) {
  const [progress, setProgress] = useState<Record<number, number>>({});

  // The server response is the single source of truth. Do not rewrite route
  // lecture orders in the profile page; learning space consumes the same data.

  useEffect(() => {
    const s = () => { try { const d = localStorage.getItem('learnmate_progress'); if (d) setProgress(JSON.parse(d)); } catch { } };
    s(); const i = setInterval(s, 3000); return () => clearInterval(i);
  }, []);

  const colors = [
    { color: '#ef4444', bg: 'from-red-50 to-rose-50', border: 'border-red-200', bar: 'bg-red-500' },
    { color: '#0aa6a6', bg: 'from-teal-50 to-cyan-50', border: 'border-teal-200', bar: 'bg-teal-500' },
    { color: '#078fc3', bg: 'from-cyan-50 to-sky-50', border: 'border-cyan-200', bar: 'bg-cyan-500' },
  ];

  // 如果 AI 路径还没加载，显示占位
  const displayPaths = aiPaths.length >= 3 ? aiPaths : [
    { id: 'path_1', icon: '🎯', label: '补弱优先', recommended: true, reason: '正在加载 AI 个性化路径...' },
    { id: 'path_2', icon: '⚡', label: '强化优势', recommended: false, reason: '正在加载 AI 个性化路径...' },
    { id: 'path_3', icon: '⚖️', label: '均衡推进', recommended: false, reason: '正在加载 AI 个性化路径...' },
  ];

  return (
    <div className="p-6" style={glassCard}>
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <Map className="w-5 h-5" style={{ color: '#078f9b' }} />个性化学习路径
        </h2>
        <div className="flex items-center gap-2">
          {aiPaths.length < 3 && <span className="text-xs text-gray-700 flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" />AI 分析中...</span>}
          <span className="text-xs text-gray-700">3条路径 · AI 画像驱动</span>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4">
        {displayPaths.map((p: any, i: number) => {
          const c = colors[i];
          const aiGenerated = aiPaths.length >= 3;
          return (
            <div key={p.id} className={`rounded-2xl border ${c.border} overflow-hidden bg-gradient-to-b ${c.bg} shadow-sm hover:shadow-md transition-shadow`}>
              {/* 卡片头部 */}
              <div className="px-5 py-4" style={{ background: `${c.color}08` }}>
                <div className="flex items-center gap-2.5 mb-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl text-white text-lg" style={{ background: c.color }}>
                    {p.icon}
                  </div>
                  <div>
                    <div className="text-base font-bold text-gray-800 flex items-center gap-1.5">
                      {p.label}
                      {p.recommended && (
                        <span className="text-xs px-1.5 py-0.5 rounded-full bg-white text-gray-700 border border-gray-200 font-normal">推荐</span>
                      )}
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{p.reason}</p>
              </div>
              {/* 讲次推荐 — 根据路径策略差异化 */}
              <div className="px-4 py-3 space-y-1">
                <div className="text-xs text-gray-700 font-medium mb-1 px-1">推荐学习路径</div>
                {(() => {
                  // 按路径过滤:补弱=弱项(<50),强化=强项(>50),均衡=全部;互补不重叠,保持顺序(1→24)
                  const introScore = Number(scores.python_basic || scores.coding_ability || 0);
                  const opsScore = Number(scores.etl || scores.practical_ops || 0);
                  const tagged = ALL_LECTURES
                    .filter((l: any) => !(introScore >= 60 || opsScore >= 60) || !/环境搭建|Jupyter入门/i.test(String(l.title || '')))
                    .map(l => ({ ...l, _e: getEmphasis(l, scores, p.id) }));
                  const scoreVals: number[] = Object.values(scores || {}).filter((v: any) => v > 0);
                  const avgScore = scoreVals.length ? scoreVals.reduce((a: any, b: any) => a + b, 0) / scoreVals.length : 50;
                  let filtered: any[];
                  if (p.id === 'path_1') {
                    filtered = tagged.filter(l => l._e.level === 'strengthen');
                    // 兜底: 无 <50 弱项时(如进阶),取低于自身均分的相对弱项
                    if (filtered.length === 0) filtered = tagged.filter(l => (l._e.dimScore || 50) < avgScore);
                    if (filtered.length < 16 && avgScore < 75) {
                      const extras = tagged.filter(l => !filtered.some(x => x.num === l.num)).sort((a, b) => (a._e.dimScore || 50) - (b._e.dimScore || 50));
                      filtered = [...filtered, ...extras.slice(0, 16 - filtered.length)];
                    }
                  } else if (p.id === 'path_2') {
                    filtered = tagged.filter(l => l._e.level === 'challenge');
                    // 兜底: 无 >50 强项时(如零基础),取高于自身均分的相对强项
                    if (filtered.length === 0) filtered = tagged.filter(l => (l._e.dimScore || 50) > avgScore);
                    if (filtered.length < 16 && avgScore < 75) {
                      const extras = tagged.filter(l => !filtered.some(x => x.num === l.num)).sort((a, b) => (b._e.dimScore || 50) - (a._e.dimScore || 50));
                      filtered = [...filtered, ...extras.slice(0, 16 - filtered.length)];
                    }
                  } else {
                    // Advanced learners review only active/weak dimensions,
                    // not every mastered lecture in the course.
                    filtered = avgScore >= 75
                      ? tagged.filter(l => (l._e.dimScore || 50) < 75 || /实战|性能|部署|项目/i.test(String(l.title)))
                      : tagged;
                  }
                  // 与学习空间保持同一讲次顺序：优先使用已持久化的 lecture_order。
                  if (Array.isArray(p.lecture_order) && p.lecture_order.length) {
                    const byNum = new globalThis.Map(tagged.map((lec: any) => [lec.num, lec]));
                    const ordered = p.lecture_order.map((num: number) => byNum.get(num)).filter(Boolean);
                    if (ordered.length) filtered = ordered;
                  }
                  return filtered.map((lec: any, pathIndex: number) => {
                    const pct = progress[lec.num] || 0;
                    const done = pct >= 100;
                    return (
                      <Link key={lec.num} href={`/learn/python-data-analysis?lecture=${lec.num}&path=${p.id}`}
                        className={`flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm transition-colors hover:bg-white/70 ${done ? 'bg-emerald-50/60' : ''}`}>
                        <div className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold ${done ? 'bg-emerald-500 text-white' : 'bg-white text-gray-700 border border-gray-200'}`}>
                          {done ? <CheckCircle className="w-2.5 h-2.5" /> : pathIndex + 1}
                        </div>
                        <span className="flex-1 truncate text-gray-700">{lec.title}</span>
                        {lec._e.label && (
                          <span className="shrink-0 text-[11px] px-1 py-0.5 rounded font-medium"
                            style={{ background: lec._e.level === 'strengthen' ? '#fef2f2' : lec._e.level === 'challenge' ? '#e8fbfa' : '#ecfdf5', color: lec._e.level === 'strengthen' ? '#ef4444' : lec._e.level === 'challenge' ? '#078f9b' : '#10b981' }}>
                            {lec._e.label}
                          </span>
                        )}
                      </Link>
                    );
                  });
                })()}
                <Link href={`/learn/python-data-analysis?path=${p.id}`} className="block text-center text-[10px] text-gray-700 hover:text-indigo-600 pt-1">
                  查看全部课程 →
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ==================== 主页面 ====================
export default function ProfilePage() {
  const { user, token } = useAuth();
  const uid = user?.id || 1;
  const [profile, setProfile] = useState<any>({ overall_score: 0, weak_dimensions: [], strong_dimensions: [], dialogue_history: [], dialogue_step: 0, dialogue_completed: false, completion_percentage: 0 });
  const [dynamicProfile, setDynamicProfile] = useState<any>(null);
  const [localStats, setLocalStats] = useState({ minutes: 0, quizzes: 0, labs: 0 });
  useEffect(() => {
    const sync = () => { try { const s = localStorage.getItem('learnmate_stats'); if (s) setLocalStats(JSON.parse(s)); } catch { } };
    sync(); const i = setInterval(sync, 3000); return () => clearInterval(i);
  }, []);
  const [loading, setLoading] = useState(true);
  const [chatInput, setChatInput] = useState("");
  const [sending, setSending] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [aiPaths, setAiPaths] = useState<any[]>([]);
  const [learningRecords, setLearningRecords] = useState<any[]>([]);

  // 从后端获取 AI 生成的个性化路径(提升到页面层,供薄弱板块和学习路径共用)
  useEffect(() => {
    // 1. 先读 localStorage 缓存,避免每次切页面都闪"正在加载 AI 个性化路径"
    // 路径缓存升级版本，避免读取旧画像阶段生成的路径
    // v4 invalidates paths cached before profile dialogue was completed;
    // each account now receives a fresh, profile-derived route set.
    const cacheKey = `learnmate_paths_v7_shared_${uid}`;
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length >= 3) {
          setAiPaths(parsed); // 学习空间和学情画像使用同一份已确认路径，避免重复调用产生不同结果
        }
      }
    } catch {}
    // 2. 后台静默刷新,成功后更新并写缓存
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const pathController = new AbortController();
    const pathTimeout = window.setTimeout(() => pathController.abort(), 12000);
    fetch(`${API}/api/profile/paths?user_id=${uid}`, { headers, signal: pathController.signal })
      .then(r => r.json())
      .then(d => {
        const paths = d.paths || [];
        if (paths.length >= 3) {
          setAiPaths(paths);
          try { localStorage.setItem(cacheKey, JSON.stringify(paths)); } catch {}
        } else {
          const fallback = [
            { id: 'path_1', icon: '🔧', label: '重点攻克薄弱知识点', recommended: true, reason: '优先补强当前最薄弱的 Python 数据分析知识点。', strategy: '围绕薄弱知识点安排讲解、练习和错题复盘。' },
            { id: 'path_2', icon: '⚡', label: '优势技能深度拓展', recommended: false, reason: '在已有优势基础上继续提升。', strategy: '围绕优势技能增加进阶案例和综合实践。' },
            { id: 'path_3', icon: '⚖️', label: 'Python 数据分析均衡推进', recommended: false, reason: '按课程顺序覆盖 Python 数据分析核心技能。', strategy: '均衡推进 Python、NumPy、Pandas、清洗、可视化和统计分析。' },
          ];
          setAiPaths(fallback);
          try { localStorage.setItem(cacheKey, JSON.stringify(fallback)); } catch {}
        }
      })
      .catch(() => {})
      .finally(() => window.clearTimeout(pathTimeout));
  }, [uid, token, API]);

  const fetchProfile = useCallback(async () => {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const fetchJson = async (url: string) => {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 12000);
      try {
        const response = await fetch(url, { headers, signal: controller.signal });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      } finally { window.clearTimeout(timeout); }
    };
    try {
      const p = await fetchJson(`${API}/api/profile?user_id=${uid}`);
      setProfile(p);
    } catch (e) { /* */ }
    try {
      const d = await fetchJson(`${API}/api/profile/dynamic/${uid}`);
      setDynamicProfile(d);
    } catch (e) { /* */ }
    try {
      const now = new Date();
      const recordsResponse = await fetch(`${API}/learning-records/?year=${now.getFullYear()}&month=${now.getMonth() + 1}`, { headers });
      if (recordsResponse.ok) setLearningRecords(await recordsResponse.json());
    } catch (e) { /* */ }
    try { const s = localStorage.getItem('learnmate_stats'); if (s) setLocalStats(JSON.parse(s)); } catch { }
    setLoading(false);
  }, [uid, token, API]);

  useEffect(() => { fetchProfile(); }, [fetchProfile]);

  const sendChat = async () => {
    if (!chatInput.trim() || sending) return;
    setSending(true);
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers.Authorization = `Bearer ${token}`;
      const response = await fetch(`${API}/api/profile/chat`, { method: "POST", headers, body: JSON.stringify({ user_id: uid, message: chatInput }) });
      if (!response.ok) throw new Error(`profile chat ${response.status}`);
      setChatInput(""); await fetchProfile();
    } catch (e) { /* */ }
    finally { setSending(false); setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100); }
  };

  const dimMap: Record<string, string> = {};
  RADAR_DIMS.forEach(d => { dimMap[d.key] = d.label; });
  // 兼容：动态画像 changes 仍使用旧版字段名
  Object.assign(dimMap, { theoretical_basis: '理论基础', coding_ability: '编程能力', practical_ops: '实践操作', troubleshooting: '问题排查', data_thinking: '数据思维', self_learning: '自学能力' });

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]"><Loader2 className="w-10 h-10 animate-spin" style={{ color: '#08b8bd' }} /></div>;

  const assessedDomainCount = RADAR_DIMS.filter(d => Number(profile.domain_skills?.[d.key] || 0) > 0).length;
  // 只有后端明确标记对话完成时才收起输入框；维度分数齐全不代表学生已经回答完。
  const isDone = profile.dialogue_completed === true;
  const changes = dynamicProfile?.changes || [];
  const domainChanges = dynamicProfile?.domain_changes || [];
  const scores: Record<string, number> = {};
  RADAR_DIMS.forEach(d => { scores[d.key] = profile.domain_skills?.[d.key] ?? 0; });
  const avgScore = Math.round(Object.values(scores).filter(v => v > 0).reduce((a, b) => a + b, 0) / Math.max(1, Object.values(scores).filter(v => v > 0).length));

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* 顶部 */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-gray-700 mb-1">首页 / 学情画像</div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ background: 'linear-gradient(135deg, #078fc3, #12c9b8)' }}>
              <Brain className="w-5 h-5 text-white" />
            </div>
            学情画像
          </h1>
          <p className="text-sm text-gray-700 mt-0.5">{isDone ? "领域技能评估 · 随学随新 · 动态更新" : `对话评估中 · ${profile.completion_percentage}%`}</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetchProfile} className="text-xs text-gray-700 hover:text-purple-400 flex items-center gap-1 transition-colors">
            <RefreshCw className="w-3 h-3" />刷新
          </button>
          <Link href="/assessment" className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium border transition-all" style={{ color: '#a78bfa', background: 'rgba(124,58,237,0.1)', borderColor: 'rgba(124,58,237,0.2)' }}>
            <BarChart3 className="w-4 h-4" />学习评估
          </Link>
        </div>
      </div>

      {/* 雷达 + 对话 */}
      <div className="grid lg:grid-cols-[1fr_380px] gap-6">
        <div className="p-4" style={glassCard}>
          <div className="flex items-center gap-2 mb-1 px-2">
            <Target className="w-4 h-4" style={{ color: '#078f9b' }} />
            <span className="text-sm font-semibold text-gray-700">领域技能雷达</span>
            <span className="text-xs text-gray-700 ml-auto">悬停查看详情</span>
          </div>
          <EChartsRadar data={scores} />
          <div className="flex justify-center gap-6 mt-2 pt-2 border-t" style={{ borderColor: 'rgba(124,58,237,0.1)' }}>
            {[{ v: avgScore, l: '综合均分' }, { v: `${Object.values(scores).filter(v => v >= 60).length}/10`, l: '达标技能', c: '#34d399' }, { v: localStats.quizzes || 0, l: '答题数', c: '#fbbf24' }, { v: localStats.labs || 0, l: '实验数', c: '#a78bfa' }].map((s, i) => (
              <div key={i} className="text-center"><div className="text-lg font-bold" style={{ color: s.c || '#e8e4f0' }}>{s.v}</div><div className="text-xs text-gray-700">{s.l}</div></div>
            ))}
          </div>
        </div>

        <div className="flex flex-col max-h-[500px]" style={glassCard}>
          <div className="px-4 py-3 border-b flex items-center gap-2" style={{ borderColor: 'rgba(124,58,237,0.1)' }}>
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: isDone ? '#10b981' : '#f59e0b', boxShadow: isDone ? '0 0 8px #10b981' : '0 0 8px #f59e0b' }} />
            <span className="font-semibold text-sm text-gray-700">AI 画像评估</span>
            <div className="ml-auto">{isDone ? <span className="text-xs flex items-center gap-1" style={{ color: '#34d399' }}><CheckCircle className="w-3.5 h-3.5" />完成</span> : <span className="text-xs text-gray-700">{profile.completion_percentage}%</span>}</div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {isDone && (
              <div className="rounded-xl p-3 text-center mb-2" style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)' }}>
                <div className="flex items-center justify-center gap-2">
                  <CheckCircle className="w-4 h-4" style={{ color: '#10b981' }} />
                  <span className="text-sm font-semibold" style={{ color: '#10b981' }}>评估完成</span>
                  <span className="text-xs text-gray-700">综合评分 {avgScore}/100</span>
                </div>
              </div>
            )}
            {profile.dialogue_history?.map((msg: any, i: number) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className="max-w-[82%] px-3.5 py-2.5 rounded-2xl text-sm" style={msg.role === "user" ? { background: 'linear-gradient(135deg, #078fc3, #08b8bd)', color: 'white', borderBottomRightRadius: '6px' } : { background: '#effafa', color: '#1f2937', border: '1px solid #cce8e7', borderBottomLeftRadius: '6px' }}>{msg.content}</div>
              </div>
            ))}
            {sending && <div className="flex justify-start"><div className="px-3.5 py-2.5 rounded-2xl text-sm" style={{ background: 'rgba(255,255,255,0.06)', color: '#444' }}><Loader2 className="w-3 h-3 animate-spin inline mr-1" />思考中...</div></div>}
            <div ref={chatEndRef} />
          </div>
          <div className="p-3 border-t flex gap-2" style={{ borderColor: 'rgba(124,58,237,0.1)' }}>
              <input value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === "Enter" && sendChat()} placeholder="输入你的回答..."
                className="flex-1 px-4 py-2.5 rounded-full border text-sm outline-none transition-all text-gray-700 placeholder-gray-600"
                style={{ background: 'rgba(255,255,255,0.04)', borderColor: 'rgba(255,255,255,0.1)' }}
                onFocus={e => { e.target.style.borderColor = 'rgba(124,58,237,0.5)'; e.target.style.boxShadow = '0 0 12px rgba(124,58,237,0.1)'; }}
                onBlur={e => { e.target.style.borderColor = 'rgba(255,255,255,0.1)'; e.target.style.boxShadow = 'none'; }} />
              <button onClick={sendChat} disabled={sending} className="px-4 py-2.5 rounded-full text-white disabled:opacity-50 transition-all"
                style={{ background: 'linear-gradient(135deg, #078fc3, #08b8bd)' }}><Send className="w-4 h-4" /></button>
          </div>
        </div>
      </div>

      <div className="p-5 rounded-2xl border" style={glassCard}>
        <div className="flex items-center gap-2 mb-3"><Clock className="w-4 h-4" style={{ color: '#078f9b' }} /><h3 className="font-semibold text-gray-700">我的学习记录</h3><span className="text-xs text-gray-500 ml-auto">本月</span></div>
        {learningRecords.length === 0 ? <p className="text-sm text-gray-500">暂无学习记录，完成讲次或练习后会显示在这里。</p> : <div className="space-y-2">{learningRecords.slice(-10).reverse().map((r: any) => <div key={r.date} className="flex justify-between text-sm text-gray-600"><span>{r.date}</span><span>{r.study_minutes || 0} 分钟 · 完成 {r.completed_lectures || 0} 讲</span></div>)}</div>}
      </div>

      {/* 知识盲区热力图 + 难度曲线（画像完成后展示） */}
      {isDone && (
        <>
          <div className="p-5" style={glassCard}>
            <div className="flex items-center gap-2 mb-3">
              <Search className="w-4 h-4" style={{ color: '#fbbf24' }} />
              <h3 className="text-sm font-semibold text-gray-700">知识盲区定位 · 知识点掌握度热力图</h3>
              <span className="text-xs text-gray-700 ml-auto">浅色 = 需加强</span>
            </div>
            <BlindSpotHeatmap profile={scores} />
          </div>

          <div className="p-5" style={glassCard}>
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4" style={{ color: '#078f9b' }} />
              <h3 className="text-sm font-semibold text-gray-700">资源难度匹配曲线</h3>
              <span className="text-xs text-gray-700 ml-auto">绿色区域 = 适配区间</span>
            </div>
            <DifficultyCurve profile={scores} />
            <p className="text-xs text-gray-700 mt-2 text-center">紫色虚线 = 当前水平 · 红色 = 课程默认难度 · 绿色 = 适配区间 · 红线超出绿带 ≠ 学不了，而是系统会自动降难度来适配你</p>
          </div>
        </>
      )}

      {/* 维度详情 + 薄弱 */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="p-5" style={glassCard}>
          <h3 className="font-bold text-gray-700 mb-3 flex items-center gap-2"><BarChart3 className="w-4 h-4" style={{ color: '#078f9b' }} />领域技能详情</h3>
          <div className="space-y-3">
            {RADAR_DIMS.map(d => {
              const v = scores[d.key] || 0;
              return (
                <div key={d.key} className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-700 w-20">{d.label}</span>
                  <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${Math.max(v, 2)}%`, background: v >= 70 ? 'linear-gradient(90deg, #10b981, #34d399)' : v >= 50 ? 'linear-gradient(90deg, #f59e0b, #fbbf24)' : 'linear-gradient(90deg, #ef4444, #f87171)' }} />
                  </div>
                  <span className="text-sm font-bold w-10 text-right" style={{ color: d.color }}>{v}</span>
                </div>
              );
            })}
          </div>
          {isDone && <div className="mt-4 pt-3 border-t" style={{ borderColor: 'rgba(124,58,237,0.1)' }}><PreferencesTags cognitive={profile.cognitive_style} pace={profile.learning_pace} motivation={profile.learning_motivation} /></div>}
        </div>

        <div className="space-y-4">
          {isDone && <WeaknessPanel weakDims={profile.domain_weak_skills} strategy={aiPaths.find((p: any) => p.recommended)?.strategy || aiPaths[0]?.strategy} />}
          {isDone && domainChanges.length > 0 && (
            <div className="rounded-2xl border p-5" style={{ background: 'rgba(16,185,129,0.06)', borderColor: 'rgba(16,185,129,0.25)' }}>
              <h3 className="font-bold text-sm text-gray-700 mb-3 flex items-center gap-2"><TrendingUp className="w-4 h-4" style={{ color: '#34d399' }} />随学随新 · 领域技能</h3>
              {domainChanges.map((c: any, i: number) => (
                <div key={i} className="flex justify-between rounded-xl px-3 py-2 text-sm mb-1.5" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <span className="text-gray-600">{c.label || c.skill}</span>
                  <div className="flex gap-2">
                    <span className="text-xs text-gray-700">{c.reason}</span>
                    <span className="font-bold" style={{ color: (c.delta ?? 0) >= 0 ? '#34d399' : '#f87171' }}>
                      {(c.delta ?? 0) >= 0 ? '+' : ''}{c.delta}（{c.old}→{c.new}）
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 学习路径 */}
      {/* 路径接口根据画像分数生成；不要求对话框先收起，避免输入框存在时路径被隐藏 */}
      {aiPaths.length > 0 && avgScore > 0 && <LearningPathSection scores={scores} aiPaths={aiPaths} uid={uid} />}
    </div>
  );
}
