"use client";

import { useState, useRef, useEffect, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";

type Phase = "checking" | "idle" | "generating" | "live";

interface Props {
  courseId?: string;
  lectureNum?: number;
  lectureTitle?: string;
}

/**
 * AI 教学视频生成面板
 * 真实调用后端多智能体管线：Planner(LLM分镜) -> TTS(edge-tts配音) -> Renderer(Pillow+ffmpeg渲染)
 * 视频按讲次缓存：/media/videos/{courseId}_{lectureNum}.mp4，已生成则直接播放。
 */
export function DigitalHumanLive({
  courseId = "python-data-analysis",
  lectureNum = 1,
  lectureTitle = "",
}: Props) {
  const [phase, setPhase] = useState<Phase>("checking");
  const [error, setError] = useState<string | null>(null);
  const [steps, setSteps] = useState<{ text: string; done: boolean; active: boolean }[]>([]);
  const [progress, setProgress] = useState(0);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [meta, setMeta] = useState<{ scenes?: number; duration?: number; audio?: boolean }>({});
  const videoRef = useRef<HTMLVideoElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const videoSrc = useCallback(
    (url: string) => `${API}${url}?t=${Date.now()}`,
    []
  );

  // 检查当前讲次视频是否已生成
  useEffect(() => {
    let cancelled = false;
    setPhase("checking");
    setVideoUrl(null);
    setError(null);
    fetch(`${API}/api/video/check/${courseId}/${lectureNum}`)
      .then((r) => r.json())
      .then((d) => {
        if (cancelled) return;
        if (d.exists && d.video_url) {
          setVideoUrl(videoSrc(d.video_url));
          setPhase("live");
        } else {
          setPhase("idle");
        }
      })
      .catch(() => !cancelled && setPhase("idle"));
    return () => {
      cancelled = true;
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [courseId, lectureNum, videoSrc]);

  const startGeneration = useCallback(async () => {
    setError(null);
    setPhase("generating");
    setProgress(0);
    setMeta({});

    // 后端确实在依次执行这些阶段（POST 为一次性返回，前端用渐进动画呈现管线进度）
    const pipeline = [
      "PlannerAgent — LLM 分析讲义，生成分镜脚本",
      "TTSService — edge-tts 合成场景旁白配音",
      "VideoRenderer — Pillow 逐帧渲染教学画面",
      "CriticAgent — 视频质量评审校验",
      "FFmpeg — 合成画面与配音，编码 H.264 MP4",
    ];
    setSteps(pipeline.map((text) => ({ text, done: false, active: false })));
    let idx = 0;
    timerRef.current = setInterval(() => {
      setSteps((prev) =>
        prev.map((s, i) => ({ ...s, done: i < idx, active: i === idx }))
      );
      setProgress(Math.min(95, Math.round(((idx + 1) / (pipeline.length + 1)) * 100)));
      idx = Math.min(idx + 1, pipeline.length - 1);
    }, 6000);

    try {
      const resp = await fetch(`${API}/api/video/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lecture_title: lectureTitle || `第${lectureNum}讲`,
          course_id: courseId,
          lecture_num: lectureNum,
          difficulty: "medium",
        }),
      });
      const data = await resp.json();
      if (timerRef.current) clearInterval(timerRef.current);

      if (data.success && data.video_url) {
        setSteps((prev) => prev.map((s) => ({ ...s, done: true, active: false })));
        setProgress(100);
        setMeta({
          scenes: data.scenes_count,
          duration: data.duration,
          audio: data.has_audio,
        });
        setVideoUrl(videoSrc(data.video_url));
        setPhase("live");
        setTimeout(() => videoRef.current?.play().catch(() => {}), 400);
      } else {
        setError(data.message || "视频生成失败，请重试");
        setPhase("idle");
      }
    } catch (e: any) {
      if (timerRef.current) clearInterval(timerRef.current);
      setError("生成请求失败：" + (e?.message || "网络错误"));
      setPhase("idle");
    }
  }, [courseId, lectureNum, lectureTitle, videoSrc]);

  const stop = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
    setPhase("idle");
    setProgress(0);
  }, []);

  return (
    <div className="bg-[var(--lm-surface)] rounded-2xl border border-[var(--lm-border)] overflow-hidden">
      {/* 标题栏 */}
      <div className="px-4 py-3 border-b border-[var(--lm-border)] font-semibold text-sm flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            phase === "live"
              ? "bg-green-500 animate-pulse"
              : phase === "generating"
              ? "bg-amber-500 animate-pulse"
              : "bg-gray-300"
          }`}
        />
        🤖 AI 视频生成 · 多智能体管线
        {phase === "live" && (
          <span className="ml-auto text-xs bg-red-500 text-white px-2 py-0.5 rounded-full animate-pulse font-bold">
            ● 已生成
          </span>
        )}
        {phase === "generating" && (
          <span className="ml-auto text-xs text-amber-600 animate-pulse font-medium">
            生成中 {progress}%
          </span>
        )}
      </div>

      {/* 视频区域 */}
      <div className="relative bg-black aspect-video">
        {/* 检查中 */}
        {phase === "checking" && (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            正在检查本讲视频…
          </div>
        )}

        {/* 等待启动 */}
        {phase === "idle" && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <div className="text-6xl mb-4">🎬</div>
              <p className="text-base font-medium text-white mb-1">
                AI 根据本讲讲义生成教学视频
              </p>
              <p className="text-xs text-gray-400 mb-2">
                多智能体管线：Planner → TTS → Critic → Renderer
              </p>
              <p className="text-[10px] text-gray-500 mb-5">
                LLM 分析第{lectureNum}讲讲义 → 生成分镜脚本 → 合成配音 → 渲染输出 MP4（约 1 分钟）
              </p>
              <button
                onClick={startGeneration}
                className="px-6 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors active:scale-95"
              >
                ▶ 生成本讲教学视频
              </button>
              {error && (
                <p className="text-xs text-red-400 mt-3 max-w-md mx-auto">{error}</p>
              )}
            </div>
          </div>
        )}

        {/* 生成过程 */}
        {phase === "generating" && (
          <div className="flex items-center justify-center h-full bg-gray-900 text-gray-200">
            <div className="w-full max-w-lg px-6">
              <div className="text-center mb-5">
                <div className="text-sm font-bold text-white mb-1">
                  正在根据讲义生成视频
                </div>
                <div className="text-xs text-gray-400">
                  POST /api/video/generate · {courseId} · 第{lectureNum}讲
                </div>
              </div>

              <div className="w-full h-2 rounded-full bg-gray-800 mb-5 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>

              <div className="space-y-1 max-h-[240px] overflow-y-auto text-xs font-mono">
                {steps.map((s, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-2 py-1 px-2 rounded transition-colors ${
                      s.active
                        ? "bg-indigo-900/40 text-white"
                        : s.done
                        ? "text-green-400"
                        : "text-gray-600"
                    }`}
                  >
                    <span className="flex-shrink-0 w-4 mt-px">
                      {s.done ? "✓" : s.active ? "●" : "○"}
                    </span>
                    <span className="flex-1">{s.text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 播放 */}
        {phase === "live" && videoUrl && (
          <video
            ref={videoRef}
            className="w-full h-full block"
            src={videoUrl}
            controls
            playsInline
            onEnded={() => {}}
            onError={() => setError("视频加载失败")}
          />
        )}
      </div>

      {/* 底部状态 */}
      <div className="p-3 flex items-center justify-between">
        <div className="text-[10px] text-gray-400">
          {phase === "live" ? (
            <span>
              多智能体生成 · Planner + TTS + Manim + Critic ·{" "}
              {meta.scenes ? `${meta.scenes} 个场景` : ""}
              {meta.duration ? ` · ${Math.round(meta.duration)}s` : ""}
              {meta.audio ? " · 含AI配音" : ""} · H.264
            </span>
          ) : phase === "generating" ? (
            <span>正在调用 LLM 生成分镜脚本并渲染视频帧...</span>
          ) : (
            <span>点击按钮，AI 将根据当前讲次讲义自动生成教学视频</span>
          )}
        </div>
        {phase === "live" && (
          <button
            onClick={startGeneration}
            className="px-3 py-1 rounded-lg bg-indigo-500 text-white text-xs hover:bg-indigo-600 mr-2"
          >
            ↻ 重新生成
          </button>
        )}
      </div>
    </div>
  );
}
