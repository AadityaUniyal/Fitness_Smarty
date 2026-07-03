import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';

interface VoiceLoggerProps {
  onTranscript: (transcript: string) => void;
}

export const VoiceLogger: React.FC<VoiceLoggerProps> = ({ onTranscript }) => {
  const [isListening, setIsListening] = useState(false);
  const [supported, setSupported] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      setSupported(true);
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = 'en-US';

      rec.onstart = () => setIsListening(true);
      rec.onend = () => setIsListening(false);
      rec.onerror = () => setIsListening(false);
      rec.onresult = (event: any) => {
        const text = event.results[0][0].transcript;
        if (text) {
          onTranscript(text);
        }
      };

      setRecognition(rec);
    }
  }, [onTranscript]);

  const toggleListen = () => {
    if (!supported || !recognition) return;
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  };

  if (!supported) return null;

  return (
    <button
      onClick={toggleListen}
      className={`p-3 rounded-2xl flex items-center justify-center transition-all ${
        isListening
          ? 'bg-rose-500/20 border border-rose-500/30 text-rose-400 animate-pulse'
          : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20'
      }`}
      title={isListening ? 'Stop Listening' : 'Log Meal by Voice'}
      aria-label="Toggle voice microphone logger"
    >
      {isListening ? <MicOff size={16} /> : <Mic size={16} />}
    </button>
  );
};
export default VoiceLogger;
