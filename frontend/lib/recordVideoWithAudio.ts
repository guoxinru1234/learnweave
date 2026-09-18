/** 浏览器端录制：视频 + TTS 语音 → MP4 */

export async function addAudioToVideo(
  videoElement: HTMLVideoElement,
  voiceTexts: string[],
  onProgress?: (current: number, total: number) => void
): Promise<Blob> {
  // 创建离屏 canvas 捕获视频帧
  const canvas = document.createElement("canvas");
  canvas.width = videoElement.videoWidth || 1280;
  canvas.height = videoElement.videoHeight || 720;
  const ctx = canvas.getContext("2d")!;

  // 录制 canvas 流
  const canvasStream = canvas.captureStream(30);
  const audioCtx = new AudioContext();
  const dest = audioCtx.createMediaStreamDestination();
  const mediaStream = new MediaStream([
    ...canvasStream.getVideoTracks(),
    ...dest.stream.getAudioTracks(),
  ]);

  const recorder = new MediaRecorder(mediaStream, { mimeType: "video/webm;codecs=vp9" });
  const chunks: Blob[] = [];
  recorder.ondataavailable = (e) => chunks.push(e.data);

  return new Promise((resolve) => {
    const finished = () => {
      recorder.stop();
      resolve(new Blob(chunks, { type: "video/webm" }));
    };

    recorder.start();

    // Play video + speak each text in sequence
    const speakNext = async (index: number) => {
      if (index >= voiceTexts.length) {
        finished();
        return;
      }
      onProgress?.(index + 1, voiceTexts.length);

      const text = voiceTexts[index];
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "zh-CN";
      utterance.rate = 0.95;
      const voices = speechSynthesis.getVoices();
      const zh = voices.find(v => v.lang.startsWith("zh"));
      if (zh) utterance.voice = zh;

      utterance.onend = () => speakNext(index + 1);
      utterance.onerror = () => speakNext(index + 1);
      speechSynthesis.speak(utterance);
    };

    videoElement.currentTime = 0;
    videoElement.muted = true; // Mute original
    videoElement.play();

    // When video starts playing, begin narration
    videoElement.onplaying = () => {
      // Start drawing frames
      const draw = () => {
        if (videoElement.paused && videoElement.ended) return;
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        requestAnimationFrame(draw);
      };
      draw();
      speakNext(0);
    };

    // Stop when video ends
    videoElement.onended = () => {
      speechSynthesis.cancel();
      finished();
    };
  });
}
