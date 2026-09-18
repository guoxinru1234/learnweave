// frontend/components/CircularProgress.tsx
'use client';

interface CircularProgressProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  color?: string;
  gradient?: boolean;
}

export function CircularProgress({
  percentage,
  size = 56,
  strokeWidth = 5,
  label,
  color,
  gradient = true,
}: CircularProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  // 默认渐变色：紫色到蓝色
  const gradientId = `progress-gradient-${Math.random().toString(36).substr(2, 9)}`;

  const getColor = () => {
    if (percentage >= 80) return '#22c55e';
    if (percentage >= 50) return '#f59e0b';
    return '#ef4444';
  };

  const finalColor = color || getColor();

  // 如果是非渐变，使用纯色
  if (!gradient) {
    return (
      <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={finalColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-[#1a1a2e]">
          {label || `${percentage}%`}
        </div>
      </div>
    );
  }

  // 渐变色：根据掌握度自动选择色系
  let startColor = '#4f46e5';
  let endColor = '#818cf8';
  if (percentage >= 80) {
    startColor = '#22c55e';
    endColor = '#4ade80';
  } else if (percentage >= 50) {
    startColor = '#f59e0b';
    endColor = '#fbbf24';
  } else {
    startColor = '#ef4444';
    endColor = '#f87171';
  }

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <div className="absolute inset-0 rounded-full shadow-lg shadow-indigo-500/20 blur-sm" />
      <svg className="transform -rotate-90" width={size} height={size}>
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={startColor} />
            <stop offset="100%" stopColor={endColor} />
          </linearGradient>
        </defs>
        {/* 背景圆环 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
        />
        {/* 进度圆环（渐变色） */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out drop-shadow-lg"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-[#1a1a2e]">
        {label || `${percentage}%`}
      </div>
    </div>
  );
}

export default CircularProgress;