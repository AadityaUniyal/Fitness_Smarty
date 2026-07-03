// Lightweight translation store for English and Hindi locales (react-i18n mapping)
const translations: Record<string, Record<string, string>> = {
  en: {
    dashboard_title: "Mission Control",
    current_state: "Current State",
    todays_progress: "Today's Progress",
    recommended_workout: "Recommended Workout",
    recommended_foods: "Recommended Foods",
    indian_foods: "Indian Foods",
    protein_goal: "Protein Goal",
    streak_count: "Streak Count",
  },
  hi: {
    dashboard_title: "मिशन कंट्रोल",
    current_state: "वर्तमान स्थिति",
    todays_progress: "आज की प्रगति",
    recommended_workout: "अनुशंसित व्यायाम",
    recommended_foods: "अनुशंसित भोजन",
    indian_foods: "भारतीय भोजन",
    protein_goal: "प्रोटीन लक्ष्य",
    streak_count: "लगातार दिन",
  }
};

class TranslationEngine {
  private currentLang: 'en' | 'hi' = 'en';
  private listeners: Set<() => void> = new Set();

  setLanguage(lang: 'en' | 'hi') {
    this.currentLang = lang;
    localStorage.setItem('smarty_lang', lang);
    this.listeners.forEach(l => l());
  }

  getLanguage() {
    return this.currentLang;
  }

  t(key: string): string {
    const locale = translations[this.currentLang];
    return locale ? (locale[key] || key) : key;
  }

  subscribe(listener: () => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
}

// Global instance matching i18next interface behavior
export const i18n = new TranslationEngine();
// Auto load preference
if (typeof localStorage !== 'undefined') {
  const saved = localStorage.getItem('smarty_lang') as 'en' | 'hi';
  if (saved === 'hi' || saved === 'en') {
    i18n.setLanguage(saved);
  }
}
