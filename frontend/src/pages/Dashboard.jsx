import React, { useEffect, useState } from 'react';
import { getStats } from '../api';
import { 
  Activity, 
  Database, 
  Fingerprint, 
  Search, 
  ShieldCheck, 
  Target, 
  Zap,
  Code
} from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState({
    counts: {
      injections: 0,
      validations: 0,
      researches: 0,
      condenser: 0
    },
    metrics: {
      pass_rate: 0,
      avg_plausibility: 0,
      avg_effectiveness: 0,
      unique_cwes: 0
    }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await getStats();
        if (response.data) {
          setStats(response.data);
        }
      } catch (error) {
        console.error("Failed to fetch stats", error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const countItems = [
    { 
      label: 'Injections', 
      key: 'injections', 
      icon: Zap, 
      color: 'text-cyan-400', 
      bg: 'bg-cyan-400/10',
      border: 'border-cyan-400/20'
    },
    { 
      label: 'Validations', 
      key: 'validations', 
      icon: ShieldCheck, 
      color: 'text-emerald-400', 
      bg: 'bg-emerald-400/10',
      border: 'border-emerald-400/20'
    },
    { 
      label: 'Research', 
      key: 'researches', 
      icon: Search, 
      color: 'text-violet-400', 
      bg: 'bg-violet-400/10',
      border: 'border-violet-400/20'
    },
    { 
      label: 'Condensed', 
      key: 'condenser', 
      icon: Database, 
      color: 'text-amber-400', 
      bg: 'bg-amber-400/10',
      border: 'border-amber-400/20'
    }
  ];

  const metricItems = [
    { 
      label: 'Pass Rate', 
      key: 'pass_rate', 
      suffix: '%', 
      icon: Activity,
      color: 'text-blue-400',
      bg: 'bg-blue-400/10'
    },
    { 
      label: 'Avg Plausibility', 
      key: 'avg_plausibility', 
      suffix: '/10', 
      icon: Fingerprint,
      color: 'text-pink-400',
      bg: 'bg-pink-400/10'
    },
    { 
      label: 'Avg Effectiveness', 
      key: 'avg_effectiveness', 
      suffix: '/10', 
      icon: Target,
      color: 'text-orange-400',
      bg: 'bg-orange-400/10'
    },
    { 
      label: 'Unique CWEs', 
      key: 'unique_cwes', 
      suffix: '', 
      icon: Code,
      color: 'text-indigo-400',
      bg: 'bg-indigo-400/10'
    }
  ];

  return (
    <div className="space-y-10 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 mb-6 flex items-center gap-2">
          <Activity className="w-6 h-6 text-blue-500" />
          System Overview
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {countItems.map((item) => (
            <div 
              key={item.label} 
              className={`relative group p-6 rounded-2xl border ${item.border} bg-gray-900/50 backdrop-blur-sm hover:bg-gray-800/80 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-${item.color.split('-')[1]}-500/10`}
            >
              <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl ${item.bg} ${item.color}`}>
                  <item.icon className="w-6 h-6" />
                </div>
                <div className={`text-xs font-medium px-2 py-1 rounded-full ${item.bg} ${item.color} opacity-0 group-hover:opacity-100 transition-opacity`}>
                  Live
                </div>
              </div>
              <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-1">{item.label}</h3>
              <p className="text-4xl font-bold text-white tracking-tight">
                {loading ? (
                  <span className="animate-pulse">...</span>
                ) : (
                  stats?.counts?.[item.key]?.toLocaleString() || 0
                )}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 mb-6 flex items-center gap-2">
          <Target className="w-6 h-6 text-emerald-500" />
          Quality Metrics
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metricItems.map((item) => (
            <div 
              key={item.label} 
              className="group p-6 rounded-2xl border border-gray-800 bg-gray-900/30 hover:bg-gray-800/50 transition-all duration-300"
            >
              <div className="flex items-center gap-3 mb-3">
                <item.icon className={`w-5 h-5 ${item.color}`} />
                <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider">{item.label}</h3>
              </div>
              <p className={`text-3xl font-bold ${item.color} tracking-tight`}>
                {loading ? (
                  <span className="animate-pulse">...</span>
                ) : (
                  <>
                    {stats?.metrics?.[item.key] || 0}
                    <span className="text-lg text-gray-500 ml-1 font-normal">{item.suffix}</span>
                  </>
                )}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
