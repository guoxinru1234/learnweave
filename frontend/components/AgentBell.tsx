'use client';

import { useState, useEffect } from 'react';
import { Bell, X, Loader2, CheckCircle, Clock, ChevronUp } from 'lucide-react';
import { useAgent } from '@/contexts/AgentContext';

interface AgentStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'success' | 'error';
  output_preview?: string;
}

export default function AgentBell() {
  const { agentSteps, isAgentRunning } = useAgent(); // 从 Context 获取
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // 计算运行中的步骤数
  const runningCount = agentSteps.filter(s => s.status === 'running').length;
  const successCount = agentSteps.filter(s => s.status === 'success').length;
  const totalCount = agentSteps.length;

  // 当新步骤完成时增加未读计数
  useEffect(() => {
    if (agentSteps.length > 0) {
      const lastStep = agentSteps[agentSteps.length - 1];
      if (lastStep.status === 'success' || lastStep.status === 'error') {
        setUnreadCount(prev => prev + 1);
      }
    }
  }, [agentSteps]);

  // 点击铃铛时重置未读计数
  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen) setUnreadCount(0);
  };

  const statusIcon = isAgentRunning ? (
    <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
  ) : totalCount > 0 && successCount === totalCount ? (
    <CheckCircle className="w-5 h-5 text-green-600" />
  ) : (
    <Bell className="w-5 h-5 text-gray-500" />
  );

  const statusLabel = isAgentRunning
    ? `协作中 ${runningCount}/${totalCount}`
    : totalCount > 0
    ? `已完成 ${successCount}/${totalCount}`
    : '智能体就绪';

  return (
    <div className="relative">
      {/* 铃铛按钮 */}
      <button
        onClick={handleToggle}
        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[#f8f8fa] hover:bg-indigo-50 transition-all border border-[#e8e8ea] relative"
      >
        {statusIcon}
        <span className="text-xs font-medium text-[#1a1a2e]">{statusLabel}</span>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </button>

      {/* 下拉面板 */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 max-h-96 overflow-y-auto bg-white rounded-2xl shadow-xl border border-[#e8e8ea] z-50 p-3">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold flex items-center gap-1.5">
              🤖 智能体协作详情
              {isAgentRunning && <span className="text-xs text-indigo-500 animate-pulse">● 运行中</span>}
            </h4>
            <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-gray-600">
              <X className="w-4 h-4" />
            </button>
          </div>
          {agentSteps.length === 0 ? (
            <div className="text-xs text-gray-400 py-4 text-center">暂无智能体活动</div>
          ) : (
            <ul className="space-y-2">
              {agentSteps.map((step, idx) => (
                <li key={step.id || idx} className="flex items-start gap-2 text-sm p-1.5 rounded-lg hover:bg-gray-50">
                  <div className="mt-0.5">
                    {step.status === 'pending' && <Clock className="w-4 h-4 text-gray-300" />}
                    {step.status === 'running' && <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />}
                    {step.status === 'success' && <CheckCircle className="w-4 h-4 text-green-500" />}
                    {step.status === 'error' && <X className="w-4 h-4 text-red-500" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-800">{step.name}</span>
                      <span className="text-[10px] font-mono text-gray-400">
                        {step.status === 'pending' && '等待'}
                        {step.status === 'running' && '执行中'}
                        {step.status === 'success' && '✓'}
                        {step.status === 'error' && '✗'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 truncate">{step.description}</p>
                    {step.output_preview && step.status === 'success' && (
                      <p className="text-[10px] text-green-600 truncate">📦 {step.output_preview}</p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
          {totalCount > 0 && !isAgentRunning && (
            <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-400 text-center">
              共 {totalCount} 个步骤，全部完成
            </div>
          )}
        </div>
      )}
    </div>
  );
}