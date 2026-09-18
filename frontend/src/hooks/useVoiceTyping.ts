"use client";

import * as React from "react";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";

interface UseVoiceTypingOptions {
  onTranscript: (transcript: string, isFinal?: boolean) => void;
  onToast?: (message: string) => void;
  language?: string;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message?: string;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: {
    length: number;
    [index: number]: {
      isFinal: boolean;
      [index: number]: {
        transcript: string;
        confidence: number;
      };
    };
  };
}

interface ISpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

interface FallbackItem {
  from: string;
  to: string;
  reason: string;
  toast?: string;
}

interface TranscribeSuccessData {
  transcript: string;
  provider: string;
  latency_ms?: number;
  fallbacks?: FallbackItem[];
}

export function useVoiceTyping({
  onTranscript,
  onToast,
  language = "en-US",
}: UseVoiceTypingOptions) {
  const [isListening, setIsListening] = React.useState(false);
  const [isTranscribing, setIsTranscribing] = React.useState(false);
  const [layer, setLayer] = React.useState<"layer1_webspeech" | "layer2_backend" | null>(null);

  const recognitionRef = React.useRef<ISpeechRecognition | null>(null);
  const mediaRecorderRef = React.useRef<MediaRecorder | null>(null);
  const audioChunksRef = React.useRef<Blob[]>([]);
  const streamRef = React.useRef<MediaStream | null>(null);
  const maxDurationTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const startTimeRef = React.useRef<number>(0);

  const recordVoiceTranscription = usePlaygroundStore((s) => s.recordVoiceTranscription);

  // Check whether browser is Chromium-based (Chrome / Edge)
  const isChromeOrEdge = React.useMemo(() => {
    if (typeof window === "undefined" || typeof navigator === "undefined") return false;
    const ua = navigator.userAgent;
    const hasChrome = /Chrome|CriOS/.test(ua);
    const hasEdge = /Edg\//.test(ua);
    const isSafariOnly = /Safari/.test(ua) && !hasChrome && !hasEdge;
    const isFirefox = /Firefox|FxiOS/.test(ua);
    return (hasChrome || hasEdge) && !isSafariOnly && !isFirefox;
  }, []);

  // Cleanup helper
  const cleanupStream = React.useCallback(() => {
    if (maxDurationTimeoutRef.current) {
      clearTimeout(maxDurationTimeoutRef.current);
      maxDurationTimeoutRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
  }, []);

  // Backend Fallback Transcription (Layer 2)
  const transcribeAudioBlob = React.useCallback(
    async (blob: Blob, mimeType: string) => {
      setIsTranscribing(true);
      const startMs = performance.now();

      try {
        const formData = new FormData();
        const ext = mimeType.includes("mp4") ? "mp4" : mimeType.includes("ogg") ? "ogg" : "webm";
        formData.append("file", blob, `voice_recording.${ext}`);
        if (language) {
          formData.append("language", language);
        }

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "";
        const res = await fetch(`${apiUrl}/api/v1/voice/transcribe`, {
          method: "POST",
          body: formData,
        });

        if (res.ok) {
          const data: TranscribeSuccessData = await res.json();
          const latency = data.latency_ms || Math.round(performance.now() - startMs);

          // If fallback occurred, show tiny non-blocking toast(s)
          if (Array.isArray(data.fallbacks) && data.fallbacks.length > 0) {
            data.fallbacks.forEach((fb: FallbackItem) => {
              const toastMsg =
                fb.toast ||
                (fb.from === "groq" && fb.to === "gemini"
                  ? "Groq busy → switching to Gemini"
                  : fb.from === "gemini" && fb.to === "openrouter"
                  ? "Gemini busy → switching to OpenRouter"
                  : `${fb.from} busy → switching to ${fb.to}`);
              onToast?.(toastMsg);
            });
          }

          if (data.transcript) {
            onTranscript(data.transcript, true);
          }

          recordVoiceTranscription(
            data.provider,
            latency,
            (data.fallbacks || []).map((fb) => ({
              from: fb.from,
              to: fb.to,
              reason: fb.reason || "Switching provider",
              toast: fb.toast,
            }))
          );
        } else {
          // All providers failed or server error
          const errData = (await res.json().catch(() => null)) as { detail?: { message?: string } } | null;
          const allFailMsg =
            errData?.detail?.message ||
            "Voice transcription unavailable right now. Please type or try again in a minute.";
          onToast?.(allFailMsg);
        }
      } catch (err: unknown) {
        console.error("Voice transcription network error:", err);
        onToast?.("Voice transcription unavailable right now. Please type or try again in a minute.");
      } finally {
        setIsTranscribing(false);
      }
    },
    [language, onToast, onTranscript, recordVoiceTranscription]
  );

  // Start Layer 2 MediaRecorder recording
  const startMediaRecorder = React.useCallback(async () => {
    cleanupStream();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      let mimeType = "audio/webm";
      if (typeof MediaRecorder !== "undefined") {
        if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
          mimeType = "audio/webm;codecs=opus";
        } else if (MediaRecorder.isTypeSupported("audio/webm")) {
          mimeType = "audio/webm";
        } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
          mimeType = "audio/mp4";
        } else if (MediaRecorder.isTypeSupported("audio/ogg")) {
          mimeType = "audio/ogg";
        }
      }

      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];
      startTimeRef.current = performance.now();

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        cleanupStream();
        setIsListening(false);
        if (audioBlob.size > 0) {
          transcribeAudioBlob(audioBlob, mimeType);
        }
      };

      recorder.start(250); // Slice every 250ms
      setIsListening(true);
      setLayer("layer2_backend");

      // Auto stop after 15s max duration
      maxDurationTimeoutRef.current = setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
          mediaRecorderRef.current.stop();
        }
      }, 15000);
    } catch (err: unknown) {
      console.error("Microphone access error:", err);
      setIsListening(false);
      onToast?.("Microphone permission denied or unavailable.");
      cleanupStream();
    }
  }, [cleanupStream, onToast, transcribeAudioBlob]);

  // Start Layer 1 Web Speech API (Chrome / Edge)
  const startWebSpeech = React.useCallback(() => {
    if (typeof window === "undefined") return;

    const win = window as unknown as {
      SpeechRecognition?: new () => ISpeechRecognition;
      webkitSpeechRecognition?: new () => ISpeechRecognition;
    };
    const SpeechRecognitionClass = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      // Fallback directly to Layer 2 MediaRecorder
      startMediaRecorder();
      return;
    }

    try {
      const recognition = new SpeechRecognitionClass();
      recognitionRef.current = recognition;
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = language;
      startTimeRef.current = performance.now();

      let finalTranscript = "";

      recognition.onstart = () => {
        setIsListening(true);
        setLayer("layer1_webspeech");
      };

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let interimTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const part = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += (finalTranscript ? " " : "") + part;
          } else {
            interimTranscript += part;
          }
        }
        const fullTranscript = finalTranscript + (interimTranscript ? ` ${interimTranscript}` : "");
        if (fullTranscript) {
          onTranscript(fullTranscript, false);
        }
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.warn("Web Speech API event error:", event.error);
        recognition.stop();
        setIsListening(false);

        // If Web Speech API fails (e.g. network, not-allowed, service-not-allowed), fallback to Layer 2
        if (event.error !== "no-speech") {
          startMediaRecorder();
        }
      };

      recognition.onend = () => {
        setIsListening(false);
        const duration = Math.round(performance.now() - startTimeRef.current);
        if (finalTranscript) {
          onTranscript(finalTranscript, true);
          recordVoiceTranscription("webSpeech", duration);
        }
      };

      recognition.start();

      // Auto stop after 15s max duration
      maxDurationTimeoutRef.current = setTimeout(() => {
        if (recognitionRef.current) {
          recognitionRef.current.stop();
        }
      }, 15000);
    } catch (err: unknown) {
      console.warn("Could not start Web Speech API, falling back to Layer 2:", err);
      startMediaRecorder();
    }
  }, [language, onTranscript, recordVoiceTranscription, startMediaRecorder]);

  // Main start handler
  const startListening = React.useCallback(() => {
    if (isListening || isTranscribing) return;

    if (isChromeOrEdge) {
      startWebSpeech();
    } else {
      startMediaRecorder();
    }
  }, [isChromeOrEdge, isListening, isTranscribing, startMediaRecorder, startWebSpeech]);

  // Main stop handler
  const stopListening = React.useCallback(() => {
    if (maxDurationTimeoutRef.current) {
      clearTimeout(maxDurationTimeoutRef.current);
      maxDurationTimeoutRef.current = null;
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore
      }
      recognitionRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      try {
        mediaRecorderRef.current.stop();
      } catch {
        // Ignore
      }
    } else {
      cleanupStream();
      setIsListening(false);
    }
  }, [cleanupStream]);

  const toggleListening = React.useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  React.useEffect(() => {
    return () => {
      stopListening();
      cleanupStream();
    };
  }, [cleanupStream, stopListening]);

  return {
    isListening,
    isTranscribing,
    layer,
    startListening,
    stopListening,
    toggleListening,
  };
}
