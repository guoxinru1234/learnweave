"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { DigitalHuman } from "./DigitalHuman";

type AvatarState = "idle" | "speaking" | "thinking" | "greeting";

interface TalkingAvatarControllerProps {
  size?: number;
  className?: string;
  speakTrigger?: number;
  contentToSpeak?: string;
  /** 朗读开始时回调，用于静音视频等 */
  onSpeakStart?: () => void;
  /** 朗读结束时回调 */
  onSpeakEnd?: () => void;
}

/**
 * 数字人 + 浏览器原生 TTS
 * 浏览器 SpeechSynthesis 声音远比 pyttsx3 自然
 */
function TalkingAvatarController({ size = 180, className = "", speakTrigger, contentToSpeak, onSpeakStart, onSpeakEnd }: TalkingAvatarControllerProps) {
    const [state, setState] = useState<AvatarState>("idle");
    const [subtitle, setSubtitle] = useState("");
    const speakingRef = useRef(false);
    const queueRef = useRef<string[]>([]);

    // Ensure voices are loaded (some browsers load them async)
    const [voicesReady, setVoicesReady] = useState(false);
    useEffect(() => {
      const loadVoices = () => {
        const voices = speechSynthesis.getVoices();
        if (voices.length > 0) {
          setVoicesReady(true);
        }
      };
      loadVoices();
      speechSynthesis.onvoiceschanged = () => {
        setVoicesReady(true);
      };
    }, []);

    const getBestVoice = useCallback((): SpeechSynthesisVoice | null => {
      const voices = speechSynthesis.getVoices();
      if (voices.length === 0) return null;
      // Prefer Chinese female voices
      for (const name of ["Xiaoxiao", "Huihui", "Yaoyao", "Kangkang"]) {
        const v = voices.find(x => x.lang.startsWith("zh") && x.name.includes(name));
        if (v) return v;
      }
      // Any Chinese voice
      return voices.find(x => x.lang.startsWith("zh")) || voices[0];
    }, []);

    const speak = useCallback((text: string) => {
      if (!text?.trim()) return;
      speechSynthesis.cancel();
      speakingRef.current = true;
      setState("speaking");
      onSpeakStart?.();

      const doSpeak = () => {
        const u = new SpeechSynthesisUtterance(text);
        u.lang = "zh-CN";
        u.rate = 0.95;
        u.pitch = 1.1;
        u.volume = 1;
        const voice = getBestVoice();
        if (voice) u.voice = voice;

        // Update blackboard text as speech progresses
        let lastChar = 0;
        u.onboundary = (e) => {
          if (e.charIndex !== undefined) {
            const pos = e.charIndex + (e.charLength || 0);
            if (pos > lastChar) {
              lastChar = pos;
              const displayEnd = Math.min(text.length, pos + 15);
              setSubtitle(text.slice(0, displayEnd));
            }
          }
        };

        u.onend = () => {
          speakingRef.current = false;
          setState("idle");
          setSubtitle("");
          onSpeakEnd?.();
          if (queueRef.current.length > 0) {
            const next = queueRef.current.shift()!;
            setTimeout(() => speak(next), 300);
          }
        };
        u.onerror = (e) => {
          console.warn("[TalkingAvatar] Speech error:", e.error);
          speakingRef.current = false;
          setState("idle");
          onSpeakEnd?.();
        };

        speechSynthesis.speak(u);
      };

      // If voices aren't loaded yet, wait briefly and retry
      if (speechSynthesis.getVoices().length === 0) {
        const checkInterval = setInterval(() => {
          if (speechSynthesis.getVoices().length > 0) {
            clearInterval(checkInterval);
            doSpeak();
          }
        }, 200);
        // Timeout after 3 seconds
        setTimeout(() => {
          clearInterval(checkInterval);
          if (speakingRef.current) doSpeak(); // Speak even without Chinese voice
        }, 3000);
      } else {
        doSpeak();
      }
    }, [getBestVoice, onSpeakStart, onSpeakEnd]);

    const speakSequence = useCallback(async (texts: string[]) => {
      if (!texts.length) return;
      speechSynthesis.cancel();
      queueRef.current = [...texts];
      const first = queueRef.current.shift()!;
      speak(first);
      // Wait for queue to drain
      await new Promise<void>(resolve => {
        const check = setInterval(() => {
          if (!speakingRef.current && queueRef.current.length === 0) {
            clearInterval(check);
            resolve();
          }
        }, 500);
      });
    }, [speak]);

    const stop = useCallback(() => {
      speechSynthesis.cancel();
      queueRef.current = [];
      speakingRef.current = false;
      setState("idle");
      setSubtitle("");
    }, []);

    // Auto-speak when speakTrigger changes
    useEffect(() => {
      if (speakTrigger && speakTrigger > 0 && contentToSpeak) {
        stop();
        setTimeout(() => speak(contentToSpeak), 200);
      }
    }, [speakTrigger]);

    return (
      <div className={`relative mx-auto ${className}`} style={{ width: size * 3, height: size * 1.2 }}>
        {/* 黑板背景 */}
        <div className="absolute inset-0 bg-[#1a2a1f] rounded-xl shadow-xl border-[3px] border-amber-700/40 overflow-hidden">
          <div className="absolute inset-0 flex items-center justify-center p-6 pr-36">
            {subtitle ? (
              <p
                className="text-center text-white/85 leading-relaxed transition-opacity duration-300"
                style={{
                  fontSize: size * 0.11,
                  fontFamily: "'Segoe Script', 'KaiTi', 'Comic Sans MS', cursive",
                  textShadow: "0 1px 2px rgba(255,255,255,0.2)",
                  lineHeight: 1.6,
                }}
              >
                {subtitle}
              </p>
            ) : (
              <p className="text-center text-white/15 text-sm italic"
                style={{ fontSize: size * 0.1, fontFamily: "'KaiTi', serif" }}>
                点 AI 朗读，开始上课...
              </p>
            )}
          </div>
        </div>
        {/* 老师站在黑板前 */}
        <div className="absolute -bottom-2 -right-4 z-10">
          <DigitalHuman state={state} size={size * 0.75} onClick={stop} />
        </div>
      </div>
    );
}

export { TalkingAvatarController };
