
import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  Dumbbell, 
  Utensils, 
  Mic, 
  Settings,
  Bell,
  Search,
  MessageCircle,
  Menu,
  X,
  LogOut,
  Zap,
  Fingerprint
} from 'lucide-react';
import { SignedIn, SignedOut, UserButton, useClerk } from '@clerk/clerk-react';
import Dashboard from './Dashboard';
import WorkoutAssistant from './WorkoutAssistant';
import NutritionHub from './NutritionHub';
import LiveCoach from './LiveCoach';
import SmartyChat from './SmartyChat';
import BioLink from './BioLink';
import Auth from './Auth';
import { NavigationTab } from './types';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>(NavigationTab.DASHBOARD);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { signOut } = useClerk();

  const renderContent = () => {
    switch (activeTab) {
      case NavigationTab.DASHBOARD: return <Dashboard />;
      case NavigationTab.BIO_PROFILE: return <BioLink />;
      case NavigationTab.WORKOUTS: return <WorkoutAssistant />;
      case NavigationTab.NUTRITION: return <NutritionHub />;
      case NavigationTab.LIVE_COACH: return <LiveCoach />;
      case NavigationTab.CHAT: return <SmartyChat />;
      default: return <Dashboard />;
    }
  };

  const navItems = [
    { id: NavigationTab.DASHBOARD, label: 'Mission Control', icon: LayoutDashboard },
    { id: NavigationTab.BIO_PROFILE, label: 'Bio Calibration', icon: Fingerprint },
    { id: NavigationTab.WORKOUTS, label: 'Kinetic Ops', icon: Dumbbell },
    { id: NavigationTab.NUTRITION, label: 'Fuel Matrix', icon: Utensils },
    { id: NavigationTab.LIVE_COACH, label: 'Neural Coach', icon: Mic },
    { id: NavigationTab.CHAT, label: 'Core Oracle', icon: MessageCircle },
  ];

  return (
    <>
      <SignedOut>
        <Auth />
      </SignedOut>
      <SignedIn>
        <div className="flex h-screen bg-[#020617] overflow-hidden text-slate-200 selection:bg-emerald-500/30">
          {/* HUD-Style Sidebar */}
          <aside className="w-80 border-r border-white/5 flex flex-col hidden lg:flex bg-slate-950/20 backdrop-blur-2xl relative">
            <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-transparent via-emerald-500/20 to-transparent"></div>
            
            <div className="p-10">
              <div className="flex items-center space-x-4 group cursor-pointer" onClick={() => setActiveTab(NavigationTab.DASHBOARD)}>
                <div className="w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center text-slate-950 shadow-[0_0_20px_rgba(16,185,129,0.4)] transition-all group-hover:scale-110 rotate-3">
                  <Zap size={26} className="fill-slate-950" />
                </div>
                <div>
                  <h1 className="text-2xl font-black italic tracking-tighter text-white">SMARTY <span className="text-emerald-400">AI</span></h1>
                  <p className="text-[8px] font-black uppercase tracking-[0.4em] text-slate-500 -mt-1">Operational v4.0</p>
                </div>
              </div>
            </div>
            
            <nav className="flex-1 px-6 space-y-3 mt-4">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center space-x-4 px-6 py-4 rounded-2xl transition-all relative group ${
                    activeTab === item.id 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-inner' 
                      : 'text-slate-500 hover:text-slate-200 hover:bg-white/5 border border-transparent'
                  }`}
                >
                  <item.icon size={22} className={activeTab === item.id ? 'text-emerald-400' : 'group-hover:text-emerald-400 transition-colors'} />
                  <span className="font-black uppercase tracking-[0.15em] text-[10px]">{item.label}</span>
                  {activeTab === item.id && (
                    <div className="absolute right-4 w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_10px_#10b981]"></div>
                  )}
                </button>
              ))}
            </nav>

            <div className="p-8 border-t border-white/5 space-y-3">
              <button 
                onClick={() => signOut()}
                className="w-full flex items-center space-x-4 px-6 py-4 text-rose-500/60 hover:text-rose-400 hover:bg-rose-500/5 rounded-2xl transition-colors group"
              >
                <LogOut size={20} />
                <span className="font-black uppercase tracking-widest text-[10px]">Deactivate Link</span>
              </button>
            </div>
          </aside>

          {/* Main Command Center */}
          <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
            <header className="h-24 border-b border-white/5 flex items-center justify-between px-10 bg-[#020617]/40 backdrop-blur-3xl sticky top-0 z-40">
              <div className="flex items-center space-x-8">
                <button className="lg:hidden p-3 text-slate-400 bg-white/5 rounded-xl" onClick={() => setIsMobileMenuOpen(true)}>
                  <Menu size={24} />
                </button>
                <div className="relative w-full max-w-lg hidden md:block">
                  <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-600" size={18} />
                  <input 
                    type="text" 
                    placeholder="EXECUTE NEURAL COMMAND..." 
                    className="w-full bg-slate-950 border border-white/10 rounded-2xl py-4 pl-14 pr-6 text-[10px] font-black tracking-widest text-emerald-400 focus:outline-none transition-all focus:ring-4 focus:ring-emerald-500/5 uppercase"
                  />
                </div>
              </div>
              
              <div className="flex items-center space-x-8">
                <div className="hidden lg:flex flex-col items-end mr-2">
                   <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Uplink Status</p>
                   <p className="text-[10px] font-black text-emerald-400 glow-text uppercase animate-pulse">Encrypted & Secure</p>
                </div>
                
                <div className="flex items-center space-x-5 pl-8 border-l border-white/5">
                  <div className="relative group cursor-pointer">
                     <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-2xl blur opacity-25 group-hover:opacity-100 transition duration-1000"></div>
                     <UserButton 
                       appearance={{
                         elements: {
                           userButtonAvatarBox: "w-14 h-14 rounded-2xl border border-white/20 shadow-2xl bg-slate-900",
                           userButtonTrigger: "focus:shadow-none"
                         }
                       }}
                     />
                  </div>
                </div>
              </div>
            </header>

            <div className="flex-1 overflow-y-auto p-8 md:p-12 relative">
              <div className="absolute inset-0 opacity-[0.02] pointer-events-none" style={{ backgroundImage: 'linear-gradient(rgba(16, 185, 129, 0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(16, 185, 129, 0.2) 1px, transparent 1px)', backgroundSize: '100px 100px' }}></div>
              <div className="relative z-10">{renderContent()}</div>
            </div>

            {isMobileMenuOpen && (
              <div className="fixed inset-0 z-50 lg:hidden">
                 <div className="absolute inset-0 bg-slate-950/90 backdrop-blur-md" onClick={() => setIsMobileMenuOpen(false)}></div>
                 <aside className="absolute top-0 left-0 bottom-0 w-72 bg-[#020617] border-r border-white/10 p-8 flex flex-col animate-in slide-in-from-left duration-500">
                    <div className="flex items-center justify-between mb-12">
                      <span className="text-2xl font-black italic text-white uppercase tracking-tighter">Smarty <span className="text-emerald-400">AI</span></span>
                      <button onClick={() => setIsMobileMenuOpen(false)} className="p-2 text-slate-500"><X size={24} /></button>
                    </div>
                    <nav className="flex-1 space-y-4">
                      {navItems.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => { setActiveTab(item.id); setIsMobileMenuOpen(false); }}
                          className={`w-full flex items-center space-x-4 p-5 rounded-2xl ${
                            activeTab === item.id ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-slate-500'
                          }`}
                        >
                          <item.icon size={22} />
                          <span className="font-black text-[10px] uppercase tracking-widest">{item.label}</span>
                        </button>
                      ))}
                    </nav>
                 </aside>
              </div>
            )}
          </main>
        </div>
      </SignedIn>
    </>
  );
};

export default App;
