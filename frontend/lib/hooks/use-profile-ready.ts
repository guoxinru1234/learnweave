"use client";

import { useState, useEffect } from "react";

/**
 * 检查当前用户的学情画像是否已完成。
 * 所有页面用这个 hook 判断——画像未完成则显示空状态/引导。
 */
export function useProfileReady(userId: number | undefined) {
  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<any>(null);

  useEffect(() => {
    if (!userId) { setLoading(false); return; }
    const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";
    fetch(`${API}/api/profile?user_id=${userId}`)
      .then(r => r.json())
      .then(p => {
        setProfile(p);
        // 画像完成条件：对话完成 或 总分>0（有任意维度被评估过）
        const hasScore = (p.theoretical_basis || 0) > 0
          || (p.coding_ability || 0) > 0
          || (p.practical_ops || 0) > 0
          || (p.troubleshooting || 0) > 0
          || (p.data_thinking || 0) > 0
          || (p.self_learning || 0) > 0;
        setReady(!!p.dialogue_completed || hasScore);
      })
      .catch(() => setReady(false))
      .finally(() => setLoading(false));
  }, [userId]);

  return { ready, loading, profile };
}
