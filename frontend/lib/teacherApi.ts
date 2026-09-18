/** LearnWeave Teacher API Client —— 教师端专用 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

function getAuthHeaders(): HeadersInit {
  const token =
    typeof window !== 'undefined'
      ? sessionStorage.getItem('auth_token')
      : null;
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function fetchTeacher<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: getAuthHeaders(),
    ...options,
  });
  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      throw new Error('需要管理员登录');
    }
    throw new Error(`API ${res.status}: ${path}`);
  }
  return res.json();
}

// ==================== 类型定义 ====================

export interface StudentSummary {
  id: number;
  name: string;
  overall: number;
  title: string;
  path: string;
  progress: number;
  last_active: string;
  scores: number[];
  hours: number;
  quiz_accuracy: number;
}

export interface DashboardResponse {
  student_count: number;
  class_avg_overall: number;
  weak_count: number;
  active_today_count: number;
  class_dim_averages: number[];
  weakest_dimension: string;
  weakest_score: number;
  at_risk_students: StudentSummary[];
  students: StudentSummary[];
}

export interface StudentDetail {
  id: number;
  name: string;
  username: string;
  grade: string;
  major: string;
  overall: number;
  title: string;
  path: string;
  progress: number;
  last_active: string;
  learning_hours: number;
  quiz_accuracy: number;
  scores: number[];
}

export interface StudentsResponse {
  total: number;
  students: StudentDetail[];
}

export interface LectureProgress {
  num: number;
  title: string;
  done: number;
}

export interface ModuleProgress {
  name: string;
  lectures: LectureProgress[];
}

export interface ProgressResponse {
  total_students: number;
  total_lectures: number;
  started_lectures_count: number;
  avg_completion_rate: number;
  lagging_count: number;
  modules: ModuleProgress[];
}

export interface StudentGrade {
  id: number;
  name: string;
  quiz_avg: number;
  lab_score: number;
  final_score: number;
  grade: string;
  rank: number;
}

export interface GradesResponse {
  avg_score: number;
  top_grade: string;
  lowest_grade: string;
  pass_rate: number;
  students: StudentGrade[];
}

export interface StudentReport {
  name: string;
  overall: number;
  scores: number[];
  weak: string[];
  strong: string[];
}

export interface ReportsResponse {
  class_dim_averages: number[];
  class_avg_overall: number;
  weakest_dimension: string;
  strongest_dimension: string;
  attention_count: number;
  students: StudentReport[];
}

export interface ResourceTypeCount {
  type: string;
  count: number;
  icon: string;
  color: string;
  desc: string;
}

export interface ResourcesResponse {
  total: number;
  lecture_count: number;
  quiz_count: number;
  lab_count: number;
  resources: ResourceTypeCount[];
}

export interface FeatureToggle {
  key: string;
  label: string;
  desc: string;
  enabled: boolean;
}

export interface SettingsResponse {
  course_info: Record<string, string>;
  ai_config: Record<string, string>;
  features: FeatureToggle[];
}

// ==================== API 方法 ====================

export const teacherApi = {
  getDashboard: () =>
    fetchTeacher<DashboardResponse>('/api/teacher/dashboard'),

  getStudents: (search?: string) =>
    fetchTeacher<StudentsResponse>(
      `/api/teacher/students${search ? `?search=${encodeURIComponent(search)}` : ''}`
    ),

  getProgress: () =>
    fetchTeacher<ProgressResponse>('/api/teacher/progress'),

  getGrades: () =>
    fetchTeacher<GradesResponse>('/api/teacher/grades'),

  getReports: () =>
    fetchTeacher<ReportsResponse>('/api/teacher/reports'),

  getResources: () =>
    fetchTeacher<ResourcesResponse>('/api/teacher/resources'),

  getSettings: () =>
    fetchTeacher<SettingsResponse>('/api/teacher/settings'),

  updateToggle: (key: string, enabled: boolean) =>
    fetchTeacher<{ success: boolean }>('/api/teacher/settings/toggle', {
      method: 'PUT',
      body: JSON.stringify({ key, enabled }),
    }),
};
