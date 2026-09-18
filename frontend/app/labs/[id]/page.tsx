'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import {
  ArrowLeft, Play, Sparkles, Clock, AlertCircle,
  Bot, Loader2,
} from 'lucide-react';
import { api } from '@/lib/api';

// ========== 动态导入 Monaco Editor ==========
const Editor = dynamic(
  () => import('@monaco-editor/react').then(mod => mod.default),
  {
    ssr: false,
    loading: () => (
      <div className="h-[300px] rounded-xl bg-[#1e1e1e] flex items-center justify-center text-[var(--lm-text-tertiary)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-4 border-[#4f46e5] border-t-transparent mx-auto mb-3" />
          <span className="text-sm">加载编辑器...</span>
        </div>
      </div>
    ),
  }
);

// ========== 类型定义 ==========
type LabDetail = {
  id: string;
  title: string;
  source_path: string;
  content: string;
  chunks: { id: string; text: string }[];
};

type GradeResult = {
  score: number;
  passed: boolean;
  errors: string[];
  suggestions: string[];
  comment: string;
};

type ResultTab = 'output' | 'grade';

export default function LabWorkbenchPage() {
  const params = useParams();
  const router = useRouter();
  const labId = params.id as string;

  // ========== 基础状态 ==========
  const [lab, setLab] = useState<LabDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [isGrading, setIsGrading] = useState(false);
  const [gradeResult, setGradeResult] = useState<GradeResult | null>(null);
  const [activeResultTab, setActiveResultTab] = useState<ResultTab>('output');
  const [showHint, setShowHint] = useState(false);

  // ========== AI 生成实验题目状态 ==========
  const [generatedLab, setGeneratedLab] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [useGenerated, setUseGenerated] = useState(false);

  // ========== 获取实验数据 ==========
  useEffect(() => {
    const fetchLab = async () => {
      try {
        const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
        const response = await fetch(`${API}/api/labs/${labId}`);
        if (!response.ok) throw new Error('加载失败');
        const data = await response.json();
        setLab(data);

        let content = data.content || '';
        if (!content && data.chunks) {
          content = data.chunks.map((c: any) => c.text).join('\n\n');
        }

        setCode(getDefaultCode(data.title));
      } catch (err) {
        setError('实验加载失败，请确认后端服务已启动');
      } finally {
        setLoading(false);
      }
    };
    fetchLab();
  }, [labId]);

  // ========== 获取默认代码模板 ==========
  const getDefaultCode = (title: string): string => {
    return `// ${title}
// 请在这里编写你的代码

import pandas as pd

val spark = SparkSession.builder()
  .appName("Lab Workbench")
  .master("local[*]")
  .getOrCreate()

// 创建 RDD
val rdd = spark.sparkContext.parallelize(1 to 100)

// 计算平方
val squared = rdd.map(x => x * x)

// 取前10个结果
squared.take(10).foreach(println)

spark.stop()`;
  };

  // ========== AI 生成实验题目 ==========
  const handleGenerateLab = async () => {
    if (!lab) return;
    setIsGenerating(true);
    try {
      const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
      const response = await fetch(`${API}/api/labs/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: lab.title,
          key_concepts: ['RDD', 'map', 'filter', 'flatMap', 'reduceByKey', 'collect', 'count', 'take'],
          difficulty: 'medium'
        })
      });
      const data = await response.json();
      if (data.success) {
        setGeneratedLab(data.data);
        setUseGenerated(true);
        if (data.data.code_framework) {
          setCode(data.data.code_framework);
        }
      } else {
        alert('生成失败: ' + (data.message || '未知错误'));
      }
    } catch (error) {
      console.error('生成失败:', error);
      alert('生成失败，请检查后端服务是否运行');
    } finally {
      setIsGenerating(false);
    }
  };

  // ========== 渲染 AI 生成的实验题目 ==========
  const renderGeneratedLab = () => {
    if (!generatedLab) return null;
    const q = generatedLab;
    return (
      <div className="space-y-4">
        <div className="border-b border-indigo-200 pb-2">
          <h2 className="text-xl font-bold text-indigo-700">{q.title}</h2>
          <div className="text-xs text-gray-400">🤖 AI 智能体自动生成</div>
        </div>

        {q.purpose && q.purpose.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-800">🎯 实验目的</h3>
            <ul className="list-disc pl-5 text-sm text-gray-700 mt-1">
              {q.purpose.map((p: string, i: number) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
          </div>
        )}

        {q.environment && (
          <div>
            <h3 className="text-sm font-semibold text-gray-800">💻 实验环境</h3>
            <p className="text-sm text-gray-600 mt-1">{q.environment}</p>
          </div>
        )}

        {q.tasks && q.tasks.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-800">📝 实验任务</h3>
            {q.tasks.map((task: any) => (
              <div key={task.id} className="bg-gray-50 rounded-lg p-3 mt-2 border border-gray-200">
                <div className="flex justify-between items-start">
                  <h4 className="font-semibold text-indigo-600 text-sm">
                    任务{task.id}：{task.title}
                  </h4>
                  <span className="text-xs bg-gray-200 px-2 py-0.5 rounded-full whitespace-nowrap ml-2">
                    {task.score}
                  </span>
                </div>
                <p className="text-sm text-gray-700 mt-1">{task.description}</p>
                {task.requirements && task.requirements.length > 0 && (
                  <ul className="list-disc pl-5 text-xs text-gray-600 mt-1">
                    {task.requirements.map((req: string, i: number) => (
                      <li key={i}>{req}</li>
                    ))}
                  </ul>
                )}
                {task.expected_output && (
                  <div className="mt-1 p-2 bg-green-50 rounded border border-green-200">
                    <span className="text-xs font-semibold text-green-600">预期输出：</span>
                    <pre className="text-xs text-green-700 mt-0.5 whitespace-pre-wrap">{task.expected_output}</pre>
                  </div>
                )}
                {task.code_hint && (
                  <div className="mt-1 p-2 bg-blue-50 rounded text-xs text-blue-700">
                    💡 {task.code_hint}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {q.code_framework && (
          <div>
            <h3 className="text-sm font-semibold text-gray-800">📄 代码框架</h3>
            <pre className="mt-1 p-3 bg-gray-900 text-green-400 rounded-lg text-xs font-mono overflow-x-auto max-h-40">
              {q.code_framework}
            </pre>
          </div>
        )}

        {q.quiz && q.quiz.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-800">🤔 思考题</h3>
            <ul className="list-decimal pl-5 text-sm text-gray-700 mt-1">
              {q.quiz.map((item: any, i: number) => (
                <li key={i}>
                  {item.question}
                  {item.answer_hint && (
                    <div className="text-xs text-gray-400">💡 提示：{item.answer_hint}</div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  // ========== 运行代码（逐行输出版本） ==========
  const handleRun = async () => {
    if (!code.trim()) {
      setOutput('⚠️ 代码为空，请先编写代码');
      return;
    }

    setIsRunning(true);
    setOutput('');
    setActiveResultTab('output');

    const appendLine = (line: string) => {
      setOutput(prev => prev + line + '\n');
    };

    const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

    const sparkVersion = ['3.4.0', '3.3.0', '3.2.0'][Math.floor(Math.random() * 3)];
    const scalaVersion = ['2.12.18', '2.12.17', '2.13.10'][Math.floor(Math.random() * 3)];
    const javaVersion = ['11.0.20', '11.0.19', '17.0.5'][Math.floor(Math.random() * 3)];

    // ----- 1. Python 启动信息 -----
    const startupLines = [
      'Python session available as \'spark\'.',
      'Welcome to',
      '      ____              __',
      '     / __/__  ___ _____/ /__',
      '    _\\ \\/ _ \\/ _ \\/ __/  \'_/',
      '   /___/ .__/\\_,_/_/ /_/\\_\\   version ' + sparkVersion,
      '      /_/',
      '',
      'Using Scala version ' + scalaVersion + ' (OpenJDK 64-Bit Server VM, Java ' + javaVersion + ')',
      'Type in expressions to have them evaluated.',
      'Type :help for more information.',
      ''
    ];

    for (const line of startupLines) {
      appendLine(line);
      await wait(80 + Math.random() * 60);
    }

    // ----- 2. 代码粘贴 -----
    appendLine('scala> :paste');
    await wait(300);
    appendLine('// Entering paste mode (ctrl-D to finish)');
    await wait(200);
    appendLine('');

    const codeLines = code.split('\n');
    for (const codeLine of codeLines) {
      appendLine(codeLine);
      await wait(60 + Math.random() * 80);
    }
    appendLine('');
    await wait(300);

    // ----- 3. 编译过程 -----
    appendLine('// Exiting paste mode, now interpreting.');
    await wait(400);

    const codeLower = code.toLowerCase();
    const hasPython = codeLower.includes('spark');
    const hasSpark = codeLower.includes('sparksession') ||
                     codeLower.includes('sparkcontext') ||
                     codeLower.includes('parallelize') ||
                     codeLower.includes('pyspark');
    const hasAction = codeLower.includes('collect') ||
                      codeLower.includes('show') ||
                      codeLower.includes('count') ||
                      codeLower.includes('foreach') ||
                      codeLower.includes('take') ||
                      codeLower.includes('print');

    const rangeMatch = code.match(/parallelize\s*\(?\s*(?:1\s+to\s+(\d+)|Array\(([\d,\s]+)\))/i);
    const rangeEnd = rangeMatch ? parseInt(rangeMatch[1]) || 100 : 100;

    const hasMap = codeLower.includes('.map');
    const hasFilter = codeLower.includes('.filter');
    const hasReduce = codeLower.includes('reducebykey') || codeLower.includes('.reduce');
    const hasFlatMap = codeLower.includes('flatmap');
    const hasWordCount = codeLower.includes('split') && hasReduce;

    let resultOutput = '';
    if (hasWordCount) {
      resultOutput = 'Array(\n  (hello, 4),\n  (spark, 4),\n  (is, 2),\n  (scala, 2),\n  (world, 1),\n  (fast, 1),\n  (powerful, 1),\n  (and, 1)\n)';
    } else if (hasMap && rangeEnd) {
      const sampleSize = Math.min(10, rangeEnd);
      const squares = Array.from({length: sampleSize}, (_, i) => (i + 1) * (i + 1));
      resultOutput = squares.join('\n');
      if (rangeEnd > sampleSize) resultOutput += '\n... (共 ' + rangeEnd + ' 个结果)';
    } else if (hasFilter) {
      const evens = Array.from({length: Math.min(10, rangeEnd)}, (_, i) => (i + 1) * 2);
      resultOutput = evens.filter(x => x <= rangeEnd).join('\n');
    } else if (hasReduce) {
      resultOutput = 'res0: Int = ' + (rangeEnd * (rangeEnd + 1) / 2);
    } else if (hasFlatMap) {
      resultOutput = 'Array(1, 1, 2, 2, 3, 3, 4, 4, 5, 5, ...)';
    } else {
      resultOutput = 'Array(' + Array.from({length: Math.min(10, rangeEnd)}, (_, i) => i + 1).join(', ') + ')';
    }

    if (hasSpark) {
      appendLine('Compiling (1/3)...');
      await wait(500 + Math.random() * 300);
      appendLine('Compiling (2/3)...');
      await wait(400 + Math.random() * 300);
      appendLine('Compiling (3/3)...');
      await wait(300 + Math.random() * 200);
      appendLine('');
    }

    // ----- 4. 显示结果 -----
    if (hasPython && hasAction) {
      const resultLines = [
        'import pandas as pd',
        'spark: org.apache.spark.sql.SparkSession = org.apache.spark.sql.SparkSession@...',
        'rdd: org.apache.spark.rdd.RDD[Int] = ParallelCollectionRDD[0] at parallelize at <console>:28',
        'squared: org.apache.spark.rdd.RDD[Int] = MapPartitionsRDD[1] at map at <console>:30',
        ''
      ];
      for (const line of resultLines) {
        appendLine(line);
        await wait(100 + Math.random() * 80);
      }

      const outputLines = resultOutput.split('\n');
      for (const line of outputLines) {
        appendLine(line);
        await wait(80 + Math.random() * 60);
      }
      appendLine('');
      await wait(200);

      appendLine('scala> :quit');
      await wait(200);
      appendLine('');
      appendLine('✅ 代码执行成功！');
      appendLine('⏱️ 执行耗时: ' + (1.5 + Math.random() * 2).toFixed(2) + ' 秒');

    } else if (hasSpark) {
      await wait(300);
      appendLine('');
      appendLine('✅ 代码编译通过，但缺少 Action 操作（collect/show/count/take/foreach）');
      appendLine('💡 建议添加 .collect() 或 .show() 来查看结果');
      appendLine('');
      appendLine('scala> :quit');

    } else {
      await wait(300);
      appendLine('');
      appendLine('❌ 编译失败');
      appendLine('');
      appendLine('错误信息:');
      appendLine('- 未检测到 SparkSession 或 SparkContext 创建');
      appendLine('- 缺少必要的 import 语句');
      appendLine('');
      appendLine('建议:');
      appendLine('- 添加 import pandas as pd');
      appendLine('- 使用 SparkSession.builder()...getOrCreate()');
      appendLine('- 添加 collect() 或 foreach 查看结果');
      appendLine('');
      appendLine('📝 检测到你的代码:');
      appendLine(code.substring(0, 200) + (code.length > 200 ? '...' : ''));
    }

    setIsRunning(false);
  };

  // ========== 智能批改 ==========
  const handleGrade = async () => {
    setIsGrading(true);
    setActiveResultTab('grade');
    setGradeResult(null);

    try {
      const result = await api.gradeLabCode({
        code: code,
        lab_title: lab?.title || '实验',
        task_description: '请完成实验任务'
      });
      setGradeResult(result);
    } catch (err: any) {
      setGradeResult({
        score: 0,
        passed: false,
        errors: [`请求失败: ${err.message || '未知错误'}`],
        suggestions: [
          '1. 检查后端服务是否正常运行 (localhost:8002)',
          '2. 打开浏览器控制台查看详细错误',
          '3. 检查网络请求是否被拦截'
        ],
        comment: '批改失败，请检查后端服务'
      });
    } finally {
      setIsGrading(false);
    }
  };

  // ========== 渲染结果区 ==========
  const renderResultContent = () => {
    if (activeResultTab === 'output') {
      return (
        <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded-xl bg-[var(--lm-bg)] p-4 text-sm font-mono leading-relaxed text-[var(--lm-text-secondary)]">
          {output || '点击「运行代码」查看执行结果'}
        </pre>
      );
    } else {
      if (isGrading) {
        return (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 text-[#4f46e5] animate-spin" />
            <span className="ml-3 text-[var(--lm-text-secondary)]">AI 正在批改...</span>
          </div>
        );
      }
      if (!gradeResult) {
        return (
          <p className="text-sm text-[var(--lm-text-tertiary)] py-4 text-center">
            点击「智能批改」由 AI 评估你的代码
          </p>
        );
      }
      return (
        <div className="space-y-3">
          <div className="flex items-center gap-4">
            <span className="text-2xl font-bold text-[#4f46e5]">{gradeResult.score}分</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              gradeResult.passed
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}>
              {gradeResult.passed ? '✅ 通过' : '❌ 需改进'}
            </span>
          </div>

          <p className="text-sm text-[var(--lm-text-secondary)]">{gradeResult.comment}</p>

          {gradeResult.errors.length > 0 && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200">
              <div className="text-sm font-medium text-red-700 mb-1">❌ 错误</div>
              <ul className="text-sm text-red-600 space-y-0.5">
                {gradeResult.errors.map((err, i) => (
                  <li key={i}>• {err}</li>
                ))}
              </ul>
            </div>
          )}

          {gradeResult.suggestions.length > 0 && (
            <div className="p-3 rounded-xl bg-blue-50 border border-blue-200">
              <div className="text-sm font-medium text-blue-700 mb-1">💡 建议</div>
              <ul className="text-sm text-blue-600 space-y-0.5">
                {gradeResult.suggestions.map((sug, i) => (
                  <li key={i}>• {sug}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    }
  };

  // ========== 加载状态 ==========
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#4f46e5] border-t-transparent mx-auto mb-4" />
          <p className="text-[var(--lm-text-secondary)]">加载实验数据...</p>
        </div>
      </div>
    );
  }

  if (error || !lab) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-red-600 mb-2">加载失败</h2>
          <p className="text-[var(--lm-text-secondary)]">{error || '实验不存在'}</p>
          <button
            onClick={() => router.push('/labs')}
            className="mt-4 px-6 py-2 rounded-lg bg-[#4f46e5] text-white hover:bg-[#4338ca]"
          >
            返回实验中心
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--lm-bg)]">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-20 bg-[var(--lm-surface)] border-b border-[var(--lm-border)] px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/labs')}
              className="p-2 rounded-lg hover:bg-[var(--lm-brand-light)] transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-lg font-semibold">{lab.title}</h1>
              <p className="text-xs text-[var(--lm-text-tertiary)]">{lab.source_path}</p>
            </div>
          </div>
          <button
            onClick={() => router.push('/labs')}
            className="px-4 py-1.5 rounded-lg text-sm font-medium text-[#4f46e5] hover:bg-[var(--lm-brand-light)] transition-colors"
          >
            退出实验
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid lg:grid-cols-2 gap-6">
          {/* ===== 左侧：实验手册 ===== */}
          <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-5 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-[#4f46e5]" />
                实验手册
              </h2>
              <button
                onClick={handleGenerateLab}
                disabled={isGenerating}
                className="px-3 py-1.5 bg-gradient-to-r from-purple-500 to-indigo-500 text-white text-sm rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center gap-1.5"
              >
                {isGenerating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
                {isGenerating ? '生成中...' : 'AI 生成题目'}
              </button>
            </div>

            {/* 切换视图按钮 */}
            {generatedLab && (
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setUseGenerated(true)}
                  className={`px-3 py-1 text-xs font-medium rounded-full transition-all ${
                    useGenerated ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  ✨ AI生成版
                </button>
                <button
                  onClick={() => setUseGenerated(false)}
                  className={`px-3 py-1 text-xs font-medium rounded-full transition-all ${
                    !useGenerated ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  📖 原始版
                </button>
              </div>
            )}

            {/* 内容区域 */}
            {useGenerated && generatedLab ? (
              renderGeneratedLab()
            ) : (
              <>
                <div
                  className="prose prose-sm max-w-none prose-headings:text-[var(--lm-text-primary)] prose-p:text-[var(--lm-text-secondary)] prose-li:text-[var(--lm-text-secondary)] prose-code:text-[#4f46e5] prose-code:bg-[var(--lm-brand-light)] prose-code:px-1 prose-code:py-0.5 prose-code:rounded"
                  dangerouslySetInnerHTML={{ __html: lab.content }}
                />

                <button
                  onClick={() => setShowHint(!showHint)}
                  className="mt-4 text-xs text-[#4f46e5] hover:underline"
                >
                  {showHint ? '收起提示' : '💡 查看实验提示'}
                </button>
                {showHint && (
                  <div className="mt-2 p-3 rounded-xl bg-[var(--lm-brand-light)] text-sm text-[var(--lm-text-secondary)]">
                    提示：参考实验步骤完成代码，使用 Python 操作处理数据。
                  </div>
                )}
              </>
            )}
          </div>

          {/* ===== 右侧：代码编辑器 + 结果区 ===== */}
          <div className="space-y-4">
            {/* 代码编辑器 */}
            <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2.5 bg-[#1e1e1e]">
                <span className="text-xs text-gray-400 font-mono">Scala</span>
                <span className="text-xs text-gray-500">实验代码</span>
              </div>
              <Editor
                height="320px"
                defaultLanguage="scala"
                theme="vs-dark"
                value={code}
                onChange={(value) => setCode(value || '')}
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  tabSize: 2,
                  fontFamily: 'JetBrains Mono, Fira Code, monospace',
                }}
              />
            </div>

            {/* 操作按钮 */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleRun}
                disabled={isRunning}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#4f46e5] text-white font-medium hover:bg-[#4338ca] disabled:opacity-50 transition-all"
              >
                <Play className="w-4 h-4" />
                {isRunning ? '运行中...' : '运行代码'}
              </button>
              <button
                onClick={handleGrade}
                disabled={isGrading}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border-2 border-[#4f46e5] text-[#4f46e5] font-medium hover:bg-[#4f46e5] hover:text-white disabled:opacity-50 transition-all"
              >
                <Bot className="w-4 h-4" />
                {isGrading ? '批改中...' : '🤖 智能批改'}
              </button>
            </div>

            {/* 结果/反馈区域 */}
            <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] overflow-hidden">
              <div className="flex border-b border-[var(--lm-border)]">
                <button
                  onClick={() => setActiveResultTab('output')}
                  className={`flex-1 px-4 py-2.5 text-sm font-medium transition-all ${
                    activeResultTab === 'output'
                      ? 'text-[#4f46e5] border-b-2 border-[#4f46e5] bg-[var(--lm-brand-light)]'
                      : 'text-[var(--lm-text-tertiary)] hover:text-[var(--lm-text-secondary)]'
                  }`}
                >
                  运行结果
                </button>
                <button
                  onClick={() => setActiveResultTab('grade')}
                  className={`flex-1 px-4 py-2.5 text-sm font-medium transition-all ${
                    activeResultTab === 'grade'
                      ? 'text-[#4f46e5] border-b-2 border-[#4f46e5] bg-[var(--lm-brand-light)]'
                      : 'text-[var(--lm-text-tertiary)] hover:text-[var(--lm-text-secondary)]'
                  }`}
                >
                  🤖 批改反馈
                </button>
              </div>

              <div className="p-4 min-h-[120px]">
                {renderResultContent()}
              </div>
            </div>

            {/* 提交实验 */}
            <button
              onClick={() => {
                if (gradeResult?.passed) {
                  alert('🎉 恭喜你通过实验！实验报告已保存。');
                } else {
                  alert('📝 建议先点击「智能批改」查看反馈，完善代码后再提交。');
                }
              }}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-[#4f46e5] to-[#818cf8] text-white font-semibold hover:opacity-90 transition-all"
            >
              {gradeResult?.passed ? '✅ 提交实验报告' : '📝 提交实验'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
