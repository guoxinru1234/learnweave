'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type JourneyStep = {
  id: number;
  label: string;
  icon: string;
  href: string;
  completed: boolean;
  active: boolean;
};

type JourneyContextType = {
  steps: JourneyStep[];
  currentStep: JourneyStep | null;
  nextStep: JourneyStep | null;
  progress: number;
  loading: boolean;
  completeStep: (stepId: number) => Promise<void>;
  refreshJourney: () => Promise<void>;
};

const JourneyContext = createContext<JourneyContextType | undefined>(undefined);

export function JourneyProvider({ children }: { children: ReactNode }) {
  const [steps, setSteps] = useState<JourneyStep[]>([]);
  const [currentStep, setCurrentStep] = useState<JourneyStep | null>(null);
  const [nextStep, setNextStep] = useState<JourneyStep | null>(null);
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchJourney = async () => {
    try {
      const res = await fetch('/api/journey');
      const data = await res.json();
      setSteps(data.steps);
      setProgress(data.overall_progress);
      setCurrentStep(data.steps.find((s: JourneyStep) => s.active) || data.steps[0]);
      const next = data.steps.find((s: JourneyStep) => !s.completed);
      setNextStep(next || null);
    } catch (error) {
      console.error('获取学习旅程失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const completeStep = async (stepId: number) => {
    try {
      await fetch('/api/journey/complete-step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step_id: stepId })
      });
      await fetchJourney();
    } catch (error) {
      console.error('完成步骤失败:', error);
    }
  };

  useEffect(() => {
    fetchJourney();

    // SSE 监听实时更新
    const eventSource = new EventSource('/api/events/stream');
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'event' && data.event.type === 'JOURNEY_UPDATED') {
        fetchJourney();
      }
    };

    return () => eventSource.close();
  }, []);

  return (
    <JourneyContext.Provider value={{
      steps,
      currentStep,
      nextStep,
      progress,
      loading,
      completeStep,
      refreshJourney: fetchJourney
    }}>
      {children}
    </JourneyContext.Provider>
  );
}

export function useJourney() {
  const context = useContext(JourneyContext);
  if (!context) {
    throw new Error('useJourney must be used within JourneyProvider');
  }
  return context;
}