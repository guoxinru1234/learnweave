// frontend/components/AgentWorkflow.tsx
'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, Loader2, XCircle, Clock } from 'lucide-react';

export interface AgentStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'success' | 'error';
  detail?: string;
  input?: string;
  output_preview?: string;
}

interface AgentWorkflowProps {
  steps?: AgentStep[];
  isActive?: boolean;
}

export function AgentWorkflow({ steps = [], isActive = false }: AgentWorkflowProps) {
  const [displaySteps, setDisplaySteps] = useState<AgentStep[]>(steps);

  // 当外部 steps 变化时更新显示
  useEffect(() => {
    setDisplaySteps(steps);
  }, [steps]);

  // 如果没有任何步骤，显示占位提示
  if (!displaySteps.length) {
    return (
      <div className="text-xs text-[var(--lm-text-tertiary)] py-4 text-center">
        {isActive ? '⏳ 等待智能体启动...' : '点击上方按钮触发智能体协作'}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {displaySteps.map((step) => {
        const statusIcon = {
          pending: <Clock className="w-3.5 h-3.5 text-gray-400" />,
          running: <Loader2 className="w-3.5 h-3.5 text-indigo-600 animate-spin" />,
          success: <CheckCircle className="w-3.5 h-3.5 text-green-600" />,
          error: <XCircle className="w-3.5 h-3.5 text-red-600" />,
        }[step.status || 'pending'];

        const statusBg = {
          pending: 'bg-gray-50 border-gray-200',
          running: 'bg-indigo-50 border-indigo-200',
          success: 'bg-green-50 border-green-200',
          error: 'bg-red-50 border-red-200',
        }[step.status || 'pending'];

        return (
          <div
            key={step.id}
            className={`flex items-start gap-2.5 p-2 rounded-lg border transition-all ${statusBg}`}
          >
            <div className="flex-shrink-0 mt-0.5">{statusIcon}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-medium text-[#1a1a2e]">{step.name}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/50 text-gray-500">
                  Agent
                </span>
              </div>
              <p className="text-xs text-[#6a6a7e] truncate">{step.description}</p>
              {step.output_preview && step.status === 'success' && (
                <p className="text-[10px] text-green-600 truncate mt-0.5">
                  📦 {step.output_preview}
                </p>
              )}
            </div>
            <div className="flex-shrink-0">
              <span
                className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                  step.status === 'pending'
                    ? 'bg-gray-200 text-gray-500'
                    : step.status === 'running'
                    ? 'bg-indigo-200 text-indigo-700 animate-pulse'
                    : step.status === 'success'
                    ? 'bg-green-200 text-green-700'
                    : 'bg-red-200 text-red-700'
                }`}
              >
                {step.status === 'pending' && '等待'}
                {step.status === 'running' && '执行中'}
                {step.status === 'success' && '已完成'}
                {step.status === 'error' && '异常'}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default AgentWorkflow;