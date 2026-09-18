/**
 * Chat Storage - Persist chat sessions to IndexedDB
 *
 * Independent from stage/scene storage cycle.
 * Handles serialization, truncation, and batch writes.
 */

import type { ChatSession, ChatMessageMetadata, SessionStatus } from '@/lib/types/chat';
import type { UIMessage } from 'ai';
import { db, type ChatSessionRecord } from './database';

/** Maximum messages per session to avoid IndexedDB bloat */
const MAX_MESSAGES_PER_SESSION = 200;

/**
 * 当前登录用户 ID（从 sessionStorage 读取 AuthContext 存的 auth_user）。
 * 未登录/读取失败时返回 'anon'，保证不会串到别的用户。
 */
function getCurrentUserId(): string {
  if (typeof window === 'undefined') return 'anon';
  try {
    const raw = sessionStorage.getItem('auth_user');
    if (raw) {
      const user = JSON.parse(raw);
      return String(user.id ?? 'anon');
    }
  } catch {
    // ignore parse errors
  }
  return 'anon';
}

/**
 * 分区 key：userId + stageId，实现"不同用户看到不同聊天记录"。
 * 用 '::' 分隔，避免 stageId 本身含冒号时冲突。
 */
function partitionKey(stageId: string): string {
  return `${getCurrentUserId()}::${stageId}`;
}

/**
 * Save chat sessions for a stage to IndexedDB.
 * - Active sessions are saved as 'interrupted' (streaming context lost on refresh)
 * - pendingToolCalls are cleared (runtime-only state)
 * - Messages are truncated to MAX_MESSAGES_PER_SESSION
 */
export async function saveChatSessions(stageId: string, sessions: ChatSession[]): Promise<void> {
  const key = partitionKey(stageId);
  if (!sessions || sessions.length === 0) {
    // Delete all sessions for this stage if empty
    await db.chatSessions.where('stageId').equals(key).delete();
    return;
  }

  const records: ChatSessionRecord[] = sessions.map((session) => ({
    id: session.id,
    stageId: key,
    type: session.type,
    title: session.title,
    // Mark active sessions as interrupted (streaming context lost on refresh)
    status: (session.status === 'active' ? 'interrupted' : session.status) as SessionStatus,
    // Truncate messages and strip non-serializable data
    messages: session.messages.slice(-MAX_MESSAGES_PER_SESSION),
    config: session.config,
    toolCalls: session.toolCalls,
    pendingToolCalls: [], // Clear runtime state
    createdAt: session.createdAt,
    updatedAt: session.updatedAt,
    sceneId: session.sceneId,
    lastActionIndex: session.lastActionIndex,
  }));

  await db.transaction('rw', db.chatSessions, async () => {
    // Delete old sessions for this stage, then bulk insert new ones
    await db.chatSessions.where('stageId').equals(key).delete();
    await db.chatSessions.bulkPut(records);
  });
}

/**
 * Load chat sessions for a stage from IndexedDB.
 * Returns sessions sorted by createdAt.
 */
export async function loadChatSessions(stageId: string): Promise<ChatSession[]> {
  const key = partitionKey(stageId);
  const records = await db.chatSessions.where('stageId').equals(key).sortBy('createdAt');

  return records.map((record) => ({
    id: record.id,
    type: record.type,
    title: record.title,
    status: record.status,
    messages: record.messages as UIMessage<ChatMessageMetadata>[],
    config: record.config,
    toolCalls: record.toolCalls,
    pendingToolCalls: record.pendingToolCalls,
    createdAt: record.createdAt,
    updatedAt: record.updatedAt,
    sceneId: record.sceneId,
    lastActionIndex: record.lastActionIndex,
  }));
}

/**
 * Delete all chat sessions for a stage.
 */
export async function deleteChatSessions(stageId: string): Promise<void> {
  const key = partitionKey(stageId);
  await db.chatSessions.where('stageId').equals(key).delete();
}
