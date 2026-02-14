
import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Loader2, Sparkles, MessageCircle, Info } from 'lucide-react';
import { createChat } from './geminiService';

interface Message {
  role: 'user' | 'model';
  text: string;
}

const SmartyChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'model', text: 'Hello! I am Smarty, your personal AI fitness consultant. How can I assist you in reaching your goals today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatRef = useRef<any>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatRef.current = createChat();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
    setLoading(true);

    try {
      if (!chatRef.current) chatRef.current = createChat();
      const response = await chatRef.current.sendMessage({ message: userMessage });
      setMessages(prev => [...prev, { role: 'model', text: response.text || "I'm sorry, I couldn't process that." }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'model', text: "Connection error. Please try again later." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-12rem)] flex flex-col bg-slate-900/40 border border-slate-800 rounded-[2.5rem] overflow-hidden animate-in zoom-in-95 duration-500">
      {/* Chat Header */}
      <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50 backdrop-blur-md">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-slate-950 shadow-lg shadow-emerald-500/20">
            <Bot size={28} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Smarty Expert Chat</h3>
            <p className="text-xs text-emerald-400 flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-2 animate-pulse"></span>
              Online & Ready
            </p>
          </div>
        </div>
        <div className="flex space-x-2">
            <div className="bg-slate-800 p-2 rounded-xl border border-slate-700 text-slate-400 cursor-help" title="Ask about workouts, diet, or recovery">
                <Info size={18} />
            </div>
        </div>
      </div>

      {/* Messages Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth"
      >
        {messages.map((msg, i) => (
          <div 
            key={i} 
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2`}
          >
            <div className={`flex max-w-[85%] space-x-3 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 ${
                msg.role === 'user' ? 'bg-slate-800 text-slate-400' : 'bg-emerald-500 text-slate-950'
              }`}>
                {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
              </div>
              <div className={`p-4 rounded-3xl ${
                msg.role === 'user' 
                  ? 'bg-emerald-500 text-slate-950 font-medium' 
                  : 'bg-slate-800 text-slate-200 border border-slate-700/50'
              }`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
             <div className="bg-slate-800 p-4 rounded-3xl flex items-center space-x-2 border border-slate-700/50">
               <Loader2 size={16} className="animate-spin text-emerald-400" />
               <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Smarty is thinking...</span>
             </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSend} className="p-6 bg-slate-900/50 backdrop-blur-md border-t border-slate-800">
        <div className="relative">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything... 'What should I eat for a slim body?'"
            className="w-full bg-slate-800 border border-slate-700 rounded-2xl py-4 pl-6 pr-16 text-sm focus:outline-none focus:border-emerald-500/50 transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute right-2 top-2 p-3 bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-700 text-slate-950 rounded-xl transition-all shadow-lg shadow-emerald-500/10"
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  );
};

export default SmartyChat;
