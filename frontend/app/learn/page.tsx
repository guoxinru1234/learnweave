'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

const FALLBACK_COURSE_ID = 'python-data-analysis';

export default function LearnPage() {
  const router = useRouter();

  useEffect(() => {
    const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    fetch(`${API}/api/courses`, { signal: controller.signal })
      .then(res => res.json())
      .then(data => {
        clearTimeout(timeoutId);
        if (data.success && data.courses?.length > 0) {
          router.replace(`/learn/${data.courses[0].id}`);
        } else {
          router.replace(`/learn/${FALLBACK_COURSE_ID}`);
        }
      })
      .catch(() => {
        clearTimeout(timeoutId);
        router.replace(`/learn/${FALLBACK_COURSE_ID}`);
      });
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-3 border-[#08b8bd] border-t-transparent mx-auto mb-3" />
        <p className="text-gray-400 text-sm">进入学习空间...</p>
      </div>
    </div>
  );
}
