import React from 'react';
import { Zap, Github, Linkedin, Mail, Code2, Cpu, Globe, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const ContactPage: React.FC = () => {
    const navigate = useNavigate();

    const techStack = [
        { name: 'React + Vite', color: 'cyan' },
        { name: 'TypeScript', color: 'blue' },
        { name: 'FastAPI', color: 'emerald' },
        { name: 'Gemini AI', color: 'purple' },
        { name: 'SQLAlchemy', color: 'orange' },
        { name: 'TailwindCSS', color: 'cyan' },
        { name: 'PostgreSQL', color: 'blue' },
        { name: 'Docker', color: 'blue' },
    ];

    return (
        <div className="min-h-screen bg-[#020617] text-white">
            {/* Background */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl" />
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 max-w-4xl mx-auto px-6 py-16">
                {/* Back */}
                <button onClick={() => navigate('/dashboard')}
                    className="flex items-center space-x-2 text-slate-500 hover:text-emerald-400 transition-colors mb-12 font-black text-[10px] uppercase tracking-widest group">
                    <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
                    <span>Back to Dashboard</span>
                </button>

                {/* Hero Card */}
                <div className="relative bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950/30 border border-white/10 rounded-[2.5rem] p-10 mb-8 overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-2xl -mr-32 -mt-32" />
                    <div className="absolute bottom-0 left-0 w-48 h-48 bg-cyan-500/5 rounded-full blur-2xl -ml-24 -mb-24" />

                    <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center gap-8">
                        {/* Avatar */}
                        <div className="relative">
                            <div className="absolute -inset-2 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-3xl blur-lg opacity-30" />
                            <div className="relative w-28 h-28 bg-slate-800 rounded-3xl border border-white/20 flex items-center justify-center text-5xl">
                                👨‍💻
                            </div>
                        </div>

                        <div className="flex-1">
                            <p className="text-[9px] font-black uppercase tracking-[0.4em] text-emerald-400 mb-2">Builder & Developer</p>
                            <h1 className="text-5xl font-black italic tracking-tighter text-white mb-1">Aaditya Uniyal</h1>
                            <p className="text-slate-400 text-sm mt-3 max-w-lg leading-relaxed">
                                AI & Full-Stack Developer passionate about building intelligent fitness systems that make healthy living accessible and data-driven for everyone.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Links */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    <a href="https://github.com/AadityaUniyal" target="_blank" rel="noopener noreferrer"
                        className="group flex items-center space-x-4 p-6 bg-slate-900 border border-white/10 hover:border-white/30 rounded-2xl transition-all hover:-translate-y-1 hover:shadow-2xl">
                        <div className="w-12 h-12 bg-slate-800 rounded-2xl flex items-center justify-center group-hover:bg-white/10 transition-colors">
                            <Github size={24} className="text-white" />
                        </div>
                        <div>
                            <p className="font-black text-sm text-white">GitHub</p>
                            <p className="text-xs text-slate-500">AadityaUniyal</p>
                        </div>
                    </a>

                    <a href="https://www.linkedin.com/in/aaditya-uniyal-48ab7b342/" target="_blank" rel="noopener noreferrer"
                        className="group flex items-center space-x-4 p-6 bg-slate-900 border border-white/10 hover:border-blue-500/40 rounded-2xl transition-all hover:-translate-y-1 hover:shadow-2xl">
                        <div className="w-12 h-12 bg-blue-950 rounded-2xl flex items-center justify-center group-hover:bg-blue-900 transition-colors">
                            <Linkedin size={24} className="text-blue-400" />
                        </div>
                        <div>
                            <p className="font-black text-sm text-white">LinkedIn</p>
                            <p className="text-xs text-slate-500">aaditya-uniyal</p>
                        </div>
                    </a>

                    <div className="group flex items-center space-x-4 p-6 bg-slate-900 border border-white/10 rounded-2xl">
                        <div className="w-12 h-12 bg-emerald-950 rounded-2xl flex items-center justify-center">
                            <Mail size={24} className="text-emerald-400" />
                        </div>
                        <div>
                            <p className="font-black text-sm text-white">Project</p>
                            <p className="text-xs text-slate-500">Smarty-Reco</p>
                        </div>
                    </div>
                </div>

                {/* Project Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                    <div className="p-8 bg-slate-900 border border-white/10 rounded-2xl">
                        <div className="flex items-center space-x-3 mb-4">
                            <Cpu size={20} className="text-emerald-400" />
                            <h3 className="font-black text-sm uppercase tracking-widest text-white">About Smarty AI</h3>
                        </div>
                        <p className="text-slate-400 text-sm leading-relaxed">
                            Smarty-Reco is an AI-powered fitness intelligence platform using Google's Gemini Vision AI for real-time food analysis, personalized workout generation, and 24/7 health coaching — all tailored to each user's unique goals.
                        </p>
                    </div>

                    <div className="p-8 bg-slate-900 border border-white/10 rounded-2xl">
                        <div className="flex items-center space-x-3 mb-4">
                            <Code2 size={20} className="text-cyan-400" />
                            <h3 className="font-black text-sm uppercase tracking-widest text-white">Tech Stack</h3>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {techStack.map(t => (
                                <span key={t.name} className={`px-3 py-1.5 bg-${t.color}-500/10 border border-${t.color}-500/20 text-${t.color}-400 rounded-xl text-[10px] font-black uppercase tracking-wider`}>
                                    {t.name}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Open Source Strip */}
                <div className="flex items-center justify-between p-6 bg-gradient-to-r from-emerald-950/50 to-slate-900 border border-emerald-500/20 rounded-2xl">
                    <div className="flex items-center space-x-4">
                        <Globe size={20} className="text-emerald-400" />
                        <div>
                            <p className="text-sm font-black text-white">Open Source Project</p>
                            <p className="text-xs text-slate-500">MIT License — contributions welcome</p>
                        </div>
                    </div>
                    <a href="https://github.com/AadityaUniyal/Fitness_Smarty" target="_blank" rel="noopener noreferrer"
                        className="flex items-center space-x-2 px-5 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-[10px] uppercase tracking-widest rounded-xl transition-all">
                        <Github size={14} />
                        <span>View Source</span>
                    </a>
                </div>

                {/* Footer */}
                <p className="text-center text-slate-600 text-[10px] font-black uppercase tracking-widest mt-10">
                    © 2025 Smarty AI • Built with ❤️ by Aaditya Uniyal
                </p>
            </div>
        </div>
    );
};

export default ContactPage;
