import React, { useState, useEffect, useRef } from 'react';
import { Camera, Trash2, Check, Image, ChevronLeft, ChevronRight, Clock } from 'lucide-react';

const STORAGE_KEY = 'smarty_progress_photos';

interface PhotoEntry {
  id: string;
  date: string;
  dataUrl: string;
  note: string;
  timestamp: string;
}

const ProgressPhotos: React.FC = () => {
  const [photos, setPhotos] = useState<PhotoEntry[]>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { return []; }
  });
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [note, setNote] = useState('');
  const [compareMode, setCompareMode] = useState(false);
  const [compareIdx, setCompareIdx] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(photos));
  }, [photos]);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const entry: PhotoEntry = {
        id: crypto.randomUUID?.() || Date.now().toString(),
        date: new Date().toISOString().split('T')[0],
        dataUrl: ev.target?.result as string,
        note,
        timestamp: new Date().toISOString(),
      };
      setPhotos(prev => [entry, ...prev]);
      setNote('');
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const handleDelete = (id: string) => {
    if (deleteConfirm === id) {
      setPhotos(prev => prev.filter(p => p.id !== id));
      setDeleteConfirm(null);
      if (compareIdx >= photos.length - 1) setCompareIdx(Math.max(0, compareIdx - 1));
    } else {
      setDeleteConfirm(id);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  const latestTwo = photos.slice(0, 2);
  const weeksSinceFirst = photos.length > 1
    ? Math.round((new Date(photos[0].timestamp).getTime() - new Date( photos[photos.length - 1].timestamp).getTime()) / (7 * 86400000))
    : 0;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="w-16 h-16 bg-rose-500/10 border border-rose-500/20 rounded-3xl flex items-center justify-center text-rose-400">
            <Camera size={32} />
          </div>
          <div>
            <h2 className="text-4xl font-black italic tracking-tighter text-white uppercase">Progress Photos</h2>
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Visual proof of your transformation</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {photos.length >= 2 && (
            <button onClick={() => setCompareMode(!compareMode)}
              className="flex items-center space-x-2 px-5 py-3 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-2xl font-black text-[9px] uppercase tracking-widest hover:bg-amber-500/20 transition">
              <Image size={14} />
              <span>{compareMode ? 'Close Compare' : 'Compare Old vs New'}</span>
            </button>
          )}
          <button onClick={() => fileRef.current?.click()}
            className="flex items-center space-x-2 px-6 py-3 bg-rose-500 hover:bg-rose-400 text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-widest transition">
            <Camera size={16} />
            <span>Take Photo</span>
          </button>
          <input ref={fileRef} type="file" accept="image/*" capture="environment" onChange={handleUpload} className="hidden" />
        </div>
      </div>

      {photos.length === 0 && (
        <div className="glass-panel rounded-[2.5rem] p-16 border border-white/5 text-center">
          <Camera size={48} className="mx-auto text-slate-600 mb-4" />
          <p className="text-lg font-black text-slate-500 uppercase tracking-wider">No progress photos yet</p>
          <p className="text-[10px] font-black text-slate-600 mt-2 uppercase tracking-widest">Snap your first photo to start tracking your transformation</p>
        </div>
      )}

      {compareMode && latestTwo.length === 2 && (
        <div className="glass-panel p-8 rounded-[2.5rem] border border-white/5">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-6">Before & After</p>
          <div className="grid grid-cols-2 gap-6">
            {latestTwo.map((p, i) => (
              <div key={p.id} className="space-y-3">
                <div className="relative aspect-[3/4] rounded-2xl overflow-hidden border border-white/10 bg-slate-950">
                  <img src={p.dataUrl} alt={`Progress ${i === 0 ? 'Latest' : 'Before'}`} className="w-full h-full object-cover" />
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-slate-950/90 to-transparent p-4">
                    <p className="text-[10px] font-black text-white uppercase tracking-widest">
                      {i === 0 ? 'Now' : 'Before'} — {new Date(p.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </p>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">
                    {i === 0 ? `Weight: ${JSON.parse(localStorage.getItem('smarty_body_measurements') || '[{}]').slice(-1)[0]?.weight || '—'} kg` : `Starting photo #${photos.length - 1}`}
                  </span>
                  {p.note && <span className="text-[9px] text-slate-500 italic">{p.note}</span>}
                </div>
              </div>
            ))}
          </div>
          {photos.length > 2 && (
            <p className="text-center text-[9px] text-slate-600 font-black uppercase tracking-widest mt-6">
              {photos.length} photos over {weeksSinceFirst} weeks
            </p>
          )}
        </div>
      )}

      {!compareMode && (
        <>
          {note !== undefined && (
            <div className="space-y-3">
              <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Note (optional)</label>
              <input value={note} onChange={e => setNote(e.target.value)} placeholder="e.g. Feeling leaner, better definition..."
                className="w-full bg-slate-950 border border-white/10 rounded-xl px-5 py-3 text-xs text-white placeholder:text-slate-600" />
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {photos.map(p => (
              <div key={p.id} className="group relative aspect-[3/4] rounded-2xl overflow-hidden border border-white/5 bg-slate-950">
                <img src={p.dataUrl} alt={`Progress ${new Date(p.date).toLocaleDateString()}`} className="w-full h-full object-cover transition-transform group-hover:scale-105" />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="absolute bottom-0 left-0 right-0 p-3 space-y-1">
                    <p className="text-[9px] font-black text-white uppercase tracking-widest">
                      {new Date(p.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </p>
                    {p.note && <p className="text-[8px] text-slate-400 italic">{p.note}</p>}
                  </div>
                </div>
                <button onClick={() => handleDelete(p.id)}
                  className="absolute top-2 right-2 p-2 rounded-xl bg-rose-500/20 text-rose-400 opacity-0 group-hover:opacity-100 hover:bg-rose-500/40 transition-all">
                  {deleteConfirm === p.id ? <Check size={14} /> : <Trash2 size={14} />}
                </button>
                <div className="absolute top-2 left-2 px-2 py-1 rounded-lg bg-slate-950/60 text-[8px] font-black text-slate-400 uppercase tracking-widest backdrop-blur-sm">
                  #{photos.length - photos.indexOf(p)}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default ProgressPhotos;
