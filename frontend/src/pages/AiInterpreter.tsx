import React, { useState, useEffect } from 'react';
import { 
  BrainCircuit, Activity, Cpu, Database, TrendingUp, RefreshCw, Sparkles, 
  HelpCircle, ShieldCheck, Play, ArrowRight, CheckCircle2, AlertTriangle, Info 
} from 'lucide-react';
import { DeepTechService, SHAPExplanation, FeatureImportance, DecisionPath } from '../services/deepTechService';
import { Reveal } from '../components/Reveal';

interface NodeStatusInfo {
  name: string;
  type: string;
  status: 'ready' | 'mock' | 'offline';
  device?: string;
  description: string;
}

const AiInterpreter: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modelStatuses, setModelStatuses] = useState<NodeStatusInfo[]>([]);
  const [activeModel, setActiveModel] = useState<string>('collaborative_filtering');
  const [featureImportance, setFeatureImportance] = useState<FeatureImportance | null>(null);
  const [decisionPath, setDecisionPath] = useState<DecisionPath | null>(null);
  const [sampleMeal, setSampleMeal] = useState({ name: 'Grilled Chicken & Quinoa Bowl', calories: 580 });
  const [shapExplanation, setShapExplanation] = useState<SHAPExplanation | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch all interpreter data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch backend neural health status
      const health = await DeepTechService.getNeuralNetworkHealth();
      const nodeStatuses: NodeStatusInfo[] = [];

      // Vision Node
      if (health.vision && health.vision.models) {
        Object.entries(health.vision.models).forEach(([name, m]: [string, any]) => {
          nodeStatuses.push({
            name: name.toUpperCase(),
            type: 'Computer Vision',
            status: m.status === 'ready' ? 'ready' : m.status === 'mock' ? 'mock' : 'offline',
            description: m.description
          });
        });
      } else {
        nodeStatuses.push({ name: 'VISION CORE', type: 'Computer Vision', status: 'offline', description: 'YOLOv8 and ResNet classification modules' });
      }

      // Reinforcement Learning Node
      if (health.rl && health.rl.models) {
        Object.entries(health.rl.models).forEach(([name, m]: [string, any]) => {
          nodeStatuses.push({
            name: name.toUpperCase(),
            type: 'Reinforcement Learning',
            status: m.status === 'ready' ? 'ready' : m.status === 'mock' ? 'mock' : 'offline',
            description: m.description
          });
        });
      } else {
        nodeStatuses.push({ name: 'DQN SEQUENCER', type: 'Reinforcement Learning', status: 'offline', description: 'Meal sequence deep Q-network optimizer' });
      }

      // Forecasting Node
      if (health.forecast && health.forecast.models) {
        Object.entries(health.forecast.models).forEach(([name, m]: [string, any]) => {
          nodeStatuses.push({
            name: name.toUpperCase(),
            type: 'Time-Series Forecast',
            status: m.status === 'ready' ? 'ready' : m.status === 'mock' ? 'mock' : 'offline',
            description: m.description
          });
        });
      } else {
        nodeStatuses.push({ name: 'LSTM WEIGHT PREDICTOR', type: 'Time-Series Forecast', status: 'offline', description: 'LSTM weight progression predictor' });
      }

      // Explainability Node
      if (health.explainability && health.explainability.models) {
        Object.entries(health.explainability.models).forEach(([name, m]: [string, any]) => {
          nodeStatuses.push({
            name: name.toUpperCase(),
            type: 'Explainable AI (XAI)',
            status: m.status === 'ready' ? 'ready' : m.status === 'mock' ? 'mock' : 'offline',
            description: m.description
          });
        });
      } else {
        nodeStatuses.push({ name: 'SHAP EXPLAINER', type: 'Explainable AI', status: 'offline', description: 'Game-theoretic model interpretability pipeline' });
      }

      setModelStatuses(nodeStatuses);

      // 2. Fetch SHAP values for active algorithm
      const importance = await DeepTechService.getFeatureImportance(activeModel);
      setFeatureImportance(importance);

      // 3. Fetch default decision path
      const path = await DeepTechService.getDecisionPath(sampleMeal.name, sampleMeal.calories);
      setDecisionPath(path);

      // 4. Fetch Sample SHAP explanation for meal
      const explanation = await DeepTechService.explainRecommendation(
        101, 
        sampleMeal.name, 
        0.91, 
        160, // 160g protein target
        2200, // 2200 cal target
        ['chicken', 'quinoa', 'avocado']
      );
      setShapExplanation(explanation);

    } catch (e: any) {
      console.error(e);
      setError('Connection to Neural Core offline. Utilizing cached simulation data.');
      // Load fallback simulation data
      setFallbackData();
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const setFallbackData = () => {
    setModelStatuses([
      { name: 'YOLOV8 FOOD DETECTOR', type: 'Computer Vision', status: 'mock', description: 'Real-time object detection with bounding boxes' },
      { name: 'RESNET50 CLASSIFIER', type: 'Computer Vision', status: 'mock', description: 'High-accuracy food classification' },
      { name: 'MASKRCNN PORTION ESTIMATOR', type: 'Computer Vision', status: 'mock', description: 'Pixel-level segmentation for accurate portions' },
      { name: 'DQN MEAL SEQUENCER', type: 'Reinforcement Learning', status: 'mock', description: 'Deep Q-Network for optimal meal sequencing' },
      { name: 'Q_LEARNING HABIT FORMER', type: 'Reinforcement Learning', status: 'mock', description: 'Q-Learning for habit formation plans' },
      { name: 'LSTM WEIGHT MODEL', type: 'Time-Series Forecast', status: 'mock', description: 'Weight prediction using LSTM neural networks' },
      { name: 'PROPHET TREND ANALYZER', type: 'Time-Series Forecast', status: 'mock', description: 'Nutrition trend analysis and forecasting' },
      { name: 'SHAP EXPLAINER', type: 'Explainable AI (XAI)', status: 'mock', description: 'SHAP values for feature importance' },
    ]);

    setFeatureImportance({
      model: activeModel,
      features: activeModel === 'collaborative_filtering' ? {
        'user_similarity': 0.45,
        'meal_popularity': 0.30,
        'recent_preferences': 0.15,
        'time_of_day': 0.10
      } : {
        'nutrition_match': 0.40,
        'ingredient_similarity': 0.35,
        'calorie_target': 0.15,
        'dietary_restrictions': 0.10
      },
      top_features: activeModel === 'collaborative_filtering' 
        ? [['user_similarity', 0.45], ['meal_popularity', 0.30], ['recent_preferences', 0.15], ['time_of_day', 0.10]]
        : [['nutrition_match', 0.40], ['ingredient_similarity', 0.35], ['calorie_target', 0.15], ['dietary_restrictions', 0.10]]
    });

    setDecisionPath({
      decision_path: [
        { step: 1, condition: 'User needs high protein (target: 160g)', action: 'Filter for protein > 30g per meal', result: '15 meals remaining' },
        { step: 2, condition: 'User prefers chicken (75% of history)', action: 'Prioritize chicken-based meals', result: '8 meals remaining' },
        { step: 3, condition: 'Calorie budget: 500-600 kcal', action: 'Filter by calorie range', result: '3 meals remaining' },
        { step: 4, condition: 'Similar users loved this meal', action: 'Select top collaborative match', result: `Final recommendation: ${sampleMeal.name}` }
      ],
      final_prediction: { name: sampleMeal.name, score: 0.91 },
      confidence: 0.89
    });

    setShapExplanation({
      recommendation: sampleMeal.name,
      shap_values: {
        'protein_match': 0.40,
        'calorie_match': 0.30,
        'user_history': 0.20,
        'time_of_day': 0.10
      },
      explanation: 'Recommended due to high protein content matching your goals',
      confidence: 0.82,
      model: 'shap_mock'
    });
  };

  useEffect(() => {
    fetchData();
  }, [activeModel]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const getStatusBadge = (status: 'ready' | 'mock' | 'offline') => {
    switch (status) {
      case 'ready':
        return <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[8px] font-black uppercase tracking-wider rounded-md">ONLINE</span>;
      case 'mock':
        return <span className="px-2 py-0.5 bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[8px] font-black uppercase tracking-wider rounded-md">SIMULATED</span>;
      case 'offline':
        return <span className="px-2 py-0.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-[8px] font-black uppercase tracking-wider rounded-md">OFFLINE</span>;
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-4xl font-black italic tracking-tighter text-white">
            NEURAL <span className="text-emerald-400">INTERPRETER</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Visualizing Model Interpretability, SHAP Values, and Neural Node health checks.
          </p>
        </div>
        <button 
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center space-x-2 px-4 py-2.5 bg-slate-900 border border-white/10 hover:border-emerald-500/30 rounded-xl text-slate-300 text-xs font-black transition-all active:scale-95 disabled:opacity-50"
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          <span>Sync Neural Network</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-amber-500/5 border border-amber-500/20 rounded-2xl flex items-center space-x-3 text-amber-400">
          <Info size={16} />
          <p className="text-xs font-bold">{error}</p>
        </div>
      )}

      {/* Model Health Status Grid */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <Cpu size={16} className="text-emerald-400" />
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Neural Network Nodes Health</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {modelStatuses.map((node, i) => (
            <div key={i} className="p-4 bg-slate-950 border border-white/5 rounded-2xl flex flex-col justify-between hover:border-emerald-500/10 transition duration-300">
              <div className="space-y-1">
                <div className="flex justify-between items-start gap-2">
                  <p className="text-[9px] font-black text-slate-500 uppercase tracking-wide truncate">{node.type}</p>
                  {getStatusBadge(node.status)}
                </div>
                <h4 className="text-sm font-black text-white truncate tracking-tight">{node.name.replace(/_/g, ' ')}</h4>
                <p className="text-[10px] text-slate-400 leading-normal line-clamp-2">{node.description}</p>
              </div>
              <div className="mt-3 flex items-center space-x-1.5 text-[8px] text-slate-600 font-bold uppercase tracking-widest">
                <Activity size={10} className="text-emerald-500" />
                <span>Node Active • 100% latency</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SHAP Explainer Card */}
        <div className="lg:col-span-2 p-6 bg-slate-900 border border-white/10 rounded-3xl space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-emerald-500/10 rounded-lg">
                <BrainCircuit size={18} className="text-emerald-400" />
              </div>
              <div>
                <p className="text-xs font-black text-white uppercase tracking-widest">SHAP Model Explanation</p>
                <p className="text-[9px] text-slate-500">Feature impact weighting on recommendation scores</p>
              </div>
            </div>

            {/* Model Select */}
            <div className="flex bg-slate-950/80 p-1 rounded-xl border border-white/5">
              {[
                { id: 'collaborative_filtering', label: 'Collab' },
                { id: 'content_based', label: 'Content' }
              ].map(m => (
                <button
                  key={m.id}
                  onClick={() => setActiveModel(m.id)}
                  className={`px-3 py-1.5 text-[8px] font-black uppercase tracking-widest rounded-lg transition-all ${
                    activeModel === m.id 
                      ? 'bg-emerald-500 text-slate-950 shadow-[0_2px_8px_rgba(16,185,129,0.3)]' 
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {/* Bar Chart representing feature weight impact */}
          {featureImportance && (
            <div className="space-y-4 pt-2">
              {Object.entries(featureImportance.features).map(([feature, val], index) => {
                const percentage = Math.round(val * 100);
                return (
                  <div key={feature} className="space-y-1.5 animate-in fade-in duration-300" style={{ animationDelay: `${index * 100}ms` }}>
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-black uppercase tracking-widest text-[9px] text-slate-400">
                        {feature.replace(/_/g, ' ')}
                      </span>
                      <span className="font-black text-emerald-400">{percentage}% Weight</span>
                    </div>
                    <div className="h-2.5 bg-slate-950 rounded-full overflow-hidden border border-white/5 relative">
                      <div 
                        className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full transition-all duration-1000"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Core Reasoning */}
          {shapExplanation && (
            <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl flex items-start space-x-3">
              <Sparkles size={16} className="text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-[10px] font-black text-emerald-400 uppercase tracking-widest mb-1">AI Recommendation Context</p>
                <p className="text-xs text-slate-300 leading-relaxed font-bold uppercase italic">
                  "{shapExplanation.explanation}"
                </p>
                <p className="text-[9px] text-slate-500 mt-2">
                  Prediction Confidence: {(shapExplanation.confidence * 100).toFixed(0)}% • Model: {shapExplanation.model}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Model Decision Path Card */}
        <div className="p-6 bg-slate-900 border border-white/10 rounded-3xl space-y-6 flex flex-col justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-cyan-500/10 rounded-lg">
              <TrendingUp size={18} className="text-cyan-400" />
            </div>
            <div>
              <p className="text-xs font-black text-white uppercase tracking-widest">Neural Decision Path</p>
              <p className="text-[9px] text-slate-500">Logical trace through neural filters</p>
            </div>
          </div>

          {/* Decision tree list */}
          {decisionPath && (
            <div className="flex-1 space-y-4 my-6 overflow-y-auto pr-1">
              {decisionPath.decision_path.map((step, i) => (
                <div key={i} className="flex gap-3 relative">
                  {i < decisionPath.decision_path.length - 1 && (
                    <div className="absolute left-2.5 top-5 bottom-[-18px] w-[1px] bg-slate-800" />
                  )}
                  <div className="w-5 h-5 rounded-full bg-slate-950 border border-cyan-500/40 text-[9px] font-black flex items-center justify-center text-cyan-400 shrink-0 relative z-10">
                    {step.step}
                  </div>
                  <div className="space-y-1">
                    <p className="text-[9px] font-black text-cyan-400 uppercase tracking-widest">{step.condition}</p>
                    <p className="text-xs text-slate-300 font-bold leading-normal">{step.action}</p>
                    <p className="text-[8px] text-slate-500 font-black uppercase tracking-wider">{step.result}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="p-4 bg-slate-950 border border-white/5 rounded-2xl flex items-center justify-between">
            <div>
              <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest">Target Objective</p>
              <p className="text-xs font-black text-white leading-normal truncate">{sampleMeal.name}</p>
            </div>
            <div className="text-right shrink-0">
              <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest">Score</p>
              <p className="text-xs font-black text-emerald-400">91% Fit</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AiInterpreter;
