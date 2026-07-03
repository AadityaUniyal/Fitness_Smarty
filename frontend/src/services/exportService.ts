function loadJSON(key: string): any[] {
  try { return JSON.parse(localStorage.getItem(key) || '[]'); } catch { return []; }
}

function escapeCSV(val: string | number | null | undefined): string {
  if (val == null) return '""';
  const s = String(val);
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}

function arrayToCSV(headers: string[], rows: string[][]): string {
  return [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
}

function download(filename: string, content: string, mime: string = 'text/csv') {
  const blob = new Blob([content], { type: `${mime};charset=utf-8;` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function exportWorkoutsCSV() {
  const logs = loadJSON('smarty_workout_logs');
  const rows = logs.map((l: any) => [
    escapeCSV(l.template || l.name || 'Workout'),
    escapeCSV(l.date || l.timestamp?.split('T')[0] || ''),
    escapeCSV(l.duration || 0),
    escapeCSV(l.caloriesBurned || 0),
    escapeCSV(l.exercises?.length || 0),
  ]);
  const csv = arrayToCSV(['Workout', 'Date', 'Duration (min)', 'Calories', 'Exercises'], rows);
  download(`smarty_workouts_${new Date().toISOString().split('T')[0]}.csv`, csv);
  return logs.length;
}

export function exportMealsCSV() {
  const logs = loadJSON('smarty_meal_logs');
  const rows = logs.map((l: any) => [
    escapeCSV(l.mealType || l.meal_type || 'Meal'),
    escapeCSV(l.timestamp?.split('T')[0] || l.date || ''),
    escapeCSV(l.totalCalories || 0),
    escapeCSV(l.totalProtein || l.totalProtein_g || 0),
    escapeCSV(l.totalCarbs || l.totalCarbs_g || 0),
    escapeCSV(l.totalFat || l.totalFat_g || 0),
    escapeCSV((l.items || l.detected_foods || []).map((f: any) => f.name || f.food_name).join('; ')),
  ]);
  const csv = arrayToCSV(['Meal Type', 'Date', 'Calories', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Foods'], rows);
  download(`smarty_meals_${new Date().toISOString().split('T')[0]}.csv`, csv);
  return logs.length;
}

export function exportSleepCSV() {
  const logs = loadJSON('smarty_sleep_logs');
  const rows = logs.map((l: any) => [
    escapeCSV(l.date || l.timestamp?.split('T')[0] || ''),
    escapeCSV(l.hours || 0),
    escapeCSV(l.quality || 0),
    escapeCSV(l.notes || ''),
  ]);
  const csv = arrayToCSV(['Date', 'Hours', 'Quality (1-5)', 'Notes'], rows);
  download(`smarty_sleep_${new Date().toISOString().split('T')[0]}.csv`, csv);
  return logs.length;
}

export function exportBodyMeasurementsCSV() {
  const logs = loadJSON('smarty_body_measurements');
  if (logs.length === 0) return 0;
  const allKeys = [...new Set(logs.flatMap((l: any) => Object.keys(l)))].filter(k => k !== 'id' && k !== 'timestamp');
  const headers = ['Date', ...allKeys.filter(k => k !== 'date')];
  const rows = logs.map((l: any) => headers.map(h => escapeCSV(h === 'Date' ? (l.date || l.timestamp?.split('T')[0] || '') : l[h.toLowerCase()] ?? l[h] ?? '')));
  const csv = arrayToCSV(headers, rows);
  download(`smarty_body_${new Date().toISOString().split('T')[0]}.csv`, csv);
  return logs.length;
}

export function exportMoodCSV() {
  const logs = loadJSON('smarty_mood_logs');
  const rows = logs.map((l: any) => [
    escapeCSV(l.timestamp?.split('T')[0] || l.date || ''),
    escapeCSV(l.mood || 0),
    escapeCSV(l.energy || 0),
    escapeCSV(l.notes || ''),
  ]);
  const csv = arrayToCSV(['Date', 'Mood (1-5)', 'Energy (1-5)', 'Notes'], rows);
  download(`smarty_mood_${new Date().toISOString().split('T')[0]}.csv`, csv);
  return logs.length;
}

export function exportMealPlanCSV() {
  const plan = (() => { try { return JSON.parse(localStorage.getItem('smarty_meal_plan') || '{}'); } catch { return {}; } })();
  const rows: string[][] = [];
  const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const SLOTS = ['breakfast', 'lunch', 'dinner', 'snack'];
  DAYS.forEach(day => {
    SLOTS.forEach(slot => {
      const meals = plan[day]?.[slot] || [];
      meals.forEach((m: any) => {
        rows.push([
          escapeCSV(day), escapeCSV(slot), escapeCSV(m.name || ''),
          escapeCSV(m.calories || 0), escapeCSV(m.protein || 0),
          escapeCSV(m.carbs || 0), escapeCSV(m.fats || 0),
          escapeCSV(m.serving || ''),
        ]);
      });
    });
  });
  const csv = arrayToCSV(['Day', 'Meal Slot', 'Food', 'Calories', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Serving'], rows);
  download(`smarty_meal_plan_${new Date().toISOString().split('T')[0]}.csv`, csv);
  return rows.length;
}

export interface ExportSummary {
  workouts: number;
  meals: number;
  sleep: number;
  body: number;
  mood: number;
  mealPlan: number;
}

export function getExportSummary(): ExportSummary {
  return {
    workouts: loadJSON('smarty_workout_logs').length,
    meals: loadJSON('smarty_meal_logs').length,
    sleep: loadJSON('smarty_sleep_logs').length,
    body: loadJSON('smarty_body_measurements').length,
    mood: loadJSON('smarty_mood_logs').length,
    mealPlan: (() => { try { return Object.keys(JSON.parse(localStorage.getItem('smarty_meal_plan') || '{}')).length; } catch { return 0; } })(),
  };
}

export function exportAllCSV(): ExportSummary {
  const summary: ExportSummary = {
    workouts: exportWorkoutsCSV(),
    meals: exportMealsCSV(),
    sleep: exportSleepCSV(),
    body: exportBodyMeasurementsCSV(),
    mood: exportMoodCSV(),
    mealPlan: exportMealPlanCSV(),
  };
  return summary;
}

export function generatePrintableReport(): string {
  const profile = (() => { try { return JSON.parse(localStorage.getItem('smarty_profile') || '{}'); } catch { return {}; } })();
  const workouts = loadJSON('smarty_workout_logs');
  const meals = loadJSON('smarty_meal_logs');
  const sleep = loadJSON('smarty_sleep_logs');
  const body = loadJSON('smarty_body_measurements');
  const mood = loadJSON('smarty_mood_logs');

  const totalCalBurned = workouts.reduce((s: number, l: any) => s + (l.caloriesBurned || 0), 0);
  const totalWorkoutMin = workouts.reduce((s: number, l: any) => s + (l.duration || 0), 0);
  const avgSleep = sleep.length > 0 ? (sleep.reduce((s: number, l: any) => s + (l.hours || 0), 0) / sleep.length).toFixed(1) : 'N/A';
  const totalMealCal = meals.reduce((s: number, l: any) => s + (l.totalCalories || 0), 0);

  return `
<!DOCTYPE html><html><head><meta charset="utf-8"><title>SMARTY Fitness Report</title>
<style>
  @page { margin: 1.5cm; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1e293b; max-width: 800px; margin: 0 auto; padding: 20px; }
  h1 { font-size: 28px; font-weight: 900; letter-spacing: -0.02em; border-bottom: 3px solid #10b981; padding-bottom: 10px; }
  h2 { font-size: 18px; font-weight: 800; margin-top: 30px; color: #10b981; text-transform: uppercase; letter-spacing: 0.1em; }
  .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }
  .stat { background: #f1f5f9; padding: 15px; border-radius: 8px; }
  .stat-label { font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; }
  .stat-value { font-size: 22px; font-weight: 900; color: #0f172a; margin-top: 4px; }
  table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 11px; }
  th { background: #10b981; color: white; padding: 8px 10px; text-align: left; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; font-size: 9px; }
  td { padding: 6px 10px; border-bottom: 1px solid #e2e8f0; }
  tr:nth-child(even) { background: #f8fafc; }
  .footer { margin-top: 40px; padding-top: 15px; border-top: 1px solid #e2e8f0; font-size: 9px; color: #94a3b8; text-align: center; }
  @media print { .no-print { display: none; } }
</style></head><body>
  <h1>SMARTY Fitness Report</h1>
  <p style="color:#64748b; font-size:12px;">Generated ${new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
  ${profile.name ? `<p style="color:#0f172a; font-weight:600;">${profile.name}${profile.age ? ' · ' + profile.age + ' years' : ''}${profile.weight_kg ? ' · ' + profile.weight_kg + ' kg' : ''}</p>` : ''}
  <div class="stats">
    <div class="stat"><div class="stat-label">Workouts</div><div class="stat-value">${workouts.length}</div></div>
    <div class="stat"><div class="stat-label">Calories Burned</div><div class="stat-value">${totalCalBurned.toLocaleString()}</div></div>
    <div class="stat"><div class="stat-label">Minutes Active</div><div class="stat-value">${totalWorkoutMin}</div></div>
    <div class="stat"><div class="stat-label">Meals Logged</div><div class="stat-value">${meals.length}</div></div>
    <div class="stat"><div class="stat-label">Avg Sleep</div><div class="stat-value">${avgSleep}h</div></div>
    <div class="stat"><div class="stat-label">Measurements</div><div class="stat-value">${body.length}</div></div>
  </div>
  ${workouts.length > 0 ? `<h2>Recent Workouts</h2><table><tr><th>Date</th><th>Workout</th><th>Duration</th><th>Calories</th></tr>${
    workouts.slice(0, 20).map((l: any) => `<tr><td>${(l.date || l.timestamp?.split('T')[0] || '').slice(0, 10)}</td><td>${l.template || l.name || 'Workout'}</td><td>${l.duration || 0} min</td><td>${l.caloriesBurned || 0}</td></tr>`).join('')
  }</table>` : ''}
  ${body.length > 0 ? `<h2>Body Measurements</h2><table><tr><th>Date</th><th>Weight (kg)</th><th>Body Fat</th><th>Other</th></tr>${
    body.slice(-10).reverse().map((l: any) => `<tr><td>${l.date || ''}</td><td>${l.weight || l.weight_kg || '-'}</td><td>${l.bodyFat ?? l.body_fat ?? '-'}</td><td>${l.chest || l.waist || l.arms ? [l.chest ? `C:${l.chest}` : '', l.waist ? `W:${l.waist}` : '', l.arms ? `A:${l.arms}` : ''].filter(Boolean).join(' ') : '-'}</td></tr>`).join('')
  }</table>` : ''}
  ${sleep.length > 0 ? `<h2>Sleep Log</h2><table><tr><th>Date</th><th>Hours</th><th>Quality</th></tr>${
    sleep.slice(0, 14).map((l: any) => `<tr><td>${(l.date || l.timestamp?.split('T')[0] || '').slice(0, 10)}</td><td>${l.hours}h</td><td>${'★'.repeat(l.quality)}${'☆'.repeat(5 - l.quality)}</td></tr>`).join('')
  }</table>` : ''}
  <div class="footer">SMARTY AI Fitness Assistant — smarty-fitness.app</div>
  <div class="no-print" style="margin-top:20px;text-align:center;"><button onclick="window.print()" style="padding:12px 32px;background:#10b981;color:white;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:13px;">🖨️ Print / Save PDF</button></div>
  <script>window.onload = function() { setTimeout(function() { document.querySelector('button')?.click(); }, 500); }; </script>
</body></html>`;
}

export function openPrintableReport() {
  const html = generatePrintableReport();
  const w = window.open('', '_blank');
  if (w) { w.document.write(html); w.document.close(); }
}
