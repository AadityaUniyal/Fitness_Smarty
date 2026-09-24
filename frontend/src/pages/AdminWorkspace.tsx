import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, 
  Dumbbell, 
  Settings, 
  Trash2, 
  ShieldAlert, 
  RefreshCw, 
  Database, 
  Activity, 
  CheckCircle2, 
  X,
  UserCheck,
  Cpu,
  Sliders,
  ToggleLeft,
  ToggleRight,
  Save,
  Server
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { AdminControlAPI, SystemConfigData } from '../services/apiService';

interface UserItem {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  age: number | null;
  weight_kg: number | null;
  height_cm: number | null;
  gender: string | null;
  activity_level: string | null;
  primary_goal: string | null;
  femmecare_enabled: boolean | null;
  local_only: boolean | null;
  created_at: string | null;
}

interface SystemStats {
  total_users: number;
  active_users_7d: number;
  total_workouts: number;
  total_meals: number;
  total_points_logs: number;
  avg_workouts_per_user: number;
  gemini_api_status: string;
  gemini_model: string;
  environment: string;
}

const AdminWorkspace: React.FC = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'users' | 'ai_config' | 'flags' | 'telemetry'>('users');
  const [users, setUsers] = useState<UserItem[]>([]);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [config, setConfig] = useState<SystemConfigData | null>(null);
  const [telemetry, setTelemetry] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [savingConfig, setSavingConfig] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [editUser, setEditUser] = useState<UserItem | null>(null);

  const getHeaders = () => {
    const token = localStorage.getItem('smarty_access_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  };

  const fetchAdminData = async () => {
    setLoading(true);
    setError('');
    const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
    try {
      const [statsRes, usersRes] = await Promise.all([
        fetch(`${API_BASE}/api/admin/stats`, { headers: getHeaders() }),
        fetch(`${API_BASE}/api/admin/users`, { headers: getHeaders() })
      ]);

      if (!statsRes.ok || !usersRes.ok) {
        throw new Error('Access denied. Admin privileges required.');
      }

      const statsData = await statsRes.json();
      const usersData = await usersRes.json();

      setStats(statsData);
      setUsers(usersData);

      // Fetch dynamic config & telemetry
      try {
        const configData = await AdminControlAPI.getSystemConfig();
        const telemetryData = await AdminControlAPI.getTelemetry();
        setConfig(configData);
        setTelemetry(telemetryData);
      } catch (err) {
        console.warn('Config API not initialized yet:', err);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch admin workspace details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleToggleAdmin = async (userId: number, currentStatus: boolean) => {
    setError('');
    setMessage('');
    const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({ is_admin: !currentStatus })
      });
      if (!res.ok) throw new Error('Failed to update user privileges');
      setMessage(`User ${userId} admin status updated.`);
      fetchAdminData();
    } catch (err: any) {
      setError(err?.message || 'Update failed');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm("Are you sure you want to permanently delete this user and all their logs? This complies with GDPR Right to be Forgotten.")) {
      return;
    }
    setError('');
    setMessage('');
    const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: getHeaders()
      });
      if (!res.ok) throw new Error('Failed to purge user');
      setMessage(`User ${userId} deleted successfully.`);
      fetchAdminData();
    } catch (err: any) {
      setError(err?.message || 'Deletion failed');
    }
  };

  const handleResetDB = async () => {
    if (!window.confirm("WARNING: This will drop all tables and reload the default seeds! Your admin account session will be re-created. Proceed?")) {
      return;
    }
    setBusy(true);
    setError('');
    setMessage('');
    const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
    try {
      const res = await fetch(`${API_BASE}/api/admin/system/reset-db`, {
        method: 'POST',
        headers: getHeaders()
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: 'Database reset failed' }));
        throw new Error(data.detail || 'Database reset failed');
      }
      const data = await res.json();
      setMessage(data.message);
      fetchAdminData();
    } catch (err: any) {
      setError(err?.message || 'Database reset failed');
    } finally {
      setBusy(false);
    }
  };

  const handleSaveConfig = async () => {
    if (!config) return;
    setSavingConfig(true);
    setError('');
    setMessage('');
    try {
      const res = await AdminControlAPI.updateSystemConfig(config);
      if (res.success) {
        setMessage('Backend system configuration updated live!');
        setConfig(res.config);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to update system config');
    } finally {
      setSavingConfig(false);
    }
  };

  const handleToggleFlag = (flagKey: string) => {
    if (!config) return;
    setConfig({
      ...config,
      feature_flags: {
        ...config.feature_flags,
        [flagKey]: !config.feature_flags[flagKey]
      }
    });
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editUser) return;
    setError('');
    setMessage('');
    const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
    try {
      const res = await fetch(`${API_BASE}/api/admin/users/${editUser.id}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({
          age: editUser.age,
          weight_kg: editUser.weight_kg,
          height_cm: editUser.height_cm,
          primary_goal: editUser.primary_goal,
          activity_level: editUser.activity_level
        })
      });
      if (!res.ok) throw new Error('Failed to update user profile');
      setMessage(`User ${editUser.id} profile updated.`);
      setEditUser(null);
      fetchAdminData();
    } catch (err: any) {
      setError(err?.message || 'Profile update failed');
    }
  };

  const handleSignout = () => {
    logout();
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <RefreshCw className="h-10 w-10 text-emerald-400 animate-spin" />
          <span className="text-xs font-black uppercase tracking-widest text-slate-500">Unlocking Command Center...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 sm:p-10">
      {/* Admin Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 pb-5 border-b border-white/5">
        <div>
          <h1 className="text-3xl font-black italic uppercase tracking-tighter text-white flex items-center gap-3">
            Command Center <span className="bg-emerald-500 text-slate-950 px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-normal">Admin</span>
          </h1>
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mt-1">Smarty AI Control Center & Infrastructure</p>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={fetchAdminData}
            className="p-3 rounded-xl border border-white/5 hover:bg-slate-900 transition text-slate-400 hover:text-white"
            title="Refresh Data"
          >
            <RefreshCw size={16} />
          </button>
          <button 
            onClick={handleSignout}
            className="px-5 py-2.5 rounded-xl bg-slate-900 border border-white/10 hover:bg-slate-800 text-xs font-black uppercase tracking-widest text-slate-400 hover:text-white transition"
          >
            Sign Out
          </button>
        </div>
      </header>

      {error && (
        <div className="mb-6 bg-rose-500/10 border border-rose-500/20 p-4 rounded-2xl flex items-center gap-3 text-rose-400 text-xs font-bold">
          <ShieldAlert size={16} />
          <span>{error}</span>
        </div>
      )}

      {message && (
        <div className="mb-6 bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-2xl flex items-center gap-3 text-emerald-400 text-xs font-bold">
          <CheckCircle2 size={16} />
          <span>{message}</span>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex flex-wrap gap-3 mb-8 border-b border-white/5 pb-4">
        <button
          onClick={() => setActiveTab('users')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition ${
            activeTab === 'users'
              ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20'
              : 'bg-slate-900 border border-white/5 text-slate-400 hover:text-white'
          }`}
        >
          <Users size={14} /> Registered Users ({users.length})
        </button>

        <button
          onClick={() => setActiveTab('ai_config')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition ${
            activeTab === 'ai_config'
              ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20'
              : 'bg-slate-900 border border-white/5 text-slate-400 hover:text-white'
          }`}
        >
          <Cpu size={14} /> AI Engine & Prompts
        </button>

        <button
          onClick={() => setActiveTab('flags')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition ${
            activeTab === 'flags'
              ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20'
              : 'bg-slate-900 border border-white/5 text-slate-400 hover:text-white'
          }`}
        >
          <Sliders size={14} /> Feature Flags Matrix
        </button>

        <button
          onClick={() => setActiveTab('telemetry')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition ${
            activeTab === 'telemetry'
              ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20'
              : 'bg-slate-900 border border-white/5 text-slate-400 hover:text-white'
          }`}
        >
          <Server size={14} /> Health & Telemetry
        </button>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <div className="bg-slate-900/60 border border-white/5 p-6 rounded-3xl backdrop-blur-xl">
          <div className="flex justify-between items-center text-slate-500 mb-4">
            <span className="text-[10px] font-black uppercase tracking-widest">Total Users</span>
            <Users size={16} className="text-emerald-400" />
          </div>
          <p className="text-4xl font-black italic tracking-tighter text-white">{stats?.total_users}</p>
          <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider block mt-2">
            Active 7d: {stats?.active_users_7d}
          </span>
        </div>

        <div className="bg-slate-900/60 border border-white/5 p-6 rounded-3xl backdrop-blur-xl">
          <div className="flex justify-between items-center text-slate-500 mb-4">
            <span className="text-[10px] font-black uppercase tracking-widest">Workouts Tracked</span>
            <Dumbbell size={16} className="text-cyan-400" />
          </div>
          <p className="text-4xl font-black italic tracking-tighter text-white">{stats?.total_workouts}</p>
          <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider block mt-2">
            Avg / User: {stats?.avg_workouts_per_user}
          </span>
        </div>

        <div className="bg-slate-900/60 border border-white/5 p-6 rounded-3xl backdrop-blur-xl">
          <div className="flex justify-between items-center text-slate-500 mb-4">
            <span className="text-[10px] font-black uppercase tracking-widest">Meal Scans</span>
            <Activity size={16} className="text-pink-400" />
          </div>
          <p className="text-4xl font-black italic tracking-tighter text-white">{stats?.total_meals}</p>
          <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider block mt-2">
            Vision Pipeline Active
          </span>
        </div>

        <div className="bg-slate-900/60 border border-white/5 p-6 rounded-3xl backdrop-blur-xl">
          <div className="flex justify-between items-center text-slate-500 mb-4">
            <span className="text-[10px] font-black uppercase tracking-widest">Active AI Model</span>
            <Cpu size={16} className="text-yellow-400" />
          </div>
          <p className="text-lg font-black tracking-tight text-white uppercase truncate">
            {config?.ai_provider || stats?.gemini_model || 'Gemini 2.0'}
          </p>
          <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider block mt-2 truncate">
            Temp: {config?.ai_temperature ?? 0.6}
          </span>
        </div>
      </div>

      {/* TAB 1: USERS & DATABASE MANAGEMENT */}
      {activeTab === 'users' && (
        <div className="grid lg:grid-cols-[1fr_350px] gap-8">
          <div className="bg-slate-900/40 border border-white/5 rounded-3xl p-6 sm:p-8 backdrop-blur-xl">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-black uppercase tracking-wider text-white">Registered Users</h3>
              <span className="text-[9px] bg-slate-800 text-slate-400 px-3 py-1 rounded-full font-bold uppercase tracking-wider">
                {users.length} Database entries
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-400 border-collapse">
                <thead>
                  <tr className="border-b border-white/5 text-[9px] font-black uppercase tracking-widest text-slate-500">
                    <th className="pb-4">Username / Email</th>
                    <th className="pb-4">Role</th>
                    <th className="pb-4">Biometrics</th>
                    <th className="pb-4">Primary Goal</th>
                    <th className="pb-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {users.map(u => (
                    <tr key={u.id} className="hover:bg-white/1 transition-colors">
                      <td className="py-4 pr-3">
                        <div className="font-bold text-white">{u.username}</div>
                        <div className="text-[10px] text-slate-500">{u.email}</div>
                      </td>
                      <td className="py-4">
                        {u.is_admin ? (
                          <span className="inline-flex items-center gap-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded text-[9px] font-black uppercase">
                            <UserCheck size={8} /> Admin
                          </span>
                        ) : (
                          <span className="bg-slate-800 border border-white/5 text-slate-500 px-2 py-0.5 rounded text-[9px] font-bold uppercase">
                            User
                          </span>
                        )}
                      </td>
                      <td className="py-4">
                        {u.age ? (
                          <div className="text-[10px]">
                            {u.gender || 'Unknown'}, {u.age} yo, {u.weight_kg}kg, {u.height_cm}cm
                          </div>
                        ) : (
                          <span className="text-slate-600 italic">No biometrics</span>
                        )}
                      </td>
                      <td className="py-4">
                        <span className="uppercase text-[9px] font-bold text-slate-300">
                          {u.primary_goal?.replace('_', ' ') || 'Not set'}
                        </span>
                      </td>
                      <td className="py-4 text-right space-x-2">
                        <button 
                          onClick={() => handleToggleAdmin(u.id, u.is_admin)}
                          className="p-2 rounded-xl bg-slate-900 border border-white/5 hover:bg-slate-800 text-slate-300 transition"
                          title="Toggle Admin Privilege"
                        >
                          {u.is_admin ? 'Make User' : 'Make Admin'}
                        </button>
                        <button 
                          onClick={() => setEditUser(u)}
                          className="p-2 rounded-xl bg-slate-900 border border-white/5 hover:bg-slate-800 text-slate-300 transition"
                          title="Edit User Details"
                        >
                          Edit
                        </button>
                        <button 
                          onClick={() => handleDeleteUser(u.id)}
                          className="p-2 rounded-xl bg-slate-900 border border-white/5 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition"
                          title="Purge User Data"
                        >
                          <Trash2 size={12} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-slate-900/40 border border-white/5 rounded-3xl p-6 backdrop-blur-xl">
              <h3 className="text-xs font-black uppercase tracking-widest text-white mb-4 flex items-center gap-2">
                <Database size={14} className="text-emerald-400" /> Database Utilities
              </h3>
              <p className="text-[10px] text-slate-500 leading-relaxed mb-6">
                Drop tables, re-run full schemas, and re-seed all food macros, custom workout templates, and gamification badge matrices.
              </p>

              <button
                onClick={handleResetDB}
                disabled={busy}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-rose-500 hover:bg-rose-400 text-slate-950 py-3 text-xs font-black uppercase tracking-widest shadow-lg transition disabled:bg-slate-800 disabled:text-slate-500"
              >
                <RefreshCw size={14} className={busy ? 'animate-spin' : ''} />
                {busy ? 'Reseeding...' : 'Reset & Seed DB'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: AI ENGINE & PROMPT STUDIO */}
      {activeTab === 'ai_config' && config && (
        <div className="max-w-4xl bg-slate-900/40 border border-white/5 rounded-3xl p-6 sm:p-8 backdrop-blur-xl space-y-6">
          <div className="flex justify-between items-center border-b border-white/5 pb-4">
            <div>
              <h3 className="text-lg font-black uppercase tracking-wider text-white flex items-center gap-2">
                <Cpu size={18} className="text-yellow-400" /> Dynamic AI Provider & Prompt Studio
              </h3>
              <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">Configure live LLM routing and system prompts without server restarts</p>
            </div>
            <button
              onClick={handleSaveConfig}
              disabled={savingConfig}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-black uppercase tracking-widest transition shadow-lg"
            >
              <Save size={14} />
              {savingConfig ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-2">
                Active AI Provider Engine
              </label>
              <select
                value={config.ai_provider}
                onChange={e => setConfig({ ...config, ai_provider: e.target.value })}
                className="w-full bg-slate-950 border border-white/10 rounded-xl py-3 px-4 text-xs text-white outline-none focus:border-emerald-500"
              >
                <option value="gemini-3.6-flash">Google Gemini 2.0 Flash (Recommended Free)</option>
                <option value="groq">Groq Cloud (Llama 3.3 70B / DeepSeek R1)</option>
                <option value="openrouter">OpenRouter (Universal Free Layer)</option>
                <option value="ollama">Ollama (Offline Self-Hosted Local LLM)</option>
                <option value="mock">Deterministic Fallback Engine (No API Key)</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-2">
                LLM Temperature ({config.ai_temperature})
              </label>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={config.ai_temperature}
                onChange={e => setConfig({ ...config, ai_temperature: parseFloat(e.target.value) })}
                className="w-full accent-emerald-500 bg-slate-950 rounded-xl cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-slate-500 font-bold mt-1">
                <span>0.0 (Deterministic / Scientific)</span>
                <span>1.0 (Creative)</span>
              </div>
            </div>
          </div>

          <div>
            <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-2">
              System Instruction Prompt
            </label>
            <textarea
              rows={5}
              value={config.ai_system_prompt}
              onChange={e => setConfig({ ...config, ai_system_prompt: e.target.value })}
              className="w-full bg-slate-950 border border-white/10 rounded-xl p-4 text-xs font-mono text-slate-200 outline-none focus:border-emerald-500 leading-relaxed"
            />
          </div>
        </div>
      )}

      {/* TAB 3: FEATURE FLAGS MATRIX */}
      {activeTab === 'flags' && config && (
        <div className="max-w-3xl bg-slate-900/40 border border-white/5 rounded-3xl p-6 sm:p-8 backdrop-blur-xl space-y-6">
          <div className="flex justify-between items-center border-b border-white/5 pb-4">
            <div>
              <h3 className="text-lg font-black uppercase tracking-wider text-white flex items-center gap-2">
                <Sliders size={18} className="text-cyan-400" /> Web App Feature Flags Matrix
              </h3>
              <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-1">Toggle features on or off in real-time across the platform</p>
            </div>
            <button
              onClick={handleSaveConfig}
              disabled={savingConfig}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-black uppercase tracking-widest transition shadow-lg"
            >
              <Save size={14} />
              {savingConfig ? 'Saving...' : 'Save Flags'}
            </button>
          </div>

          <div className="space-y-4">
            {Object.entries(config.feature_flags || {}).map(([flagKey, isEnabled]) => (
              <div key={flagKey} className="flex justify-between items-center bg-slate-950/60 border border-white/5 p-4 rounded-2xl">
                <div>
                  <span className="text-xs font-black uppercase tracking-wider text-white block">
                    {flagKey.replace('_', ' ')}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {isEnabled ? 'Feature actively routed to users' : 'Feature disabled'}
                  </span>
                </div>

                <button
                  onClick={() => handleToggleFlag(flagKey)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition ${
                    isEnabled
                      ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                      : 'bg-slate-800 text-slate-500'
                  }`}
                >
                  {isEnabled ? <ToggleRight size={20} className="text-emerald-400" /> : <ToggleLeft size={20} />}
                  {isEnabled ? 'ENABLED' : 'DISABLED'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: SYSTEM HEALTH & TELEMETRY */}
      {activeTab === 'telemetry' && telemetry && (
        <div className="max-w-4xl space-y-6">
          <div className="bg-slate-900/40 border border-white/5 rounded-3xl p-6 sm:p-8 backdrop-blur-xl">
            <h3 className="text-lg font-black uppercase tracking-wider text-white flex items-center gap-2 mb-6">
              <Server size={18} className="text-pink-400" /> Infrastructure Telemetry & Status
            </h3>

            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-slate-950 p-5 rounded-2xl border border-white/5">
                <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1">Environment</span>
                <span className="text-lg font-black text-white uppercase">{telemetry.environment}</span>
              </div>

              <div className="bg-slate-950 p-5 rounded-2xl border border-white/5">
                <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1">Database Engine</span>
                <span className="text-lg font-black text-emerald-400 uppercase">{telemetry.database_type}</span>
              </div>

              <div className="bg-slate-950 p-5 rounded-2xl border border-white/5">
                <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1">Redis Status</span>
                <span className={`text-lg font-black uppercase ${telemetry.system_metrics?.redis_status === 'CONNECTED' ? 'text-emerald-400' : 'text-yellow-400'}`}>
                  {telemetry.system_metrics?.redis_status}
                </span>
              </div>

              <div className="bg-slate-950 p-5 rounded-2xl border border-white/5">
                <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1">Process Memory</span>
                <span className="text-lg font-black text-white">{telemetry.system_metrics?.memory_usage_mb} MB</span>
              </div>

              <div className="bg-slate-950 p-5 rounded-2xl border border-white/5">
                <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1">CPU Utilization</span>
                <span className="text-lg font-black text-white">{telemetry.system_metrics?.cpu_percent}%</span>
              </div>

              <div className="bg-slate-950 p-5 rounded-2xl border border-white/5">
                <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 block mb-1">24h Active Users</span>
                <span className="text-lg font-black text-cyan-400">{telemetry.table_counts?.active_users_24h}</span>
              </div>
            </div>

            <h4 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">AI API Key Configuration Status</h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {Object.entries(telemetry.ai_keys_configured || {}).map(([provider, isSet]) => (
                <div key={provider} className="bg-slate-950 p-4 rounded-xl border border-white/5 flex justify-between items-center">
                  <span className="text-xs font-bold uppercase text-slate-300">{provider}</span>
                  <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${isSet ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                    {isSet ? 'CONFIGURED' : 'UNSET'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {editUser && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur flex items-center justify-center p-6">
          <div className="bg-slate-900 border border-white/10 rounded-3xl p-8 max-w-md w-full relative">
            <button 
              onClick={() => setEditUser(null)}
              className="absolute right-6 top-6 text-slate-500 hover:text-white"
            >
              <X size={18} />
            </button>

            <h3 className="text-xl font-black italic uppercase tracking-tight text-white mb-6">
              Edit User Profile
            </h3>

            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div>
                <label className="text-[9px] font-black uppercase tracking-wider text-slate-500 block mb-1">Age</label>
                <input 
                  type="number"
                  value={editUser.age || ''}
                  onChange={e => setEditUser({...editUser, age: parseInt(e.target.value) || null})}
                  className="w-full bg-slate-950 border border-white/10 rounded-xl py-3 px-4 text-xs text-white outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[9px] font-black uppercase tracking-wider text-slate-500 block mb-1">Weight (kg)</label>
                  <input 
                    type="number"
                    step="0.1"
                    value={editUser.weight_kg || ''}
                    onChange={e => setEditUser({...editUser, weight_kg: parseFloat(e.target.value) || null})}
                    className="w-full bg-slate-950 border border-white/10 rounded-xl py-3 px-4 text-xs text-white outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-[9px] font-black uppercase tracking-wider text-slate-500 block mb-1">Height (cm)</label>
                  <input 
                    type="number"
                    value={editUser.height_cm || ''}
                    onChange={e => setEditUser({...editUser, height_cm: parseInt(e.target.value) || null})}
                    className="w-full bg-slate-950 border border-white/10 rounded-xl py-3 px-4 text-xs text-white outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-[9px] font-black uppercase tracking-wider text-slate-500 block mb-1">Goal</label>
                <select
                  value={editUser.primary_goal || ''}
                  onChange={e => setEditUser({...editUser, primary_goal: e.target.value})}
                  className="w-full bg-slate-950 border border-white/10 rounded-xl py-3 px-4 text-xs text-white outline-none focus:border-emerald-500"
                >
                  <option value="weight_loss">Weight Loss</option>
                  <option value="muscle_gain">Muscle Gain</option>
                  <option value="maintenance">Maintenance</option>
                </select>
              </div>

              <div>
                <label className="text-[9px] font-black uppercase tracking-wider text-slate-500 block mb-1">Activity Level</label>
                <select
                  value={editUser.activity_level || ''}
                  onChange={e => setEditUser({...editUser, activity_level: e.target.value})}
                  className="w-full bg-slate-950 border border-white/10 rounded-xl py-3 px-4 text-xs text-white outline-none focus:border-emerald-500"
                >
                  <option value="sedentary">Sedentary</option>
                  <option value="moderate">Moderate</option>
                  <option value="active">Active</option>
                </select>
              </div>

              <button
                type="submit"
                className="w-full flex items-center justify-center rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 py-3 text-xs font-black uppercase tracking-widest transition shadow-lg mt-6"
              >
                Save Profile
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminWorkspace;
