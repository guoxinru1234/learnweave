/** Safe data adapters — honest handling of missing fields, never fake success */
export function safePct(v: any): string { if (v == null || isNaN(Number(v))) return '--'; return `${v}%`; }
export function safeNum(v: any): string { if (v == null || isNaN(Number(v))) return '--'; return String(v); }

export interface NormalizedCitation {
  title: string; source: string;
  chunk_id: string | null; evidence_excerpt: string | null;
  /** verified = has both chunk_id AND evidence_excerpt; incomplete = has source but no chunk; missing = no source */
  status: 'verified' | 'incomplete' | 'missing';
  statusLabel: string;
}
export function normalizeCitation(c: any): NormalizedCitation {
  const title = c?.title || '未命名来源';
  const source = c?.source || c?.source_path || '';
  const chunk_id = c?.chunk_id || null;
  const excerpt = c?.evidence_excerpt || null;
  let status: NormalizedCitation['status'];
  let label: string;
  if (chunk_id && excerpt) { status = 'verified'; label = '已验证'; }
  else if (source) { status = 'incomplete'; label = '引用粒度不足，待补充 chunk_id 和 evidence_excerpt'; }
  else { status = 'missing'; label = '缺少来源引用'; }
  return { title, source, chunk_id, evidence_excerpt: excerpt, status, statusLabel: label };
}

export function normalizeVerificationStatus(v: any): string {
  if (v === true || v === 'approved' || v === 'pass') return 'supported';
  if (v === false || v === 'rejected' || v === 'fail') return 'unsupported';
  return 'unverifiable';
}

export function normalizeGenerationResult(data: any) {
  const task_id = data?.task_id || '';
  const verified = data?.verified ?? null;
  const citations = (data?.citations || []).map(normalizeCitation);
  return {
    task_id, status: data?.status || 'unknown', verified,
    generation_mode: data?.generation_mode || '',
    resource: data?.resource || {},
    citations,
    audit_report: data?.audit_report || null,
    verification_steps: data?.verification_steps || [],
  };
}

export function formatMetric(v: any, suffix = '%'): string {
  if (v == null || isNaN(Number(v))) return '--';
  return `${v}${suffix}`;
}

/** Session-storage cache with user isolation */
const CACHE_PREFIX = 'learnmate_task_';
export function saveTaskCache(userId: number | string, result: any) {
  try {
    const entry = { user_id: String(userId), task_id: result.task_id, created_at: new Date().toISOString(), result };
    sessionStorage.setItem(CACHE_PREFIX + userId, JSON.stringify(entry));
  } catch { /* quota exceeded, ignore */ }
}
export function loadTaskCache(userId: number | string): any | null {
  try {
    const raw = sessionStorage.getItem(CACHE_PREFIX + userId);
    if (!raw) return null;
    const entry = JSON.parse(raw);
    if (entry.user_id !== String(userId)) return null; // wrong user
    const age = Date.now() - new Date(entry.created_at).getTime();
    if (age > 3600000) { sessionStorage.removeItem(CACHE_PREFIX + userId); return null; } // expired after 1h
    return entry.result;
  } catch { sessionStorage.removeItem(CACHE_PREFIX + userId); return null; }
}
export function clearTaskCache(userId: number | string) { sessionStorage.removeItem(CACHE_PREFIX + userId); }
