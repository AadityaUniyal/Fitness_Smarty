import React, { useState, useRef } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { transcribeVoiceAudio } from '../services/geminiService';

interface VoiceLoggerProps {
  onTranscript: (transcript: string) => void;
  mode?: 'general' | 'meal' | 'workout';
}

export const VoiceLogger: React.FC<VoiceLoggerProps> = ({ onTranscript, mode = 'meal' }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Stop all tracks to release mic
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType || 'audio/webm' });
        if (audioBlob.size > 0) {
          setIsProcessing(true);
          try {
            const res = await transcribeVoiceAudio(audioBlob, mode);
            if (res.transcript) {
              onTranscript(res.transcript);
            }
          } catch (err) {
            console.error('Deepgram transcription error:', err);
          } finally {
            setIsProcessing(false);
          }
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.warn('Microphone access unavailable or denied:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isProcessing) return;
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <button
      type="button"
      onClick={toggleRecording}
      disabled={isProcessing}
      className={`p-3 rounded-2xl flex items-center justify-center transition-all ${
        isRecording
          ? 'bg-rose-500/20 border border-rose-500/30 text-rose-400 animate-pulse'
          : isProcessing
          ? 'bg-amber-500/20 border border-amber-500/30 text-amber-400'
          : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20'
      }`}
      title={isRecording ? 'Stop Recording Voice' : isProcessing ? 'Processing with Deepgram...' : 'Record Voice with Deepgram'}
      aria-label="Toggle voice microphone logger"
    >
      {isProcessing ? (
        <Loader2 size={16} className="animate-spin text-amber-400" />
      ) : isRecording ? (
        <MicOff size={16} />
      ) : (
        <Mic size={16} />
      )}
    </button>
  );
};

export default VoiceLogger;
