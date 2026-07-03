import React, { useState, useEffect } from 'react';
import { Download, FileText, CheckCircle2, Loader2, FileSpreadsheet, Printer, AlertCircle, BarChart3 } from 'lucide-react';
import { exportWorkoutsCSV, exportMealsCSV, exportSleepCSV, exportBodyMeasurementsCSV, exportMoodCSV, exportMealPlanCSV, exportAllCSV, openPrintableReport, getExportSummary, ExportSummary } from '../services/exportService';

const EXPORT_ITEMS = [
  { id: 'workouts', label: 'Workouts', icon: '💪', desc: 'Duration, calories, exercises', action: exportWorkoutsCSV },
  { id: 'meals', label: 'Meals', icon: '🍽️', desc: 'Calories, macros, foods', action: exportMealsCSV },
  { id: 'sleep', label: 'Sleep', icon: '😴', desc: 'Hours, quality, notes', action: exportSleepCSV },
  { id: 'body', label: 'Body Measurements', icon: '📏', desc: 'Weight, body fat, circumferences', action: exportBodyMeasurementsCSV },
  { id: 'mood', label: 'Mood & Energy', icon: '🧠', desc: 'Mood, energy, notes', action: exportMoodCSV },
  { id: 'mealPlan', label: 'Meal Plan', icon: '📋', desc: 'Weekly meal schedule', action: exportMealPlanCSV },
];

const ExportPage: React.FC = () => {
  const [summary, setSummary] = useState<ExportSummary>(getExportSummary());
  const [exporting, setExporting] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [lastExported, setLastExported] = useState<string | null>(null);

  useEffect(() => {
    const interval = setInterval(() => { setSummary(getExportSummary()); }, 3000);
    return () => clearInterval(interval);
  }, []);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  const handleExport = async (id: string, action: () => number) => {
    setExporting(id);
    await new Promise(r => setTimeout(r, 300));
    try {
      const count = action();
      setLastExported(id);
      showToast(`Exported ${count} ${id} record${count !== 1 ? 's' : ''}`);
    } catch {
      showToast('Export failed — try again');
    }
    setExporting(null);
    setSummary(getExportSummary());
  };

  const handleExportAll = async () => {
    setExporting('all');
    await new Promise(r => setTimeout(r, 500));
    try {
      const result = exportAllCSV();
      const total = Object.values(result).reduce((s, c) => s + c, 0);
      showToast(`Exported ${total} total records across all categories`);
    } catch {
      showToast('Export failed — try again');
    }
    setExporting(null);
  };

  const handlePDF = () => {
    try {
      openPrintableReport();
      showToast('Report opened in new tab — use Print/Save as PDF');
    } catch {
      showToast('Failed to generate report');
    }
  };

  const totalRecords = Object.values(summary).reduce((s, c) => s + c, 0);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {toast && (
        <div className="fixed top-6 right-6 z-50 px-5 py-3 bg-emerald-500/20 border border-emerald-500/30 rounded-2xl text-emerald-400 text-[10px] font-black uppercase tracking-widest backdrop-blur-xl animate-fade-in">
          {toast}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-indigo-500/10 border border-indigo-500/20 rounded-3xl flex items-center justify-center text-indigo-400">
            <Download size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Export Data</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
              {totalRecords} records available
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={handlePDF}
            className="flex items-center space-x-2 px-5 py-3 bg-rose-500 hover:bg-rose-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
            <FileText size={14} />
            <span>PDF Report</span>
          </button>
          <button onClick={handleExportAll} disabled={exporting === 'all' || totalRecords === 0}
            className="flex items-center space-x-2 px-5 py-3 bg-indigo-500 hover:bg-indigo-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition disabled:opacity-50">
            {exporting === 'all' ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            <span>Export All</span>
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        {[
          { id: 'workouts', label: 'Workouts', value: summary.workouts, color: 'text-emerald-400' },
          { id: 'meals', label: 'Meals', value: summary.meals, color: 'text-amber-400' },
          { id: 'sleep', label: 'Sleep', value: summary.sleep, color: 'text-indigo-400' },
          { id: 'body', label: 'Body', value: summary.body, color: 'text-cyan-400' },
          { id: 'mood', label: 'Mood', value: summary.mood, color: 'text-purple-400' },
          { id: 'mealPlan', label: 'Planned', value: summary.mealPlan, color: 'text-rose-400' },
        ].map(s => (
          <div key={s.id} className="glass-panel p-4 rounded-2xl border border-white/5">
            <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest">{s.label}</p>
            <p className={`text-2xl font-black ${s.color} mt-0.5`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Export grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {EXPORT_ITEMS.map(item => {
          const count = summary[item.id as keyof ExportSummary];
          const isExporting = exporting === item.id;
          const isDone = lastExported === item.id;
          return (
            <button key={item.id} onClick={() => handleExport(item.id, item.action)}
              disabled={isExporting || count === 0}
              className={`glass-panel rounded-[2rem] border p-6 text-left transition-all group
                ${isDone ? 'border-emerald-500/30 bg-emerald-500/[0.03]' : 'border-white/5 hover:border-white/10'}
                disabled:opacity-50 disabled:cursor-not-allowed`}>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-4">
                  <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-2xl ${
                    isDone ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-white/[0.03] border border-white/10'
                  }`}>
                    {isDone ? <CheckCircle2 size={24} className="text-emerald-400" /> : item.icon}
                  </div>
                  <div>
                    <p className="text-sm font-black text-white flex items-center space-x-2">
                      <span>{item.label}</span>
                      <span className="text-[9px] text-slate-500 font-black">{count} records</span>
                    </p>
                    <p className="text-[9px] text-slate-600 font-black uppercase tracking-widest mt-0.5">{item.desc}</p>
                  </div>
                </div>
                <div className={`p-2.5 rounded-xl transition-all ${
                  isExporting ? 'bg-indigo-500/10 text-indigo-400' : 
                  isDone ? 'bg-emerald-500/10 text-emerald-400' :
                  'bg-white/[0.03] text-slate-600 group-hover:text-slate-400'
                }`}>
                  {isExporting ? <Loader2 size={16} className="animate-spin" /> : <FileSpreadsheet size={16} />}
                </div>
              </div>
              {count === 0 && (
                <p className="text-[8px] text-slate-600 font-black uppercase tracking-widest mt-3 flex items-center space-x-1">
                  <AlertCircle size={10} />
                  <span>No data to export</span>
                </p>
              )}
            </button>
          );
        })}
      </div>

      {/* PDF Report card */}
      <div className="glass-panel rounded-[2rem] border border-white/5 overflow-hidden">
        <div className="p-6 border-b border-white/5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Fitness Summary Report</p>
        </div>
        <div className="p-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
              <FileText size={22} />
            </div>
            <div>
              <p className="text-sm font-black text-white">Full Printable Report</p>
              <p className="text-[9px] text-slate-600 font-black uppercase tracking-widest mt-0.5">
                Workout stats · Nutrition summary · Sleep trends · Body measurements
              </p>
            </div>
          </div>
          <button onClick={handlePDF}
            className="flex items-center space-x-2 px-6 py-3 bg-rose-500 hover:bg-rose-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
            <Printer size={14} />
            <span>Open Report</span>
          </button>
        </div>
      </div>

      {/* Info */}
      <div className="text-center py-6">
        <p className="text-[8px] text-slate-700 font-black uppercase tracking-widest">
          All data is exported from your local storage. No data is sent to any server.
        </p>
      </div>
    </div>
  );
};

export default ExportPage;
