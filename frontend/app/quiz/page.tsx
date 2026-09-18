'use client';
import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  BarChart3,
  BookOpen,
  Flame,
  Clock,
  Search,
  ChevronRight,
  Timer,
  Trophy,
} from 'lucide-react';
import { api, type QuizQuestion } from '@/lib/api';
import { CircularProgress } from '@/components/CircularProgress';

// ============================================================
// 细粒度知识点 + 考点列表（用于展示列表和元数据）
// ============================================================
const TOPIC_QUESTIONS: Record<
  string,
  { id: string; title: string; type: string; difficulty: number; mastery: number; source: string }[]
> = {
  'Python基础': [
    { id: 's1', title: 'Python中列表和元组的区别', type: '选择题', difficulty: 1, mastery: 92, source: '第2讲' },
    { id: 's2', title: 'Python字典的键有什么要求', type: '选择题', difficulty: 1, mastery: 85, source: '第2讲' },
    { id: 's3', title: 'Python中==和is的区别', type: '选择题', difficulty: 2, mastery: 78, source: '第2讲' },
    { id: 's4', title: '列表推导式的执行顺序', type: '选择题', difficulty: 2, mastery: 70, source: '第3讲' },
    { id: 's5', title: 'Python函数参数的传递方式', type: '选择题', difficulty: 2, mastery: 76, source: '第4讲' },
    { id: 's6', title: 'for循环中break和continue的区别', type: '选择题', difficulty: 1, mastery: 90, source: '第3讲' },
    { id: 's7', title: 'Python中的作用域规则(LEGB)', type: '选择题', difficulty: 3, mastery: 55, source: '第4讲' },
    { id: 's8', title: 'Python切片操作的语法', type: '选择题', difficulty: 1, mastery: 88, source: '第2讲' },
    { id: 's9', title: 'with语句的作用', type: '选择题', difficulty: 2, mastery: 72, source: '第4讲' },
    { id: 's10', title: 'Python中异常处理的方式', type: '选择题', difficulty: 2, mastery: 68, source: '第4讲' },
  ],
  'NumPy基础': [
    { id: 'h1', title: 'NumPy数组与Python列表的性能差异', type: '选择题', difficulty: 1, mastery: 88, source: '第5讲' },
    { id: 'h2', title: 'np.array()创建的数组dtype如何指定', type: '选择题', difficulty: 2, mastery: 80, source: '第5讲' },
    { id: 'h3', title: 'NumPy数组的shape和reshape', type: '选择题', difficulty: 2, mastery: 75, source: '第5讲' },
    { id: 'h4', title: 'np.arange()和np.linspace()的区别', type: '选择题', difficulty: 2, mastery: 78, source: '第6讲' },
    { id: 'h5', title: 'NumPy广播机制的工作原理', type: '选择题', difficulty: 3, mastery: 62, source: '第6讲' },
    { id: 'h6', title: 'NumPy中axis=0和axis=1的含义', type: '选择题', difficulty: 2, mastery: 72, source: '第7讲' },
    { id: 'h7', title: 'np.where()的用法', type: '选择题', difficulty: 2, mastery: 70, source: '第7讲' },
    { id: 'h8', title: 'NumPy数组的布尔索引', type: '选择题', difficulty: 2, mastery: 82, source: '第6讲' },
    { id: 'h9', title: 'np.random.seed()的作用', type: '选择题', difficulty: 1, mastery: 90, source: '第8讲' },
    { id: 'h10', title: 'NumPy中视图(view)和副本(copy)的区别', type: '选择题', difficulty: 3, mastery: 58, source: '第6讲' },
  ],
  'Pandas基础': [
    { id: 'r1', title: 'Series和DataFrame的区别', type: '选择题', difficulty: 1, mastery: 90, source: '第9讲' },
    { id: 'r2', title: 'df.head()和df.tail()的作用', type: '选择题', difficulty: 1, mastery: 95, source: '第9讲' },
    { id: 'r3', title: 'loc和iloc的区别', type: '选择题', difficulty: 2, mastery: 78, source: '第10讲' },
    { id: 'r4', title: '如何从CSV文件读取数据', type: '选择题', difficulty: 1, mastery: 92, source: '第9讲' },
    { id: 'r5', title: 'df.info()和df.describe()的区别', type: '选择题', difficulty: 2, mastery: 75, source: '第9讲' },
    { id: 'r6', title: '布尔索引筛选数据的语法', type: '选择题', difficulty: 2, mastery: 80, source: '第10讲' },
    { id: 'r7', title: 'df.dropna()的参数用法', type: '选择题', difficulty: 2, mastery: 68, source: '第10讲' },
    { id: 'r8', title: '如何给DataFrame添加新列', type: '选择题', difficulty: 1, mastery: 88, source: '第9讲' },
    { id: 'r9', title: 'df.sort_values()的参数', type: '选择题', difficulty: 2, mastery: 72, source: '第10讲' },
    { id: 'r10', title: 'Pandas中链式操作的方法', type: '选择题', difficulty: 3, mastery: 55, source: '第10讲' },
  ],
  '数据清洗': [
    { id: 'p1', title: '缺失值的识别方法(isna/notna)', type: '选择题', difficulty: 1, mastery: 82, source: '第13讲' },
    { id: 'p2', title: 'fillna()的method参数选项', type: '选择题', difficulty: 2, mastery: 72, source: '第13讲' },
    { id: 'p3', title: 'drop_duplicates()的去重逻辑', type: '选择题', difficulty: 2, mastery: 75, source: '第14讲' },
    { id: 'p4', title: '异常值检测的Z-score方法', type: '选择题', difficulty: 3, mastery: 58, source: '第14讲' },
    { id: 'p5', title: 'IQR方法剔除异常值', type: '选择题', difficulty: 3, mastery: 55, source: '第14讲' },
    { id: 'p6', title: 'astype()类型转换的注意事项', type: '选择题', difficulty: 2, mastery: 70, source: '第15讲' },
    { id: 'p7', title: 'str.replace()文本清洗的用法', type: '选择题', difficulty: 2, mastery: 68, source: '第16讲' },
    { id: 'p8', title: '正则表达式提取数据的基本语法', type: '选择题', difficulty: 3, mastery: 50, source: '第16讲' },
  ],
  'Matplotlib可视化': [
    { id: 'v1', title: 'plt.plot()的基本用法', type: '选择题', difficulty: 1, mastery: 85, source: '第17讲' },
    { id: 'v2', title: 'plt.figure()和plt.subplot()的区别', type: '选择题', difficulty: 2, mastery: 72, source: '第17讲' },
    { id: 'v3', title: 'Matplotlib中设置中文字体', type: '选择题', difficulty: 2, mastery: 65, source: '第17讲' },
    { id: 'v4', title: 'Seaborn与Matplotlib的关系', type: '选择题', difficulty: 2, mastery: 70, source: '第18讲' },
    { id: 'v5', title: 'plt.bar()和plt.hist()的区别', type: '选择题', difficulty: 2, mastery: 68, source: '第18讲' },
  ],
  'ETL综合实践': [
    { id: 'sq1', title: 'ETL管道的三个步骤', type: '选择题', difficulty: 2, mastery: 72, source: '第21讲' },
    { id: 'sq2', title: 'pd.read_csv()的常用参数', type: '选择题', difficulty: 1, mastery: 90, source: '第9讲' },
    { id: 'sq3', title: 'DataFrame的dtypes属性', type: '选择题', difficulty: 2, mastery: 65, source: '第9讲' },
    { id: 'sq4', title: 'df.columns和df.index', type: '选择题', difficulty: 1, mastery: 75, source: '第9讲' },
    { id: 'sq5', title: 'Pandas链式操作注意事项', type: '选择题', difficulty: 3, mastery: 58, source: '第9讲' },
    { id: 'sq6', title: '读取Excel/JSON数据', type: '选择题', difficulty: 2, mastery: 78, source: '第9讲' },
  ],
  'ETL与实战': [
    { id: 'st1', title: 'ETL管道的三个步骤', type: '选择题', difficulty: 2, mastery: 68, source: '第22讲' },
    { id: 'st2', title: '数据清洗的基本流程', type: '选择题', difficulty: 2, mastery: 72, source: '第22讲' },
    { id: 'st3', title: 'Pandas管道操作(.pipe)', type: '选择题', difficulty: 3, mastery: 50, source: '第22讲' },
  ],
  'Scikit-learn入门': [
    { id: 'm1', title: 'train_test_split的作用', type: '选择题', difficulty: 2, mastery: 72, source: '第23讲' },
    { id: 'm2', title: 'StandardScaler数据标准化', type: '选择题', difficulty: 3, mastery: 65, source: '第23讲' },
    { id: 'm3', title: '分类与回归的区别', type: '选择题', difficulty: 2, mastery: 60, source: '第23讲' },
    { id: 'm4', title: '交叉验证的基本原理', type: '选择题', difficulty: 3, mastery: 50, source: '第23讲' },
    { id: 'm7', title: '特征选择与降维 (PCA)', type: '选择题', difficulty: 4, mastery: 40, source: '第12讲' },
    { id: 'm8', title: '模型保存与加载', type: '选择题', difficulty: 3, mastery: 55, source: '第12讲' },
  ],
  '数据可视化': [
    { id: 'g1', title: 'Seaborn 统计可视化入门', type: '选择题', difficulty: 2, mastery: 68, source: '第18讲' },
    { id: 'g2', title: 'PageRank 算法原理', type: '选择题', difficulty: 4, mastery: 48, source: '第12讲' },
    { id: 'g3', title: '边与顶点的操作', type: '选择题', difficulty: 4, mastery: 40, source: '第12讲' },
    { id: 'g4', title: '图计算的应用场景', type: '选择题', difficulty: 3, mastery: 55, source: '第12讲' },
    { id: 'g5', title: 'Triangle Counting 算法', type: '选择题', difficulty: 4, mastery: 38, source: '第12讲' },
  ],
};

// 知识点元信息
const TOPIC_META: {
  id: string;
  name: string;
  icon: string;
  weak?: boolean;
}[] = [
  { id: 'Python基础', name: 'Python基础', icon: '📘' },
  { id: '高阶函数', name: '高阶函数', icon: '🔀' },
  { id: 'NumPy数组操作', name: 'NumPy数组操作', icon: '📦' },
  { id: 'PairDataFrame 与聚合', name: 'PairDataFrame 与聚合', icon: '🔗' },
  { id: 'Action 算子', name: 'Action 算子', icon: '⚡' },
  { id: '依赖与容错', name: '依赖与容错', icon: '🛡️' },
  { id: 'Shuffle 与存储', name: 'Shuffle 与存储', icon: '💾', weak: true },
  { id: 'Pandas 数据处理', name: 'Pandas 数据处理', icon: '📊' },
  { id: 'NumPy 数值计算', name: 'NumPy 数值计算', icon: '🔢' },
  { id: '数据ETL管道构建', name: '数据ETL管道构建', icon: '🌊' },
  { id: '机器学习基础', name: '机器学习基础', icon: '🤖' },
  { id: '数据可视化', name: '数据可视化', icon: '📈' },
];

type QuizDifficulty = 'adaptive' | 'basic' | 'intermediate' | 'advanced';
const QUIZ_CACHE_VERSION = 'v3';

const DIFFICULTY_LEVELS: {
  stars: string;
  label: string;
  difficulty: QuizDifficulty;
  count: number;
  acc: number;
  desc: string;
  unlocked: boolean;
}[] = [
  {
    stars: '★★',
    label: '基础入门',
    difficulty: 'basic',
    count: 18,
    acc: 88,
    desc: '适合刚接触该知识点的练习，侧重概念理解和基本语法',
    unlocked: true,
  },
  {
    stars: '★★★',
    label: '进阶巩固',
    difficulty: 'intermediate',
    count: 28,
    acc: 72,
    desc: '需要综合运用多个概念，涉及实际编码和分析',
    unlocked: true,
  },
  {
    stars: '★★★★',
    label: '综合实战',
    difficulty: 'advanced',
    count: 20,
    acc: 55,
    desc: '模拟真实场景，考察多知识点交叉和性能调优能力',
    unlocked: true,
  },
  {
    stars: '★★★★★',
    label: '专家级',
    difficulty: 'advanced',
    count: 0,
    acc: 0,
    desc: '源码级理解 + 架构设计 + 生产环境问题排查',
    unlocked: false,
  },
];

// 模拟考试
const MOCK_EXAMS = [
  {
    title: '章节测试',
    topic: 'NumPy数组操作',
    difficulty: 'intermediate' as QuizDifficulty,
    desc: '基于当前学习进度，AI 自动组卷 15-20 题',
    tags: ['限时 30min'],
  },
  {
    title: '薄弱点专项',
    topic: 'Shuffle 与存储',
    difficulty: 'intermediate' as QuizDifficulty,
    desc: '聚焦 Shuffle + 流处理，AI 重点出题 10 题',
    tags: ['不限时', '高优先级'],
    accent: true,
  },
  {
    title: '综合模拟',
    topic: '综合练习',
    difficulty: 'advanced' as QuizDifficulty,
    desc: '全课程范围随机出题 30 题',
    tags: ['限时 60min'],
  },
  {
    title: '每日一练',
    topic: '综合练习',
    difficulty: 'basic' as QuizDifficulty,
    desc: 'AI 每日推送 3 道混合难度题目',
    tags: ['5-10min'],
    done: true,
  },
];

// ========== 初始错题数据 ==========
const INITIAL_WRONG_QUESTIONS = [
  {
    id: 1,
    topic: 'Shuffle 与存储',
    q: '以下哪个操作不会触发 Shuffle？',
    options: ['reduceByKey', 'map', 'groupByKey', 'join'],
    answer: 1,
    explain: 'map 是窄依赖转换，不需要跨分区重分布。',
    wrongCount: 2,
    correct: 'B',
    yours: 'A',
    consecutiveCorrect: 0,
    inWrongList: true,
  },
  {
    id: 2,
    topic: 'Shuffle 与存储',
    q: 'reduceByKey 和 groupByKey 的本质区别？',
    options: ['reduceByKey 只能求和', 'groupByKey 不会产生网络 IO', 'reduceByKey 可在 Map 端局部聚合', '二者完全相同'],
    answer: 2,
    explain: 'reduceByKey 能先在 Map 端局部聚合，减少 Shuffle 数据量。',
    wrongCount: 3,
    correct: 'C',
    yours: 'A',
    consecutiveCorrect: 0,
    inWrongList: true,
  },
  {
    id: 3,
    topic: '数据ETL管道构建',
    q: '数据ETL管道构建 将实时数据流抽象为什么？',
    options: ['不断追加的表', '静态配置文件', 'Driver 日志', 'HDFS 副本'],
    answer: 0,
    explain: '数据ETL管道构建 的核心抽象是不断追加的输入表。',
    wrongCount: 1,
    correct: 'A',
    yours: 'B',
    consecutiveCorrect: 0,
    inWrongList: true,
  },
  {
    id: 4,
    topic: 'NumPy数组操作',
    q: '关于广播变量描述正确的是？',
    options: ['缓存到 Executor 供 Task 读取', '只能在浏览器使用', '每次 Task 都从 Driver 重新传输', '只能保存字符串'],
    answer: 0,
    explain: '广播变量会被分发并缓存到 Executor，适合共享只读大对象。',
    wrongCount: 1,
    correct: 'A',
    yours: 'C',
    consecutiveCorrect: 0,
    inWrongList: true,
  },
];

export default function QuizPage() {
  const { user, token } = useAuth();
  const [profileScores, setProfileScores] = useState<Record<string, number>>({});
  const [realAttempts, setRealAttempts] = useState(0);
  const [topicProgress, setTopicProgress] = useState<Record<string, any>>({});
  useEffect(() => {
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/profile?user_id=${user?.id || 1}`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(p => { if (p?.domain_skills) setProfileScores(p.domain_skills); })
      .catch(() => {});
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/quiz/progress`, { headers })
      .then(r => r.ok ? r.json() : null).then(p => { setRealAttempts(Number(p?.attempts || 0)); setTopicProgress(p?.topics || {}); }).catch(() => {});
  }, [user?.id, token]);
  const [tab, setTab] = useState('topic');
  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(
    new Set(Object.entries(TOPIC_QUESTIONS).filter(([, questions]) => questions.length > 0).map(([topic]) => topic))
  );
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'mastered' | 'learning' | 'weak'>('all');

  // 练习状态
  const [practiceTopic, setPracticeTopic] = useState<string | null>(null);
  const [practiceTitle, setPracticeTitle] = useState('');
  const [practiceDifficulty, setPracticeDifficulty] = useState<QuizDifficulty>('adaptive');
  const [generatedQuestions, setGeneratedQuestions] = useState<QuizQuestion[] | null>(null);
  const [loadingQuiz, setLoadingQuiz] = useState(false);
  const [currentQ, setCurrentQ] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [draftAnswer, setDraftAnswer] = useState('');
  const [score, setScore] = useState(0);
  const [done, setDone] = useState(false);
  const [timeSpent, setTimeSpent] = useState(0);
  const [timerActive, setTimerActive] = useState(false);

  // ===== 每道题的对错状态 =====
  const [questionResults, setQuestionResults] = useState<Record<number, 'correct' | 'wrong' | null>>({});

  // 错题本状态
  const [wrongQuestions, setWrongQuestions] = useState<any[]>([]);
  const [expandedWrongId, setExpandedWrongId] = useState<number | null>(null);
  const [retryResults, setRetryResults] = useState<Record<number, 'correct' | 'wrong' | null>>({});
  useEffect(() => {
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/notes/?category=wrong_question`, { headers })
      .then(r => r.ok ? r.json() : []).then(items => setWrongQuestions(Array.isArray(items) ? items : [])).catch(() => setWrongQuestions([]));
  }, [user?.id, token]);

  // ========== 计时器 ==========
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (timerActive && !done) {
      interval = setInterval(() => {
        setTimeSpent(prev => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [timerActive, done]);

  // ========== 重置答题卡状态 ==========
  useEffect(() => {
    if (practiceTopic) {
      setQuestionResults({});
    }
  }, [practiceTopic]);

  // ========== 统计 ==========
  const totalQuestions = Object.values(TOPIC_QUESTIONS).reduce((acc, qs) => acc + qs.length, 0);
  const topicSkill: Record<string, string> = { 'Python基础': 'python_basic', 'NumPy基础': 'numpy', 'Pandas基础': 'pandas', '数据清洗': 'data_cleaning', 'Matplotlib可视化': 'visualization', '数据可视化': 'visualization' };
  const accountMastery = (topic: string, fallback: number) => {
    const p = topicProgress[topic];
    return p ? Math.round((p.correct / Math.max(p.total, 1)) * 100) : 0;
  };
  const questionMastery = (topic: string, title: string, fallback: number) => {
    const exact = topicProgress[`${topic}|${title}`];
    if (exact) return Math.round((exact.correct / Math.max(exact.total, 1)) * 100);
    // 没有做过这道题时显示该题自己的初始掌握度（当前账号未作答则为 0），
    // 不能把分类汇总分数复制到同分类的每一道题。
    return 0;
  };
  const avgMastery = Math.round(
    realAttempts === 0 ? 0 : Object.values(TOPIC_QUESTIONS).reduce((acc, qs) => acc + qs.reduce((s, q) => s + q.mastery, 0), 0) / totalQuestions
  );
  const activeWrong = wrongQuestions.filter(w => w.inWrongList);
  const masteredWrong = wrongQuestions.filter(w => !w.inWrongList);

  // ========== 筛选逻辑 ==========
  const getFilteredTopics = () => {
    let filtered = TOPIC_META;
    if (filterStatus === 'mastered') {
      filtered = filtered.filter(t => {
        const qs = TOPIC_QUESTIONS[t.id] || [];
        const avg = qs.reduce((s, q) => s + q.mastery, 0) / (qs.length || 1);
        return avg >= 80;
      });
    } else if (filterStatus === 'learning') {
      filtered = filtered.filter(t => {
        const qs = TOPIC_QUESTIONS[t.id] || [];
        const avg = qs.reduce((s, q) => s + q.mastery, 0) / (qs.length || 1);
        return avg >= 50 && avg < 80;
      });
    } else if (filterStatus === 'weak') {
      filtered = filtered.filter(t => {
        const qs = TOPIC_QUESTIONS[t.id] || [];
        const avg = qs.reduce((s, q) => s + q.mastery, 0) / (qs.length || 1);
        return avg < 50 || t.weak;
      });
    }
    if (searchTerm.trim()) {
      filtered = filtered.filter(t => t.name.includes(searchTerm.trim()));
    }
    return filtered;
  };
  const filteredTopics = getFilteredTopics();
  // 以实际题库键为准生成分类，避免 TOPIC_META 文案/编码差异导致整类题目消失。
  const topicIcons: Record<string, string> = {
    'Python基础': '🐍', 'NumPy基础': '🔢', 'Pandas基础': '📊', '数据清洗': '🧹',
    'Matplotlib可视化': '📈', '数据可视化': '📈', 'ETL综合实践': '🌊', 'ETL与实战': '🌊',
    'Scikit-learn入门': '🤖',
  };
  const availableTopics = Object.entries(TOPIC_QUESTIONS)
    .filter(([, questions]) => questions.length > 0)
    .map(([name, questions]) => ({ id: name, name, icon: topicIcons[name] || '📘', questions }))
    .filter(topic => {
      if (filterStatus === 'all') return true;
      const mastery = accountMastery(topic.name, 0);
      return filterStatus === 'weak' ? mastery < 50 : filterStatus === 'mastered' ? mastery >= 80 : mastery >= 50 && mastery < 80;
    })
    .filter(topic => !searchTerm.trim() || topic.name.includes(searchTerm.trim()));

  const toggleTopic = (topicId: string) => {
    setExpandedTopics(prev => {
      const next = new Set(prev);
      if (next.has(topicId)) next.delete(topicId);
      else next.add(topicId);
      return next;
    });
  };

  const toggleQuestionSelection = (qId: string) => {
    setSelectedQuestions(prev =>
      prev.includes(qId) ? prev.filter(id => id !== qId) : [...prev, qId]
    );
  };

  // ========== 开始练习（选中的题目） ==========
  const handlePracticeSelected = () => {
    if (selectedQuestions.length === 0) return;
    const firstQuestion = Object.entries(TOPIC_QUESTIONS)
      .find(([topic, qs]) => qs.some(q => selectedQuestions.includes(q.id)));
    if (firstQuestion) {
      const topic = firstQuestion[0];
      const firstQ = firstQuestion[1].find(q => selectedQuestions.includes(q.id));
      if (firstQ) {
        handlePractice(topic, 'intermediate', firstQ.title, firstQ.source);
      }
      setSelectedQuestions([]);
    }
  };

  // ========== 练习模式 - 完全依赖后端个性化出题（不再使用静态题库） ==========
  const handlePractice = async (topic: string, difficulty: QuizDifficulty = 'adaptive', title?: string, lecture?: string) => {
    if (!topic || topic.trim() === '') {
      const params = new URLSearchParams(window.location.search);
      const t = params.get('topic');
      topic = t && t.trim() !== '' ? t : 'Python基础';
    }
    if (topic === '综合练习') {
      topic = 'Python基础';
    }

    console.log('[Quiz] 开始个性化练习，考点:', title || topic);

    setPracticeTopic(topic);
    setPracticeTitle(title || topic);
    setPracticeDifficulty(difficulty);
    setLoadingQuiz(true);
    setCurrentQ(0);
    setSelected(null);
    setShowAnswer(false);
    setDraftAnswer('');
    setScore(0);
    setDone(false);
    setTimeSpent(0);
    setTimerActive(true);
    setQuestionResults({});

    const cacheKey = `learnmate:quiz:${QUIZ_CACHE_VERSION}:${user?.id || 0}:${topic}:${title || topic}:${difficulty}`;
    try {
      const cached = window.localStorage.getItem(cacheKey);
      if (cached) {
        const cachedQuestions = JSON.parse(cached);
        if (Array.isArray(cachedQuestions) && cachedQuestions.length > 0) {
          setGeneratedQuestions(cachedQuestions);
          setLoadingQuiz(false);
          return;
        }
      }
    } catch (error) {
      console.warn('[Quiz] 读取题组缓存失败', error);
    }

    // 后端根据账号画像 + 考点(RAG 证据) 生成专属题组；本地不再回退静态题库。
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers.Authorization = `Bearer ${token}`;
      const skillMap: Record<string, string> = { 'Python基础': 'python_basic', 'NumPy基础': 'numpy', 'Pandas基础': 'pandas', '数据清洗': 'data_cleaning', '数据可视化': 'visualization' };
      const score = profileScores[skillMap[topic]] ?? 0;
      const targetDifficulty = score < 35 ? 'basic' : score < 70 ? 'intermediate' : 'advanced';
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/generate/quiz`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ topic, subtopic: title || topic, count: 5, difficulty: targetDifficulty, user_id: user?.id || 0, lecture }),
      });
      if (response.ok) {
        const data = await response.json();
        const dynamic = (data.questions || []).slice(0, 5).map((question: any, index: number) => ({
          ...question,
          topic: title || topic,
          id: `${question.id || 'generated'}-${encodeURIComponent(title || topic)}-${index}`,
          q: question.q || question.question || `${title || topic}：练习题 ${index + 1}`,
          options: Array.isArray(question.options)
            ? question.options.map((option: any) => typeof option === 'string' ? option : option.text || option.label || JSON.stringify(option))
            : [],
        }));
        if (dynamic.length > 0) {
          setGeneratedQuestions(dynamic);
          window.localStorage.setItem(cacheKey, JSON.stringify(dynamic));
          setLoadingQuiz(false);
          return;
        }
      }
    } catch (e) {
      console.error('[Quiz] 个性化出题失败', e);
    }

    // 大模型不可用时使用当前小节的本地题库兜底，避免题库出现空白。
    const currentItem = (TOPIC_QUESTIONS[topic] || []).find(item => item.title === (title || topic));
    const fallbackSource = currentItem && currentItem.title.includes('字典') ? [
      {
        q: '下面哪一种对象可以直接作为 Python 字典的键？',
        options: ['列表 [1, 2]', '字典 {"a": 1}', '元组 (1, 2)', '集合 {1, 2}'],
        answer: 2,
      },
      {
        q: '为什么列表不能作为 Python 字典的键？',
        options: ['列表没有元素', '列表是可变对象，不能稳定哈希', '列表只能保存字符串', '列表不能被遍历'],
        answer: 1,
      },
      {
        q: '执行代码 d = {(1, 2): "ok"} 后，哪条语句可以取得字符串 "ok"？',
        options: ['d[1, 2]', 'd[[1, 2]]', 'd[(1, 2)]', 'd[{1, 2}]'],
        answer: 2,
      },
      {
        q: '关于 Python 字典键的说法，正确的是哪一项？',
        options: ['键可以重复并同时保留', '键必须是可哈希对象', '键只能是字符串', '键必须是整数'],
        answer: 1,
      },
      {
        q: '下列哪个元组不能作为字典的键？',
        options: ['(1, 2)', '("a", 3)', '([1, 2], 3)', '(True, None)'],
        answer: 2,
      },
    ] : currentItem ? [
      {
        q: `${currentItem.title}：以下说法中最准确的是？`,
        options: ['应依据该知识点的语法规则和实际代码判断', '任何写法都可以', '只看变量名称即可判断', '该知识点与 Python 无关'],
        answer: 0,
      },
      {
        q: `${currentItem.title}：在实际编程中，应优先采用哪种验证方式？`,
        options: ['编写最小可运行示例并观察结果', '只凭感觉判断', '忽略解释器报错', '删除相关代码'],
        answer: 0,
      },
      {
        q: `${currentItem.title}：如果代码行为与预期不一致，首先应该怎么做？`,
        options: ['检查对象类型、语法规则和运行结果', '立即重装操作系统', '随机修改全部代码', '忽略问题'],
        answer: 0,
      },
    ] : [];
    const fallback = currentItem ? fallbackSource.map((item, index) => ({
      id: `fallback-${currentItem.id}-${index}`,
      topic: title || topic,
      type: 'single_choice',
      difficulty: currentItem.difficulty <= 2 ? 'basic' : currentItem.difficulty <= 3 ? 'intermediate' : 'advanced',
      q: item.q,
      options: item.options,
      answer: item.answer,
      explain: `本题只考查“${currentItem.title}”，请结合对应讲义和实际代码理解。`,
      source: { title: currentItem.source, category: topic },
    } as QuizQuestion)) : [];
    if (fallback.length > 0) {
      const cachedFallback = fallback.map((question, index) => ({
        ...question,
        topic: title || topic,
        id: `${question.id || 'fallback'}-${encodeURIComponent(title || topic)}-${index}`,
      }));
      setGeneratedQuestions(cachedFallback);
      window.localStorage.setItem(cacheKey, JSON.stringify(cachedFallback));
    } else {
      setGeneratedQuestions(null);
    }
    setLoadingQuiz(false);
  };

  // ========== 重练错题 ==========
  const handleRetrySimilar = async (wrongId: number, topic: string) => {
    const firstItem = TOPIC_QUESTIONS[topic]?.[0];
    if (firstItem) {
      handlePractice(topic, 'intermediate', firstItem.title, firstItem.source);
    }
  };

  // ========== 处理答题 ==========
  const handleSelect = (idx: number) => {
    if (showAnswer || !q?.options?.length) return;
    setSelected(idx);
    setShowAnswer(true);
    const isCorrect = idx === q.answer;
    if (isCorrect) {
      setScore(s => s + 1);
      setQuestionResults(prev => ({ ...prev, [currentQ]: 'correct' }));
    } else {
      setQuestionResults(prev => ({ ...prev, [currentQ]: 'wrong' }));
      void api.createNote({
        title: `错题：${(q as any).title || q.q || 'Python 数据分析练习'}`,
        content: JSON.stringify({ type: 'single_choice', question: q.q || (q as any).title, options: q.options || (q as any).choices || (q as any).options_list || [], selected: idx, answer: q.answer ?? (q as any).correct_index ?? 0, explanation: q.explain || (q as any).explanation || '请回顾本题涉及的 Python 数据分析知识点。' }),
        category: 'wrong_question',
      }).catch(() => {});
    }
    // Track for dynamic profile
    const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${API}/api/quiz/submit`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({user_id: user?.id || 1, topic: `${practiceTopic || '综合练习'}|${practiceTitle || ''}`, score: isCorrect ? 1 : 0, total: 1})
    }).then(response => {
      if (!response.ok) throw new Error(`保存答题记录失败：${response.status}`);
      const submittedTopic = q?.topic || practiceTopic || '综合练习';
      setRealAttempts(value => value + 1);
      setTopicProgress(previous => {
        const current = previous[submittedTopic] || { attempts: 0, correct: 0, total: 0 };
        return { ...previous, [submittedTopic]: {
          attempts: Number(current.attempts || 0) + 1,
          correct: Number(current.correct || 0) + (isCorrect ? 1 : 0),
          total: Number(current.total || 0) + 1,
        } };
      });
    }).catch(error => console.error(error));
  };

  const handleNext = () => {
    if (currentQ + 1 < questions.length) {
      setCurrentQ(c => c + 1);
      setSelected(null);
      setShowAnswer(false);
      setDraftAnswer('');
    } else {
      setTimerActive(false);
      setDone(true);
    }
  };

  const handlePrevious = () => {
    if (currentQ <= 0) return;
    setCurrentQ(current => current - 1);
    setSelected(null);
    setShowAnswer(false);
    setDraftAnswer('');
  };

  const handleBack = () => {
    setTimerActive(false);
    setPracticeTopic(null);
    setPracticeTitle('');
    setPracticeDifficulty('adaptive');
    setGeneratedQuestions(null);
    setDone(false);
    setTimeSpent(0);
    setQuestionResults({});
  };

  const displayTitle = practiceTitle || practiceTopic || '';
  const questions = practiceTopic ? (generatedQuestions || []) : [];
  const q = questions[currentQ];

  // 错题状态
  const getWrongStatus = (w: typeof INITIAL_WRONG_QUESTIONS[0]) => {
    if (!w.inWrongList) {
      return { label: '✅ 已掌握', color: 'bg-green-100 text-green-700', borderColor: 'border-green-500', bgColor: 'bg-green-50' };
    }
    if (w.consecutiveCorrect >= 2) {
      return { label: `🔥 ${w.consecutiveCorrect}/3`, color: 'bg-orange-100 text-orange-700', borderColor: 'border-orange-400', bgColor: 'bg-orange-50' };
    }
    if (w.consecutiveCorrect > 0) {
      return { label: `${w.consecutiveCorrect}/3`, color: 'bg-blue-100 text-blue-700', borderColor: 'border-blue-400', bgColor: 'bg-blue-50' };
    }
    return { label: '🔴 待攻克', color: 'bg-red-100 text-red-700', borderColor: 'border-red-500', bgColor: 'bg-red-50' };
  };

  const renderStars = (diff: number) => '⭐'.repeat(diff) + '☆'.repeat(5 - diff);
  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  // ========== 练习模式渲染 ==========
  if (practiceTopic) {
    return (
      <div className="p-6 lg:p-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-4">
          <button onClick={handleBack} className="flex items-center gap-1.5 text-sm text-[var(--lm-text-secondary)] hover:text-[#4f46e5] transition-colors">
            <ArrowLeft className="w-4 h-4" /> 返回题库
          </button>
          <div className="flex items-center gap-4 text-sm text-[var(--lm-text-tertiary)]">
            <span className="flex items-center gap-1"><Timer className="w-4 h-4" /> {formatTime(timeSpent)}</span>
            <span className="font-medium text-[#1a1a2e]">{currentQ + 1} / {questions.length}</span>
          </div>
        </div>

        {loadingQuiz ? (
          <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-12 text-center">
            <div className="animate-spin text-4xl mb-4">⏳</div>
            <h2 className="text-xl font-bold mb-2">加载题目中...</h2>
          </div>
        ) : done ? (
          <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-12 text-center">
            <div className="text-5xl mb-4">{score === questions.length ? '🎉' : score >= questions.length / 2 ? '👍' : '📚'}</div>
            <h2 className="text-2xl font-bold mb-2">练习完成！</h2>
            <div className="flex items-center justify-center gap-6 text-sm text-[var(--lm-text-secondary)] mb-4">
              <span>✅ 正确 <strong className="text-green-600">{score}</strong> 题</span>
              <span>📝 共 <strong>{questions.length}</strong> 题</span>
              <span>⏱ 用时 <strong>{formatTime(timeSpent)}</strong></span>
            </div>
            <div className="h-3 bg-[var(--lm-brand-light)] rounded-full overflow-hidden mb-4 max-w-xs mx-auto">
              <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all" style={{ width: (score / questions.length) * 100 + '%' }} />
            </div>
            <p className="text-sm font-medium text-[#1a1a2e] mb-6">
              正确率 {Math.round((score / questions.length) * 100)}%
              {score === questions.length && ' 🏆 完美！'}
              {score >= questions.length * 0.8 && score < questions.length && ' 🌟 优秀！'}
              {score >= questions.length * 0.5 && score < questions.length * 0.8 && ' 💪 继续加油！'}
              {score < questions.length * 0.5 && ' 📖 需要更多练习！'}
            </p>
            <div className="flex gap-3 justify-center flex-wrap">
              <button onClick={() => handlePractice(practiceTopic || 'Python基础', practiceDifficulty, displayTitle)} className="px-6 py-2.5 rounded-xl bg-[#4f46e5] text-white font-medium hover:bg-[#4338ca] transition-all">
                <RefreshCw className="w-4 h-4 inline mr-1.5" /> 重新练习
              </button>
              <button onClick={handleBack} className="px-6 py-2.5 rounded-xl border border-[var(--lm-border)] font-medium">返回题库</button>
            </div>
          </div>
        ) : !q ? (
          <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-12 text-center">
            <h2 className="text-xl font-bold mb-2">暂无可用题目</h2>
            <p className="text-sm text-[var(--lm-text-secondary)] mb-6">请返回题库选择其他知识点。</p>
            <button onClick={handleBack} className="px-6 py-2.5 rounded-xl border border-[var(--lm-border)] font-medium">返回题库</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_240px] gap-6 items-stretch">
            <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-6 md:p-10">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 font-medium">📚 {q.topic || practiceTopic || displayTitle}</span>
                  <span className="text-xs px-2.5 py-1 rounded-full bg-amber-50 text-amber-700">{'⭐'.repeat(q.difficulty === 'basic' ? 1 : q.difficulty === 'intermediate' ? 3 : 5) + '☆'.repeat(5 - (q.difficulty === 'basic' ? 1 : q.difficulty === 'intermediate' ? 3 : 5))}</span>
                  <span className="text-xs px-2.5 py-1 rounded-full bg-gray-100 text-gray-600">{q.type === 'single_choice' ? '📝 选择题' : q.type === 'debugging' ? '🔧 排错题' : '✏️ 简答题'}</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-[var(--lm-text-tertiary)]">
                  <span>进度 {Math.round(((currentQ) / questions.length) * 100)}%</span>
                  <span className="font-medium text-[#1a1a2e]">第 {currentQ + 1} 题</span>
                </div>
              </div>
              <div className="flex gap-1 mb-5">
                {questions.map((_, i) => (
                  <div key={i} className={`flex-1 h-1.5 rounded-full transition-all ${i < currentQ ? 'bg-green-500' : i === currentQ ? 'bg-indigo-500' : 'bg-[var(--lm-border)]'}`} />
                ))}
              </div>
              <div className="mb-5">
                <h3 className="text-lg font-semibold text-[#1a1a2e] leading-relaxed">{q.q}</h3>
              </div>
              {q.options && q.options.length > 0 ? (
                <div className="space-y-2.5 mb-5">
                  {q.options.map((opt, i) => {
                    let cls = 'border-[var(--lm-border)] hover:border-indigo-400 hover:bg-indigo-50/50';
                    if (showAnswer) {
                      if (i === q.answer) cls = 'border-green-500 bg-green-50';
                      else if (i === selected && i !== q.answer) cls = 'border-red-500 bg-red-50';
                      else cls = 'border-[var(--lm-border)] opacity-50';
                    } else if (i === selected) cls = 'border-indigo-500 bg-indigo-50';
                    return (
                      <button key={i} onClick={() => handleSelect(i)} className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl border-2 text-left text-sm font-medium transition-all ${cls}`}>
                        <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 flex-shrink-0 ${showAnswer && i === q.answer ? 'bg-green-500 text-white border-green-500' : showAnswer && i === selected ? 'bg-red-500 text-white border-red-500' : i === selected ? 'bg-indigo-500 text-white border-indigo-500' : 'border-[var(--lm-border)] text-[var(--lm-text-tertiary)]'}`}>
                          {showAnswer && i === q.answer ? '✓' : showAnswer && i === selected ? '✗' : String.fromCharCode(65 + i)}
                        </span>
                        {opt}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="mb-5">
                  <textarea value={draftAnswer} onChange={e => setDraftAnswer(e.target.value)} className="w-full min-h-[120px] rounded-xl border border-[var(--lm-border)] bg-transparent px-4 py-3 text-sm outline-none focus:border-indigo-500" placeholder="写下你的分析..." />
                </div>
              )}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <button onClick={handlePrevious} disabled={currentQ === 0} className="py-3 rounded-xl border border-[var(--lm-border)] font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50">← 上一题</button>
                <button onClick={handleNext} className="py-3 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700">{currentQ + 1 < questions.length ? '下一题 →' : '完成练习'}</button>
              </div>
              {!q.options?.length && !showAnswer && (
                <button onClick={() => setShowAnswer(true)} className="w-full py-3 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-all">提交并查看参考答案</button>
              )}
              {showAnswer && (
                <div className="space-y-3">
                  <div className={`p-4 rounded-xl text-sm ${selected === q.answer ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                    <div className="flex items-center gap-2 font-semibold mb-1">
                      {selected === q.answer ? <CheckCircle className="w-4 h-4 text-green-600" /> : <XCircle className="w-4 h-4 text-red-600" />}
                      <span className={selected === q.answer ? 'text-green-700' : 'text-red-700'}>{selected === q.answer ? '🎉 回答正确！' : '😅 回答错误'}</span>
                      {selected === q.answer && <span className="text-xs text-green-500 ml-auto">+1 掌握度</span>}
                    </div>
                    <p className="text-[var(--lm-text-secondary)] leading-relaxed">{q.explain || '解析：请结合课程内容理解。'}</p>
                    {q.source && <p className="text-xs text-[var(--lm-text-tertiary)] mt-2">📖 来源：{q.source.title}</p>}
                  </div>
                  <details className="mt-2">
                    <summary className="text-xs text-[var(--lm-text-tertiary)] cursor-pointer hover:text-[#4f46e5] transition-colors flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5" /> 📖 知识点回顾
                    </summary>
                    <div className="mt-2 p-3 rounded-lg bg-indigo-50/50 border border-indigo-100 text-xs text-[var(--lm-text-secondary)] leading-relaxed">
                      <p><strong className="text-indigo-700">核心概念：</strong>{q.topic || displayTitle} 是 Python 编程中的重要知识点。建议复习相关讲义内容加深理解。</p>
                      <p className="mt-1 text-[var(--lm-text-tertiary)]">💡 连续答对 3 道同类题可提升掌握度</p>
                    </div>
                  </details>
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    <button onClick={handlePrevious} disabled={currentQ === 0} className="py-3 rounded-xl border border-[var(--lm-border)] font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50">← 上一题</button>
                    <button onClick={handleNext} className="py-3 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition-all">{currentQ + 1 < questions.length ? '下一题 →' : '完成练习'}</button>
                  </div>
                </div>
              )}
            </div>
            <div className="hidden lg:block h-full">
              <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-5 sticky top-6 flex flex-col h-full">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-semibold text-[#1a1a2e]">📋 答题卡</h4>
                  <span className="text-xs text-[var(--lm-text-tertiary)]">{Math.round(((currentQ + (selected !== null ? 1 : 0)) / questions.length) * 100)}%</span>
                </div>
                <div className="grid grid-cols-5 gap-2">
                  {questions.map((_, idx) => {
                    let bg = 'bg-gray-100 text-gray-500', border = 'border-gray-200';
                    const result = questionResults[idx];
                    if (result === 'correct') { bg = 'bg-green-500 text-white'; border = 'border-green-500'; }
                    else if (result === 'wrong') { bg = 'bg-red-500 text-white'; border = 'border-red-500'; }
                    else if (idx === currentQ) { bg = 'bg-indigo-500 text-white'; border = 'border-indigo-500 ring-2 ring-indigo-200'; }
                    return (
                      <button key={idx} onClick={() => { if (idx < questions.length) { setCurrentQ(idx); setSelected(null); setShowAnswer(false); setDraftAnswer(''); } }} className={`w-full aspect-square rounded-lg border-2 text-xs font-medium transition-all ${bg} ${border} hover:scale-105`}>
                        {idx + 1}
                      </button>
                    );
                  })}
                </div>
                <div className="mt-auto pt-3 border-t border-[var(--lm-border)] space-y-1.5 text-xs">
                  <div className="flex items-center justify-between"><span className="text-[var(--lm-text-tertiary)]">✅ 已答对</span><span className="font-medium text-green-600">{score}</span></div>
                  <div className="flex items-center justify-between"><span className="text-[var(--lm-text-tertiary)]">❌ 已答错</span><span className="font-medium text-red-600">{Object.values(questionResults).filter(r => r === 'wrong').length}</span></div>
                  <div className="flex items-center justify-between"><span className="text-[var(--lm-text-tertiary)]">⏳ 剩余</span><span className="font-medium text-[var(--lm-text-secondary)]">{questions.length - Object.values(questionResults).filter(r => r !== null).length}</span></div>
                  <div className="flex items-center justify-between pt-1 border-t border-[var(--lm-border)]"><span className="text-[var(--lm-text-tertiary)]">🎯 正确率</span><span className="font-bold text-[#1a1a2e]">{Object.values(questionResults).filter(r => r !== null).length > 0 ? Math.round((score / Object.values(questionResults).filter(r => r !== null).length) * 100) : 0}%</span></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ========== 主视图 ==========
  return (
    <div className="p-6 lg:p-8 max-w-7xl">
      <div className="text-xs text-[var(--lm-text-tertiary)] mb-2">首页 / 题库练习</div>
      <div className="flex flex-wrap justify-between items-start gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold">📝 题库练习</h1>
          <p className="text-sm text-[var(--lm-text-secondary)] mt-1">静态考点题库 · 每个考点 3 道题</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setTab('wrong')} className="px-4 py-2 rounded-lg border border-[var(--lm-border)] text-sm">错题本 ({activeWrong.length}题)</button>
          <button onClick={() => handlePractice('Python基础', 'adaptive', 'AI 智能出题')} className="px-4 py-2 rounded-lg bg-[#4f46e5] text-white text-sm">+ 随机练习</button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { icon: BookOpen, value: Object.values(TOPIC_QUESTIONS).filter(questions => questions.length > 0).length, suffix: '', label: '考点分类' },
          { icon: CheckCircle, value: avgMastery, suffix: '%', label: '综合掌握度' },
          { icon: Flame, value: realAttempts > 0 ? 1 : 0, suffix: '天', label: '连续打卡' },
          { icon: Clock, value: 0, suffix: 'min', label: '平均用时' },
        ].map((s, i) => (
          <div key={i} className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-4 text-center">
            <div className="text-2xl font-bold">{s.value}<span className="text-base font-normal text-[var(--lm-text-tertiary)]">{s.suffix}</span></div>
            <div className="text-sm text-[var(--lm-text-secondary)]">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Tab */}
      <div className="flex gap-1 bg-[var(--lm-brand-light)] p-1 rounded-xl mb-6 w-fit flex-wrap">
        {[
          { id: 'topic', label: '按知识点' },
          { id: 'diff', label: '按难度' },
          { id: 'wrong', label: '错题重练', badge: String(activeWrong.length) },
          { id: 'mock', label: '模拟考试' },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === t.id ? 'bg-white shadow-sm text-[var(--lm-text)]' : 'text-[var(--lm-text-secondary)]'}`}>
            {t.label}
            {t.badge && parseInt(t.badge) > 0 && <span className="ml-1.5 text-xs bg-red-500 text-white rounded-full px-1.5 py-0.5">{t.badge}</span>}
          </button>
        ))}
      </div>

      {/* ====== 按知识点 ====== */}
      {tab === 'topic' && (
        <div>
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <div className="flex gap-1.5">
              {[
                { value: 'all', label: '全部' },
                { value: 'mastered', label: '🌟 已掌握' },
                { value: 'learning', label: '📖 学习中' },
                { value: 'weak', label: '⚠️ 需加强' },
              ].map(option => (
                <button key={option.value} onClick={() => setFilterStatus(option.value as any)} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${filterStatus === option.value ? 'bg-indigo-50 text-indigo-600 border-indigo-200' : 'bg-transparent text-[var(--lm-text-tertiary)] border-transparent hover:bg-gray-100'}`}>
                  {option.label}
                </button>
              ))}
            </div>
            <div className="relative flex-1 min-w-[180px] ml-auto">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--lm-text-tertiary)]" />
              <input type="text" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder="搜索知识点..." className="w-full pl-9 pr-4 py-1.5 rounded-lg border border-[var(--lm-border)] bg-[var(--lm-surface)] text-sm outline-none focus:border-indigo-400" />
            </div>
          </div>

          {selectedQuestions.length > 0 && (
            <div className="flex items-center gap-3 mb-4 p-3 bg-indigo-50 rounded-xl border border-indigo-200">
              <span className="text-sm font-medium text-indigo-700">已选 {selectedQuestions.length} 题</span>
              <button onClick={() => setSelectedQuestions([])} className="text-xs text-indigo-500 hover:text-indigo-700">清空</button>
              <button onClick={handlePracticeSelected} className="ml-auto px-4 py-1.5 rounded-lg bg-[#4f46e5] text-white text-sm font-medium hover:bg-[#4338ca] transition-all">开始练习 →</button>
            </div>
          )}

          <div className="space-y-3">
          {availableTopics.map(topicMeta => {
              const questions = TOPIC_QUESTIONS[topicMeta.id] || [];
              const avgMastery = accountMastery(topicMeta.name, 0);
              const isExpanded = expandedTopics.has(topicMeta.id);
              const weak = avgMastery < 50;
              const status = weak ? 'weak' : avgMastery >= 80 ? 'mastered' : 'learning';
              const statusConfig = {
                mastered: { label: '已掌握', color: 'text-green-600', bg: 'bg-green-50' },
                learning: { label: '学习中', color: 'text-amber-600', bg: 'bg-amber-50' },
                weak: { label: '需加强', color: 'text-red-600', bg: 'bg-red-50' },
              }[status];

              return (
                <div key={topicMeta.id} className={`bg-[var(--lm-surface)] rounded-2xl border-2 overflow-hidden transition-all ${weak ? 'border-red-200/70' : 'border-[var(--lm-border)]'}`}>
                  <div onClick={() => toggleTopic(topicMeta.id)} className="flex items-center gap-4 px-5 py-3 cursor-pointer hover:bg-indigo-50/30 transition-all">
                    <div className="flex-shrink-0"><CircularProgress percentage={Math.round(avgMastery)} size={44} strokeWidth={4} /></div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{topicMeta.icon}</span>
                        <span className="font-semibold text-[#1a1a2e]">{topicMeta.name}</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full ${statusConfig.bg} ${statusConfig.color}`}>{statusConfig.label}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-[var(--lm-text-tertiary)]">
                        <span>📝 {questions.length} 考点</span>
                        <span>🎯 掌握度 {Math.round(avgMastery)}%</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[var(--lm-text-tertiary)]">{isExpanded ? '收起' : '展开'}</span>
                      {isExpanded ? <ChevronUp className="w-4 h-4 text-[var(--lm-text-tertiary)]" /> : <ChevronDown className="w-4 h-4 text-[var(--lm-text-tertiary)]" />}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-t border-[var(--lm-border)] px-4 py-3">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-[var(--lm-border)]">
                            <th className="text-left py-2 pr-2 w-8">
                              <input type="checkbox" checked={questions.every(q => selectedQuestions.includes(q.id))} onChange={() => {
                                const allIds = questions.map(q => q.id);
                                const allSelected = allIds.every(id => selectedQuestions.includes(id));
                                if (allSelected) setSelectedQuestions(prev => prev.filter(id => !allIds.includes(id)));
                                else setSelectedQuestions(prev => [...prev, ...allIds.filter(id => !prev.includes(id))]);
                              }} className="rounded border-[var(--lm-border)]" />
                            </th>
                            <th className="text-left py-2 text-xs font-medium text-[var(--lm-text-tertiary)]">考点</th>
                            <th className="text-left py-2 text-xs font-medium text-[var(--lm-text-tertiary)]">类型</th>
                            <th className="text-left py-2 text-xs font-medium text-[var(--lm-text-tertiary)]">难度</th>
                            <th className="text-left py-2 text-xs font-medium text-[var(--lm-text-tertiary)]">掌握度</th>
                            <th className="text-left py-2 text-xs font-medium text-[var(--lm-text-tertiary)]">来源</th>
                            <th className="text-right py-2 text-xs font-medium text-[var(--lm-text-tertiary)]">操作</th>
                          </tr>
                        </thead>
                        <tbody>
                          {questions.map(q => {
                            const isSelected = selectedQuestions.includes(q.id);
                            const liveMastery = questionMastery(topicMeta.name, q.title, q.mastery);
                            return (
                              <tr key={q.id} className="border-b border-[var(--lm-border)] last:border-0 hover:bg-indigo-50/20 transition-all">
                                <td className="py-2 pr-2">
                                  <input type="checkbox" checked={isSelected} onChange={() => toggleQuestionSelection(q.id)} className="rounded border-[var(--lm-border)]" />
                                </td>
                                <td className="py-2 text-[#1a1a2e] font-medium">{q.title}</td>
                                <td className="py-2 text-xs text-[var(--lm-text-tertiary)]">{q.type}</td>
                                <td className="py-2 text-xs text-amber-500">{renderStars(q.difficulty)}</td>
                                <td className="py-2">
                                  <div className="flex items-center gap-1.5">
                                    <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                      <div className={`h-full rounded-full ${liveMastery >= 80 ? 'bg-green-500' : liveMastery >= 50 ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${liveMastery}%` }} />
                                    </div>
                                    <span className="text-xs text-[var(--lm-text-tertiary)]">{liveMastery}%</span>
                                  </div>
                                </td>
                                <td className="py-2 text-xs text-[var(--lm-text-tertiary)]">{q.source}</td>
                                <td className="py-2 text-right">
                                  <button onClick={() => handlePractice(topicMeta.id, 'intermediate', q.title, q.source)} className="text-xs px-3 py-1 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors">
                                    开始练习
                                  </button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          {availableTopics.length === 0 && (
            <div className="text-center py-12 text-[var(--lm-text-tertiary)]"><div className="text-4xl mb-3">🔍</div><p className="text-sm">没有匹配的知识点</p></div>
          )}
        </div>
      )}

      {/* ====== 按难度 ====== */}
      {tab === 'diff' && (
        <div className="grid sm:grid-cols-2 gap-4">
          {DIFFICULTY_LEVELS.map((d, i) => (
            <div key={i} className={`bg-[var(--lm-surface)] rounded-2xl border p-6 ${d.unlocked ? 'border-[var(--lm-border)]' : 'border-2 border-dashed border-[var(--lm-border)] opacity-70'}`}>
              <h4 className="font-semibold mb-2">{d.stars} {d.label}</h4>
              <p className="text-sm text-[var(--lm-text-secondary)] mb-3">{d.desc}</p>
              <div className="flex gap-2 flex-wrap mb-3">
                <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--lm-brand-light)] text-[#4f46e5]">{d.count}题</span>
                {d.acc > 0 && <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--lm-success-bg)] text-[#16a34a]">正确率 {d.acc}%</span>}
              </div>
              <div className="h-1.5 bg-[var(--lm-brand-light)] rounded-full overflow-hidden mb-3"><div className="h-full rounded-full bg-[#4f46e5]" style={{ width: Math.max(5, d.acc) + '%' }} /></div>
              <button onClick={() => d.unlocked && handlePractice('Python基础', d.difficulty, d.label)} disabled={!d.unlocked} className={`w-full py-2 rounded-lg text-sm font-medium ${d.unlocked ? 'bg-[#4f46e5] text-white hover:bg-[#4338ca]' : 'bg-gray-200 text-gray-400 cursor-not-allowed'}`}>
                {d.unlocked ? '开始练习 →' : '暂未解锁'}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ====== 错题重练 ====== */}
      {tab === 'wrong' && (
        <div className="space-y-3">
          <div className="flex justify-between items-center mb-2">
            <h4 className="font-semibold">待重练错题（{activeWrong.length}题）{masteredWrong.length > 0 && <span className="text-xs text-green-600 font-normal ml-2">✅ {masteredWrong.length} 题已掌握</span>}</h4>
            <button onClick={() => { if (activeWrong.length === 0) return; const topics = [...new Set(activeWrong.map(w => w.topic))]; handlePractice(topics[0], 'intermediate', '错题重练'); }} className="px-4 py-2 rounded-lg bg-[#4f46e5] text-white text-sm">全部重练</button>
          </div>
          {activeWrong.length === 0 ? (
            <div className="bg-green-50 rounded-2xl border border-green-200 p-8 text-center"><div className="text-4xl mb-3">🎉</div><h4 className="text-lg font-semibold text-green-700">错题本已清空！</h4><p className="text-sm text-green-600">所有错题已连续作对3次，全部掌握！</p></div>
          ) : (
            activeWrong.map(w => {
              const status = getWrongStatus(w);
              const isExpanded = expandedWrongId === w.id;
              const retryResult = retryResults[w.id];
              return (
                <div key={w.id} className={`p-4 rounded-xl border-l-4 ${status.borderColor} ${status.bgColor} border border-[var(--lm-border)] transition-all`}>
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${w.wrongCount >= 3 ? 'bg-red-200 text-red-700' : 'bg-amber-200 text-amber-700'}`}>错{w.wrongCount}次</span>
                    <span className="text-xs px-1.5 py-0.5 rounded-full bg-purple-100 text-purple-700">{w.topic}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded-full ${status.color}`}>{status.label}</span>
                    {retryResult === 'correct' && <span className="text-xs px-1.5 py-0.5 rounded-full bg-green-100 text-green-700">✅ 上次重练通过</span>}
                    {retryResult === 'wrong' && <span className="text-xs px-1.5 py-0.5 rounded-full bg-red-100 text-red-700">❌ 上次重练未通过</span>}
                    <span className="text-sm font-medium flex-1">{w.q}</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs">
                    <span className="text-green-600">正解：{w.correct}</span>
                    <span className="text-red-600">你选：{w.yours}</span>
                    <button onClick={() => setExpandedWrongId(isExpanded ? null : w.id)} className="text-[#4f46e5] cursor-pointer flex items-center gap-0.5">{isExpanded ? '收起解析' : '查看解析'} {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}</button>
                  </div>
                  {isExpanded && (
                    <div className="mt-3 p-3 rounded-lg bg-white/70 text-sm text-[var(--lm-text-secondary)]">
                      <p><strong>解析：</strong>{w.explain}</p>
                      <p className="text-xs text-[var(--lm-text-tertiary)] mt-1.5">💡 连续答对 3 次即可移出错题本</p>
                    </div>
                  )}
                  <div className="mt-3 pt-3 border-t border-[var(--lm-border)]/50">
                    <button onClick={() => { const firstItem = TOPIC_QUESTIONS[w.topic]?.[0]; if (firstItem) handlePractice(w.topic, 'intermediate', firstItem.title, firstItem.source); }} className="px-4 py-2 rounded-lg bg-[#4f46e5] text-white text-sm font-medium hover:bg-[#4338ca] transition-all flex items-center gap-1.5">
                      <RefreshCw className="w-3.5 h-3.5" /> 开始重练（相似题）
                    </button>
                    <span className="ml-3 text-xs text-[var(--lm-text-tertiary)]">AI 生成 5 道「{w.topic}」相似题</span>
                  </div>
                </div>
              );
            })
          )}
          {masteredWrong.length > 0 && (
            <div className="mt-4">
              <details className="cursor-pointer">
                <summary className="text-sm text-[var(--lm-text-tertiary)] hover:text-[#4f46e5]">✅ 已掌握的错题（{masteredWrong.length}题）</summary>
                <div className="mt-2 space-y-2">
                  {masteredWrong.map(w => (
                    <div key={w.id} className="p-3 rounded-xl bg-green-50 border border-green-200 text-sm text-[var(--lm-text-secondary)]">
                      <span className="font-medium">{w.q}</span>
                      <span className="ml-2 text-xs text-green-600">✅ 已连续作对3次，已掌握</span>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}
        </div>
      )}

      {/* ====== 模拟考试 ====== */}
      {tab === 'mock' && (
        <div className="grid sm:grid-cols-2 gap-4">
          {MOCK_EXAMS.map((m, i) => (
            <div key={i} className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] p-6">
              <h4 className="font-semibold mb-1">{m.title}</h4>
              <p className="text-sm text-[var(--lm-text-secondary)] mb-3">{m.desc}</p>
              <div className="flex gap-1.5 flex-wrap mb-4">
                {m.tags.map((tag, j) => (
                  <span key={j} className={`text-xs px-2 py-0.5 rounded-full ${m.accent ? 'bg-red-100 text-red-600' : 'bg-[var(--lm-brand-light)] text-[#4f46e5]'}`}>{tag}</span>
                ))}
              </div>
              <button onClick={() => { const firstItem = TOPIC_QUESTIONS[m.topic === '综合练习' ? 'Python基础' : m.topic]?.[0]; if (firstItem) handlePractice(m.topic === '综合练习' ? 'Python基础' : m.topic, m.difficulty, firstItem.title, firstItem.source); }} className={`w-full py-2 rounded-lg text-sm font-medium ${m.done ? 'bg-gray-100 text-gray-700 hover:bg-gray-200' : 'bg-[#4f46e5] text-white hover:bg-[#4338ca]'}`}>
                {m.done ? '查看今日练习' : '开始考试'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
