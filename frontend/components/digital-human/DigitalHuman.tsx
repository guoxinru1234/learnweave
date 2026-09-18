"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";

type AvatarState = "idle" | "speaking" | "thinking" | "greeting";

interface Props {
  state?: AvatarState;
  size?: number;
  className?: string;
  onClick?: () => void;
}

/**
 * AI 女教师 — 讯飞2D风格数字人
 * 外观参考讯飞虚拟人形象设计
 */
export function DigitalHuman({ state = "idle", size = 200, className = "", onClick }: Props) {
  const [blink, setBlink] = useState(false);
  const [mouthPhase, setMouthPhase] = useState(0);
  const blinkTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const schedule = () => {
      blinkTimer.current = setTimeout(() => {
        setBlink(true);
        setTimeout(() => setBlink(false), 120);
        schedule();
      }, 2800 + Math.random() * 3200);
    };
    schedule();
    return () => { if (blinkTimer.current) clearTimeout(blinkTimer.current); };
  }, []);

  useEffect(() => {
    if (state === "speaking") {
      const i = setInterval(() => setMouthPhase(p => (p + 1) % 4), 80);
      return () => clearInterval(i);
    }
    setMouthPhase(0);
  }, [state]);

  const s = size / 200;

  return (
    <motion.div
      className={`relative select-none ${className}`}
      style={{ width: size, height: size * 1.3 }}
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
    >
      {/* 外发光 */}
      <motion.div
        className="absolute rounded-full"
        style={{
          inset: -6,
          background: "linear-gradient(135deg, #818cf8, #a78bfa, #4f46e5, #c084fc)",
          backgroundSize: "300% 300%",
          filter: "blur(12px)",
          opacity: 0.35,
        }}
        animate={
          state === "speaking"
            ? { backgroundPosition: ["0% 0%", "100% 100%", "0% 0%"] }
            : {}
        }
        transition={{ backgroundPosition: { repeat: Infinity, duration: 2, ease: "linear" } }}
      />

      <svg viewBox="0 0 200 260" width={size} height={size * 1.3}>
        <defs>
          <radialGradient id="bg2" cx="50%" cy="35%">
            <stop offset="0%" stopColor="#e8e0f0" />
            <stop offset="100%" stopColor="#1e1b4b" />
          </radialGradient>
          <clipPath id="circle2"><circle cx="100" cy="90" r="88" /></clipPath>
          <linearGradient id="hairGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2d2050" />
            <stop offset="100%" stopColor="#1a1035" />
          </linearGradient>
        </defs>

        {/* 背景圆 */}
        <circle cx="100" cy="90" r="90" fill="url(#bg2)" />
        <circle cx="100" cy="90" r="90" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2.5" />

        <g clipPath="url(#circle2)">
          {/* 肩膀 */}
          <ellipse cx="100" cy="200" rx="95" ry="55" fill="#312e81" opacity="0.5" />
          <path d="M30 170 Q100 210 170 170 L180 240 Q100 260 20 240Z" fill="#4c1d95" opacity="0.35" />

          {/* 脖子 */}
          <rect x="88" y="120" width="24" height="24" rx="8" fill="#f5e1ce" />

          {/* 头+脸 */}
          <motion.g
            animate={
              state === "idle" ? { y: [0, -1.5, 0] } :
              state === "speaking" ? { y: [0, -1, 0, -1.5, 0] } : {}
            }
            transition={{
              repeat: Infinity,
              duration: state === "speaking" ? 0.5 : 3,
              ease: "easeInOut",
            }}
          >
            {/* 脸型 */}
            <ellipse cx="100" cy="82" rx="50" ry="55" fill="#fde8d0" />
            {/* 下颌 */}
            <path d="M60 100 Q100 140 140 100" fill="#fde8d0" />

            {/* 腮红 */}
            <ellipse cx="68" cy="92" rx="10" ry="6" fill="#f4a4a4" opacity="0.25" />
            <ellipse cx="132" cy="92" rx="10" ry="6" fill="#f4a4a4" opacity="0.25" />

            {/* 眉毛 */}
            <path d="M62 58 Q76 52 84 58" stroke="#3d2010" strokeWidth="2" fill="none" strokeLinecap="round" />
            <path d="M116 58 Q124 52 138 58" stroke="#3d2010" strokeWidth="2" fill="none" strokeLinecap="round" />

            {/* 眼睛 */}
            {blink ? (
              <>
                <line x1="64" y1="70" x2="86" y2="70" stroke="#1a1a2e" strokeWidth="3" strokeLinecap="round" />
                <line x1="114" y1="70" x2="136" y2="70" stroke="#1a1a2e" strokeWidth="3" strokeLinecap="round" />
              </>
            ) : (
              <>
                <ellipse cx="75" cy="70" rx="11" ry="10" fill="white" />
                <circle cx="76" cy="69" r="5.5" fill="#2d1b0e" />
                <circle cx="78.5" cy="67.5" r="2" fill="white" />
                <circle cx="74.5" cy="72" r="1" fill="white" />
                <ellipse cx="125" cy="70" rx="11" ry="10" fill="white" />
                <circle cx="126" cy="69" r="5.5" fill="#2d1b0e" />
                <circle cx="128.5" cy="67.5" r="2" fill="white" />
                <circle cx="124.5" cy="72" r="1" fill="white" />
              </>
            )}

            {/* 眼镜 (知性风格) */}
            <rect x="58" y="61" width="34" height="22" rx="6" fill="none" stroke="#8b7355" strokeWidth="1.8" opacity="0.6" />
            <rect x="108" y="61" width="34" height="22" rx="6" fill="none" stroke="#8b7355" strokeWidth="1.8" opacity="0.6" />
            <line x1="92" y1="72" x2="108" y2="72" stroke="#8b7355" strokeWidth="1.8" opacity="0.6" />

            {/* 鼻子 */}
            <path d="M97 82 L95 92 Q100 95 105 92 L103 82" fill="#e8c8a0" opacity="0.35" />

            {/* 嘴 (说话时动态变化) */}
            {state === "speaking" ? (
              <>
                {mouthPhase === 0 && <ellipse cx="100" cy="102" rx="9" ry="3" fill="#d4687c" />}
                {mouthPhase === 1 && <ellipse cx="100" cy="102" rx="8" ry="7" fill="#d4687c" />}
                {mouthPhase === 2 && <ellipse cx="100" cy="102" rx="7" ry="5" fill="#d4687c" />}
                {mouthPhase === 3 && <ellipse cx="100" cy="103" rx="6" ry="3.5" fill="#d4687c" />}
              </>
            ) : (
              <path d="M89 100 Q100 108 111 100" stroke="#d4687c" strokeWidth="2.2" fill="none" strokeLinecap="round" />
            )}
          </motion.g>

          {/* 头发 */}
          <path d="M45 82 Q45 8 100 6 Q155 8 155 82 Q155 35 100 28 Q45 35 45 82Z" fill="url(#hairGrad)" />
          {/* 刘海细节 */}
          <path d="M48 62 Q58 16 78 20 Q62 28 50 55" fill="#2d2050" opacity="0.8" />
          <path d="M152 62 Q142 16 122 20 Q138 28 150 55" fill="#2d2050" opacity="0.8" />
          <path d="M62 38 Q88 10 100 12 Q94 18 70 42" fill="#2d2050" opacity="0.5" />
          <path d="M138 38 Q112 10 100 12 Q106 18 130 42" fill="#2d2050" opacity="0.5" />

          {/* 发饰 (小蝴蝶结) */}
          <circle cx="140" cy="45" r="10" fill="#818cf8" opacity="0.7" />
          <path d="M140 38 L132 30 L140 42Z" fill="#a78bfa" opacity="0.6" />
          <path d="M140 38 L148 30 L140 42Z" fill="#a78bfa" opacity="0.6" />

          {/* AI 标识 耳麦 */}
          <rect x="148" y="60" width="5" height="20" rx="3" fill="#6366f1" opacity="0.8" />
          <circle cx="150" cy="54" r="8" fill="none" stroke="#6366f1" strokeWidth="2.5" />
          <circle cx="150" cy="54" r="3" fill="#22c55e" />

          {/* 衣领 */}
          <path d="M84 126 L100 148 L116 126" fill="white" opacity="0.5" stroke="#818cf8" strokeWidth="1" />
        </g>
      </svg>

      {/* 状态粒子 */}
      {state === "thinking" && (
        <div className="absolute -top-2 right-0 flex gap-1.5">
          {[0, 1, 2].map(i => (
            <motion.div key={i} className="w-3 h-3 rounded-full bg-indigo-400"
              animate={{ y: [0, -12, 0], opacity: [0.3, 1, 0.3] }}
              transition={{ repeat: Infinity, duration: 0.6, delay: i * 0.15 }}
            />
          ))}
        </div>
      )}

      {/* 语音波纹 (说话时) */}
      {state === "speaking" && (
        <div className="absolute top-1/2 -right-3 flex items-end gap-0.5">
          {[0.6, 1, 0.8, 1, 0.6, 0.4].map((h, i) => (
            <motion.div key={i} className="w-1 bg-indigo-400 rounded-full"
              animate={{ height: [8, h * 24, 8] }}
              transition={{ repeat: Infinity, duration: 0.4, delay: i * 0.06 }}
            />
          ))}
        </div>
      )}

      {/* 标签 */}
      <div className="absolute -bottom-3 left-1/2 -translate-x-1/2">
        <motion.span
          className="text-xs px-3 py-1 rounded-full bg-white/90 dark:bg-gray-900/85 text-indigo-600 dark:text-indigo-300 font-semibold shadow-md whitespace-nowrap border border-indigo-100 dark:border-indigo-900/50"
          animate={state === "speaking" ? { scale: [1, 1.05, 1] } : {}}
          transition={{ repeat: Infinity, duration: 0.8 }}
        >
          {state === "idle" && "🟢 AI 教师在线"}
          {state === "speaking" && "🔊 讲解中..."}
          {state === "thinking" && "🤔 思考中..."}
          {state === "greeting" && "👋 你好!"}
        </motion.span>
      </div>
    </motion.div>
  );
}
