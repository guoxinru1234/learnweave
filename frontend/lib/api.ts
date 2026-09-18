/** LearnWeave API Client */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type ProfileVector = [number, number, number, number, number, number];

export type RecommendedLecture = {
  lecture_id: number;
  title: string;
  reason: string;
  priority: 'high' | 'medium';
};

export type RecommendResponse = {
  recommendations: RecommendedLecture[];
  summary: string;
};

export type AgentSource = {
  asset_id?: string;
  title: string;
  category: string;
  source_path?: string;
  topics?: string[];
  score?: number;
};

export type GeneratedResource = {
  type: string;
  title: string;
  content?: string | string[];
  root?: string;
  children?: { label: string; type: string; topics?: string[] }[];
  language?: string;
};

export type QuizQuestion = {
  id: string;
  topic?: string;
  type: string;
  difficulty: string;
  q: string;
  options?: string[];
  answer?: number;
  explain?: string;
  reference?: string;
  source?: AgentSource;
};

export type TutorAnswer = {
  question: string;
  topic?: string;
  answer: string;
  sources: AgentSource[];
  related_labs: AgentSource[];
  follow_up: string[];
};

export type LabAsset = {
  id: string;
  title: string;
  category: string;
  source_path: string;
  suffix: string;
  topics: string[];
  lecture_ids: number[];
  text_chars: number;
  chunk_count: number;
};

export type LabDetail = LabAsset & {
  chunks: { id: string; chunk_index: number; title: string; text: string }[];
  content: string;
  content_preview: string;
};

export type DatasetAsset = {
  id: string;
  title: string;
  source_path: string;
  suffix: string;
  topics: string[];
  text_chars: number;
};

export type KnowledgePoint = {
  id: string;
  name: string;
  lecture_ids: number[];
  asset_count: number;
};

export type AgentRunResult = {
  profile: number[];
  learning_path: {
    path: {
      module?: string;
      lectures?: number[];
      estimated_hours?: number;
      focus?: string;
      labs?: Record<string, unknown>[];
      focus_area?: string;
      action?: string;
      reason?: string;
    }[];
    profile_based: boolean;
    lab_integrated: boolean;
  };
  resources: { topic: string; resources: GeneratedResource[]; sources: AgentSource[] };
  tutoring: TutorAnswer;
  quiz: { topic: string; difficulty: string; questions: QuizQuestion[]; sources: AgentSource[] };
  assessment: {
    mastery: number;
    weak_points: { name: string; score: number; action: string }[];
    knowledge_points: { name?: string; topic?: string; mastery?: number }[];
    recommendations: string[];
  };
  focus_topic: string;
  current_phase: string;
  done: boolean;
};

async function fetchAPI(path: string, options?: RequestInit) {
  const token = typeof window !== 'undefined' ? sessionStorage.getItem('auth_token') : null;
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
      ...options,
      cache: 'no-store',
    });
  } catch {
    throw new Error(`无法连接后端服务 ${API_BASE}，请确认后端已启动`);
  }
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  // Knowledge
  getLectures: () => fetchAPI('/api/knowledge/lectures'),
  getLecture: (id: string) => fetchAPI(`/api/knowledge/lecture/${id}`),
  searchKnowledge: (q: string) => fetchAPI(`/api/knowledge/search?q=${encodeURIComponent(q)}`),
  getKnowledgeAssets: () => fetchAPI('/api/knowledge/assets'),

  // Profile
  getProfile: () => fetchAPI('/api/profile'),
  sendProfileMessage: (message: string) =>
    fetchAPI('/api/profile/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
  recommendCourses: (weakDimensions: [string, number][], strongDimensions: [string, number][]) =>
    fetchAPI('/api/profile/recommend', {
      method: 'POST',
      body: JSON.stringify({ weak_dimensions: weakDimensions, strong_dimensions: strongDimensions }),
    }),

  // Chat
  sendMessage: (messages: { role: string; content: string }[]) =>
    fetchAPI('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ messages }),
    }),

  // -------------------- 新增：AI 对话历史 --------------------
  getChatSessions: () =>
    fetchAPI('/api/chat/history/sessions/list'),

  getChatHistory: (sessionId: string) =>
    fetchAPI(`/api/chat/history/${sessionId}`),

  deleteChatSession: (sessionId: string) =>
    fetchAPI(`/api/chat/history/${sessionId}`, {
      method: 'DELETE',
    }),

  renameChatSession: (sessionId: string, title: string) =>
    fetchAPI(`/api/chat/history/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }),

  // Quiz
  getQuizRecommend: (topic?: string) =>
    fetchAPI(`/api/quiz/recommend${topic ? `?topic=${encodeURIComponent(topic)}` : ''}`),

  // ========== 修改这一行：增加 lecture 参数 ==========
  generateQuiz: (topic: string, count = 4, profile?: number[], difficulty = 'adaptive', lecture?: string) =>
    fetchAPI('/api/generate/quiz', {
      method: 'POST',
      body: JSON.stringify({ topic, count, difficulty, profile, lecture }),
    }) as Promise<{ topic: string; difficulty: string; questions: QuizQuestion[]; sources: AgentSource[] }>,

  // Learning resources
  generateResource: (topic: string, resourceTypes?: string[]) =>
    fetchAPI('/api/generate/resource', {
      method: 'POST',
      body: JSON.stringify({ topic, resource_types: resourceTypes }),
    }) as Promise<{
      topic: string;
      resources: GeneratedResource[];
      sources: AgentSource[];
      task_id: string;
      status: string;
    }>,
  generateTutor: (question: string, topic?: string, history: Array<{ role: string; content: string }> = []) =>
    fetchAPI('/api/generate/tutor', {
      method: 'POST',
      body: JSON.stringify({ question, topic, history }),
    }) as Promise<TutorAnswer>,

  // Labs
  getLabs: (topic?: string, category?: string) =>
    fetchAPI(`/api/labs${topic || category ? `?${new URLSearchParams({ ...(topic ? { topic } : {}), ...(category ? { category } : {}) }).toString()}` : ''}`) as Promise<{ total: number; labs: LabAsset[] }>,
  getLabDetail: (id: string) => fetchAPI(`/api/labs/${encodeURIComponent(id)}`) as Promise<LabDetail>,
  getDatasets: () => fetchAPI('/api/labs/datasets') as Promise<{ total: number; datasets: DatasetAsset[] }>,
  getKnowledgePoints: () => fetchAPI('/api/labs/knowledge-points') as Promise<{ total: number; knowledge_points: KnowledgePoint[] }>,

  // Agents
  getAgentsStatus: () => fetchAPI('/api/agents/status'),
  runAgents: (profile: number[] = [72, 80, 55, 75, 90, 85]) =>
    fetchAPI('/api/agents/run', {
      method: 'POST',
      body: JSON.stringify({ profile }),
    }) as Promise<AgentRunResult>,

  // Assessment
  getAssessmentSummary: () => fetchAPI('/api/assessment/summary'),

  // -------------------- 学习日历 / 打卡系统 --------------------
  getLearningRecords: ({ year, month }: { year: number; month: number }) =>
    fetchAPI(`/learning-records?year=${year}&month=${month}`),
  saveLearningRecord: (data: { date: string; minutes: number; lectures: number; accuracy: number }) =>
    fetchAPI('/learning-records', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // -------------------- 每日计划（Daily Tasks）--------------------
  getDailyTasks: (date: string) =>
    fetchAPI(`/daily-tasks?date=${date}`),
  addDailyTask: (data: { date: string; content: string; category: string }) =>
    fetchAPI('/daily-tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  toggleTask: (taskId: number, isDone: boolean) =>
    fetchAPI(`/daily-tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_done: isDone }),
    }),
  deleteTask: (taskId: number) =>
    fetchAPI(`/daily-tasks/${taskId}`, {
      method: 'DELETE',
    }),

  // -------------------- 笔记系统（Note System）--------------------
  getNotes: (params?: { lecture_id?: number; category?: string; q?: string }) =>
    fetchAPI(`/notes/?${new URLSearchParams(params as any).toString()}`),
  getNote: (noteId: number) =>
    fetchAPI(`/notes/${noteId}`),
  getCategoryStats: () =>
    fetchAPI('/notes/categories/stats'),
  createNote: async (data: { lecture_id?: number; category?: string; title: string; content: string }) => {
    const result = await fetchAPI('/notes/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (typeof window !== 'undefined') window.dispatchEvent(new Event('learnmate-note-created'));
    return result;
  },
  updateNote: (noteId: number, data: { title?: string; content?: string; category?: string }) =>
    fetchAPI(`/notes/${noteId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  deleteNote: (noteId: number) =>
    fetchAPI(`/notes/${noteId}`, {
      method: 'DELETE',
    }),
  exportNotes: (lectureId: number) =>
    fetchAPI(`/notes/export/${lectureId}`),

  // -------------------- 实验批改（Lab Grader）--------------------
  gradeLabCode: (data: { code: string; lab_title: string; task_description?: string }) =>
    fetchAPI('/api/lab-grader/grade', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // -------------------- 多智能体验证 --------------------
  /** 触发生成+审核闭环，返回完整 verification_steps */
  runVerification: (params: {
    course_id: string; lecture_num: number; mode?: string; profile_json?: string;
  }) => {
    const qs = new URLSearchParams({
      course_id: params.course_id,
      lecture_num: String(params.lecture_num),
      mode: params.mode || 'study',
    });
    if (params.profile_json) qs.set('profile_json', params.profile_json);
    return fetchAPI(`/api/lecture/${params.course_id}/${params.lecture_num}/multi-agent?${qs.toString()}`) as Promise<VerificationResponse>;
  },

  /** 获取审核报告 */
  getAuditReport: (courseId: string, lectureNum: number) =>
    fetchAPI(`/api/verification/audit-report/${courseId}/${lectureNum}`),

  /** 验证编排器状态 */
  getVerificationStatus: () =>
    fetchAPI('/api/verification/status'),
};

export interface VerificationStep {
  step: string;
  agent: string;
  action: string;
  status: string;
  version: number;
  score: number;
  issues: Array<{ location?: string; problem?: string; severity?: string; fix?: string }>;
  feedback: string;
  started_at: string;
  finished_at: string | null;
}

export interface VerificationResponse {
  task_id: string;
  status: 'approved' | 'rejected' | 'fallback_pending';
  verified: boolean;
  generation_mode: string;
  final_version: number;
  retry_count: number;
  verification_steps: VerificationStep[];
  audit_report: {
    overall_confidence: number;
    total_issues: number;
    critical_issues: number;
    details: any[];
  } | null;
  citations: Array<{ title: string; source: string }>;
  resource: {
    title: string;
    content: string;
    code: string;
    mindmap: any[];
    extended_reading?: any;
  };
  warning?: string;
}
