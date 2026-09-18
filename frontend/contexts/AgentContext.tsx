// frontend/contexts/AgentContext.tsx
'use client';

import { createContext, useContext, useEffect, useState, useCallback, ReactNode, useRef } from 'react';

// ==================== 类型定义 ====================
export type AgentEvent = {
  id?: string;
  type: string;
  title: string;
  description?: string;
  timestamp?: string;
  read?: boolean;
};

// 智能体步骤类型
export interface AgentStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'success' | 'error';
  output_preview?: string;
}

interface AgentContextType {
  // ===== 原有事件相关 =====
  events: AgentEvent[];
  unreadCount: number;
  isConnected: boolean;
  markAsRead: () => void;
  clearEvents: () => void;
  onNewEvent: (callback: (event: AgentEvent) => void) => () => void;

  // ===== 🆕 智能体步骤相关（方案 A） =====
  agentSteps: AgentStep[];
  isAgentRunning: boolean;
  setAgentSteps: (steps: AgentStep[]) => void;
  setAgentRunning: (running: boolean) => void;
  // 更新单个步骤状态（自动触发 Toast）
  updateAgentStep: (stepId: string, updates: Partial<AgentStep>) => void;
  // 重置智能体状态
  resetAgent: () => void;
}

const AgentContext = createContext<AgentContextType | undefined>(undefined);

export function AgentProvider({ children }: { children: ReactNode }) {
  // ===== 原有事件状态 =====
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const listenersRef = useRef<((event: AgentEvent) => void)[]>([]);

  // ===== 🆕 智能体步骤状态 =====
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);
  const [isAgentRunning, setIsAgentRunning] = useState(false);
  const prevAgentStepsRef = useRef<AgentStep[]>([]);

  // ===== 添加新事件（触发 Toast） =====
  const addEvent = useCallback((newEvent: AgentEvent) => {
    setEvents(prev => {
      const exists = prev.some(e => e.title === newEvent.title && e.type === newEvent.type);
      if (exists) return prev;
      const updated = [newEvent, ...prev];
      return updated.slice(0, 50);
    });
    setUnreadCount(prev => prev + 1);

    // 通知所有订阅者（触发 Toast）
    listenersRef.current.forEach(callback => {
      try {
        callback(newEvent);
      } catch (e) {
        console.warn('Toast 回调执行失败', e);
      }
    });
  }, []);

  // ===== 订阅新事件 =====
  const onNewEvent = useCallback((callback: (event: AgentEvent) => void) => {
    listenersRef.current.push(callback);
    return () => {
      listenersRef.current = listenersRef.current.filter(cb => cb !== callback);
    };
  }, []);

  // ===== 🆕 监听 agentSteps 变化，检测步骤状态转换并触发 Toast =====
  // ✅ 修复：将 addEvent 从 setState updater 内部移到 useEffect 中，
  // 避免在 AgentProvider 渲染期间更新 ToastManager 的状态
  useEffect(() => {
    const prevSteps = prevAgentStepsRef.current;
    agentSteps.forEach(step => {
      const prevStep = prevSteps.find(s => s.id === step.id);
      // 当步骤变为 success 时，发布 Toast 事件
      if (step.status === 'success' && (!prevStep || prevStep.status !== 'success')) {
        addEvent({
          type: 'agent',
          title: `✅ ${step.name} 完成`,
          description: step.description,
          timestamp: new Date().toISOString(),
        });
      }
      // 当步骤变为 error 时，发布错误 Toast
      if (step.status === 'error' && (!prevStep || prevStep.status !== 'error')) {
        addEvent({
          type: 'error',
          title: `❌ ${step.name} 失败`,
          description: step.description || '请查看详细日志',
          timestamp: new Date().toISOString(),
        });
      }
    });
    prevAgentStepsRef.current = agentSteps;
  }, [agentSteps, addEvent]);

  // ===== 🆕 更新单个步骤状态（自动触发 Toast） =====
  const updateAgentStep = useCallback((stepId: string, updates: Partial<AgentStep>) => {
    setAgentSteps(prev =>
      prev.map(step =>
        step.id === stepId ? { ...step, ...updates } : step
      )
    );
  }, []);

  // ===== 🆕 重置智能体状态 =====
  const resetAgent = useCallback(() => {
    setAgentSteps([]);
    setIsAgentRunning(false);
  }, []);

  // ===== SSE 连接 =====
  useEffect(() => {
    let eventSource: EventSource | null = null;

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      eventSource = new EventSource(`${API_BASE}/api/events/stream`);
      setIsConnected(true);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'event') {
            const evt = data.event;
            addEvent({
              id: evt.id || Date.now().toString(),
              type: evt.type || 'info',
              title: evt.title || '智能体更新',
              description: evt.description || '',
              timestamp: evt.timestamp || new Date().toISOString(),
              read: false,
            });
          }
        } catch (e) {
          console.warn('解析 SSE 消息失败', e);
        }
      };

      eventSource.onerror = (err) => {
        console.warn('SSE 连接异常，5秒后重试', err);
        setIsConnected(false);
        eventSource?.close();
        setTimeout(() => {
          if (eventSource?.readyState === EventSource.CLOSED) {
            setIsConnected(true);
          }
        }, 5000);
      };
    } catch (e) {
      console.warn('SSE 初始化失败', e);
      setIsConnected(false);
    }

    return () => {
      eventSource?.close();
      setIsConnected(false);
    };
  }, [addEvent]);

  // ===== 标记全部已读 =====
  const markAsRead = useCallback(() => {
    setEvents(prev => prev.map(e => ({ ...e, read: true })));
    setUnreadCount(0);
  }, []);

  // ===== 清空所有事件 =====
  const clearEvents = useCallback(() => {
    setEvents([]);
    setUnreadCount(0);
  }, []);

  // ===== Context Value =====
  const value: AgentContextType = {
    // 原有
    events,
    unreadCount,
    isConnected,
    markAsRead,
    clearEvents,
    onNewEvent,
    // 🆕 新增
    agentSteps,
    isAgentRunning,
    setAgentSteps,
    setAgentRunning: setIsAgentRunning,
    updateAgentStep,
    resetAgent,
  };

  return (
    <AgentContext.Provider value={value}>
      {children}
    </AgentContext.Provider>
  );
}

export function useAgent() {
  const context = useContext(AgentContext);
  if (context === undefined) {
    throw new Error('useAgent must be used within an AgentProvider');
  }
  return context;
}