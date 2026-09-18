'use client';

import Link from 'next/link';
import { useJourney } from '@/contexts/JourneyContext';
import { CheckCircle, Loader2 } from 'lucide-react';

export default function JourneySteps() {
  const { steps, currentStep, nextStep, progress, loading } = useJourney();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100 p-6 mb-6">
      {/* 步骤条 */}
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = step.completed;
          const isActive = step.id === currentStep?.id;
          const isNext = step.id === nextStep?.id;

          return (
            <div key={step.id} className="flex items-center flex-1">
              <Link
                href={step.href}
                className="flex flex-col items-center group"
                onClick={(e) => {
                  if (!isCompleted && !isActive) {
                    e.preventDefault();
                  }
                }}
              >
                <div className={`
                  w-12 h-12 rounded-full flex items-center justify-center text-xl transition-all duration-300
                  ${isCompleted ? 'bg-green-500 text-white shadow-lg shadow-green-200' :
                    isActive ? 'bg-indigo-600 text-white ring-4 ring-indigo-200 animate-pulse' :
                    isNext ? 'bg-orange-400 text-white ring-4 ring-orange-200' :
                    'bg-gray-200 text-gray-400'}
                `}>
                  {isCompleted ? <CheckCircle className="w-6 h-6" /> : step.icon}
                </div>
                <span className={`
                  text-xs mt-1 font-medium transition-colors
                  ${isActive ? 'text-indigo-600' :
                    isCompleted ? 'text-green-600' :
                    isNext ? 'text-orange-500' :
                    'text-gray-400'}
                `}>
                  {step.label}
                </span>
                {isCompleted && (
                  <span className="text-[10px] text-green-500">✅ 已完成</span>
                )}
                {isActive && (
                  <span className="text-[10px] text-indigo-500 animate-pulse">📍 进行中</span>
                )}
                {isNext && !isCompleted && (
                  <span className="text-[10px] text-orange-500">⏳ 下一步</span>
                )}
              </Link>
              {index < steps.length - 1 && (
                <div className={`
                  flex-1 h-0.5 mx-2 transition-all duration-500
                  ${isCompleted ? 'bg-green-400' :
                    isActive ? 'bg-indigo-300' :
                    'bg-gray-200'}
                `} />
              )}
            </div>
          );
        })}
      </div>

      {/* 进度条 */}
      <div className="mt-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>总体进度</span>
          <span className="font-semibold text-indigo-600">{Math.round(progress * 100)}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-700"
            style={{ width: `${progress * 100}%` }}
          />
        </div>
      </div>

      {/* 下一步引导 */}
      {nextStep && (
        <div className="mt-4 p-3 bg-white rounded-xl border border-indigo-100 flex items-center justify-between">
          <div>
            <span className="text-xs text-indigo-500 font-medium">📍 下一步</span>
            <p className="text-sm font-semibold">{nextStep.label}</p>
            <p className="text-xs text-gray-500">点击上方图标或下方按钮继续</p>
          </div>
          <Link
            href={nextStep.href}
            className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition-colors"
          >
            进入 {nextStep.label} →
          </Link>
        </div>
      )}
    </div>
  );
}