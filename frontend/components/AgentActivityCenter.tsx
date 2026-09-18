'use client';

import { useState } from 'react';
import { Bot, X, Sparkles } from 'lucide-react';

const AGENT_COLORS: Record<string, string> = {
  '协调智能体': 'text-purple-600 bg-purple-100 border-purple-200',
  '评估智能体': 'text-blue-600 bg-blue-100 border-blue-200',
  '路径规划智能体': 'text-orange-600 bg-orange-100 border-orange-200',
  '资源生成智能体': 'text-green-600 bg-green-100 border-green-200',
  '画像智能体': 'text-pink-600 bg-pink-100 border-pink-200',
  '答疑智能体': 'text-indigo-600 bg-indigo-100 border-indigo-200',
};

const AGENT_ICONS: Record<string, string> = {
  '协调智能体': '🎯',
  '评估智能体': '📊',
  '路径规划智能体': '🗺️',
  '资源生成智能体': '📦',
  '画像智能体': '🧠',
  '答疑智能体': '💬',
};

type AgentEvent = {
  type: string;
  data: any;
  source: string;
  timestamp: string;
};

export default function AgentActivityCenter({
  events,
  unreadCount,
  onMarkRead,
}: {
  events: AgentEvent[];
  unreadCount: number;
  onMarkRead: () => void;
}) {
  const [expanded, setExpanded] = useState(true);

  const getEventMessage = (event: AgentEvent): string => {
    const messages: Record<string, string> = {
      STEP_COMPLETED: `✅ 完成步骤「${event.data.step_name || event.data.step_id}」`,
      WEAKNESS_DETECTED: `⚠️ 检测到薄弱点「${event.data.topic}」(${event.data.mastery}%)`,
      PLAN_GENERATED: `📋 生成补强计划「${event.data.plan?.topic || ''}」`,
      MASTERY_CHANGED: `📈 「${event.data.topic}」掌握度变化 ${(event.data.change * 100).toFixed(0)}%`,
      PROFILE_UPDATED: `🧠 画像已更新`,
      RESOURCE_GENERATED: `📦 已生成 ${event.data.count || ''} 个资源`,
      USER_NOTIFICATION: `${event.data.title || event.data.message || ''}`,
      PROFILE_COMPLETED: `🎉 画像已构建完成！`,
    };
    return messages[event.type] || `${event.source}: ${event.type}`;
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <button
        onClick={() => {
          setExpanded(!expanded);
          onMarkRead();
        }}
        className="relative w-14 h-14 rounded-full bg-indigo-600 text-white shadow-lg hover:bg-indigo-700 transition-all flex items-center justify-center"
      >
        <Bot className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center animate-pulse">
            {unreadCount}
          </span>
        )}
      </button>

      {expanded && (
        <div className="absolute bottom-20 right-0 w-96 max-h-[420px] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-gray-800 dark:to-gray-700 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span className="font-semibold text-sm">智能体动态</span>
            </div>
            <button
              onClick={() => setExpanded(false)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="overflow-y-auto max-h-[340px] p-3 space-y-2">
            {events.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                <Bot className="w-10 h-10 mx-auto mb-2 opacity-30" />
                等待智能体活动...
              </div>
            ) : (
              events.map((event, index) => {
                const color = AGENT_COLORS[event.source] || 'text-gray-600 bg-gray-100 border-gray-200';
                const icon = AGENT_ICONS[event.source] || '🤖';
                return (
                  <div
                    key={index}
                    className="p-3 rounded-xl border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                  >
                    <div className="flex items-start gap-2">
                      <span className="text-sm">{icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-[10px] px-2 py-0.5 rounded-full border ${color}`}>
                            {event.source}
                          </span>
                          <span className="text-[10px] text-gray-400">
                            {formatTime(event.timestamp)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                          {getEventMessage(event)}
                        </p>
                        {event.data.message && (
                          <p className="text-xs text-gray-500 mt-0.5">{event.data.message}</p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 text-center text-[10px] text-gray-400">
            {events.length} 条动态 · 实时更新
          </div>
        </div>
      )}
    </div>
  );
}