import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getValidationById } from '../api';
import CWETag from '../components/CWETag';
import { ArrowLeft, Calendar, Tag, Hash, CheckCircle, XCircle, AlertTriangle, Activity, Zap, ExternalLink } from 'lucide-react';

const ValidationDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getValidationById(id);
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center text-gray-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
        Loading details...
      </div>
    );
  }

  if (!data) {
    return <div className="text-center text-red-400 mt-10">Validation entry not found.</div>;
  }

  const isValid = data.is_valid === 1;

  const getColorStyles = (color) => {
    const styles = {
        yellow: 'text-yellow-400 bg-yellow-500/10',
        blue: 'text-blue-400 bg-blue-500/10',
        green: 'text-green-400 bg-green-500/10',
        red: 'text-red-400 bg-red-500/10',
    };
    return styles[color] || styles.blue;
  };

  const ScoreCard = ({ title, score, max = 10, icon: Icon, color }) => {
      const colorClass = getColorStyles(color);
      const textColor = colorClass.split(' ')[0];
      
      return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 flex items-center justify-between">
            <div>
                <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-1">{title}</h3>
                <div className={`text-3xl font-bold ${textColor}`}>{score}<span className="text-gray-600 text-lg">/{max}</span></div>
            </div>
            <div className={`p-3 rounded-full ${colorClass}`}>
                <Icon size={24} />
            </div>
        </div>
      );
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-10">
      {/* Header */}
      <div className="space-y-4">
        <button 
            onClick={() => navigate(-1)} 
            className="flex items-center text-gray-400 hover:text-white transition-colors mb-2"
        >
            <ArrowLeft size={18} className="mr-1" /> Back
        </button>
        
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 border-b border-gray-700 pb-6">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2 font-mono">
                    {data.func_name}
                </h1>
                <div className="flex flex-wrap items-center gap-4 text-gray-500 text-sm">
                    <span className="flex items-center">
                        <Hash size={14} className="mr-1" /> ID: {data.id}
                    </span>
                    <span className="flex items-center">
                        <Calendar size={14} className="mr-1" /> {data.timestamp}
                    </span>
                    <CWETag cweLabel={data.cwe_label} className="bg-purple-500/10 text-purple-400 hover:bg-purple-500/20" />
                </div>
            </div>
            
            <div className="flex items-center gap-3">
                <div className={`px-6 py-2 rounded-full border flex items-center gap-2 font-bold ${isValid ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
                    {isValid ? <CheckCircle size={20} /> : <XCircle size={20} />}
                    {isValid ? 'VALID INJECTION' : 'INVALID INJECTION'}
                </div>
            </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ScoreCard title="Effectiveness" score={data.effectiveness} icon={Zap} color="yellow" />
          <ScoreCard title="Plausibility" score={data.plausibility} icon={Activity} color="blue" />
          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 flex items-center justify-between">
            <div>
                <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-1">Limited to ROI</h3>
                <div className={`text-2xl font-bold ${data.limited_to_roi ? 'text-green-400' : 'text-red-400'}`}>
                    {data.limited_to_roi ? 'Yes' : 'No'}
                </div>
            </div>
            <div className={`p-3 rounded-full ${data.limited_to_roi ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                {data.limited_to_roi ? <CheckCircle size={24} /> : <AlertTriangle size={24} />}
            </div>
        </div>
      </div>

      {/* Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          <section className="bg-gray-800 p-6 rounded-xl border border-gray-700 space-y-4">
              <h3 className="text-lg font-semibold text-white border-b border-gray-700 pb-2">Analysis</h3>
              
              <div>
                  <h4 className="text-sm text-gray-400 font-medium mb-1">Exploitability</h4>
                  <p className="text-gray-300 text-sm leading-relaxed">{data.exploitability}</p>
              </div>
              
              <div>
                  <h4 className="text-sm text-gray-400 font-medium mb-1">Naturalness</h4>
                  <p className="text-gray-300 text-sm leading-relaxed">{data.naturalness}</p>
              </div>

              <div>
                  <h4 className="text-sm text-gray-400 font-medium mb-1">Maintains Functionality</h4>
                  <p className="text-gray-300 text-sm leading-relaxed">{data.maintains_functionality}</p>
              </div>
          </section>

          <section className="bg-gray-800 p-6 rounded-xl border border-gray-700 space-y-4">
              <h3 className="text-lg font-semibold text-white border-b border-gray-700 pb-2">Feedback & Improvements</h3>
              
              <div className="bg-blue-900/20 p-4 rounded-lg border border-blue-500/20">
                  <h4 className="text-sm text-blue-400 font-medium mb-1 flex items-center"><Activity size={14} className="mr-1"/> Feedback</h4>
                  <p className="text-gray-300 text-sm leading-relaxed italic">"{data.feedback}"</p>
              </div>
              
              <div className="bg-purple-900/20 p-4 rounded-lg border border-purple-500/20">
                  <h4 className="text-sm text-purple-400 font-medium mb-1 flex items-center"><Zap size={14} className="mr-1"/> Suggested Improvements</h4>
                  <p className="text-gray-300 text-sm leading-relaxed italic">"{data.suggested_improvements}"</p>
              </div>
          </section>
      </div>

      {/* Metadata */}
      <section className="bg-gray-800 p-4 rounded-xl border border-gray-700/50 flex flex-wrap items-center gap-6 text-sm text-gray-400">
          <div>
              <span className="font-semibold text-gray-500 block text-xs uppercase tracking-wider">Ref Hash</span>
              <span className="font-mono text-gray-300">{data.ref_hash}</span>
          </div>
          <div>
              <span className="font-semibold text-gray-500 block text-xs uppercase tracking-wider">ROI Index</span>
              <span className="font-mono text-gray-300">{data.roi_index}</span>
          </div>
          <div>
              <span className="font-semibold text-gray-500 block text-xs uppercase tracking-wider">Lines Affected</span>
              <span className="font-mono text-gray-300">{data.lines}</span>
          </div>

          <div className="h-8 w-px bg-gray-700 mx-2 ml-auto"></div>

          <button
                onClick={async () => {
                    try {
                        const response = await fetch(`/api/v1/db/injections?ref_hash=${data.ref_hash}`);
                        const injectionData = await response.json();
                        if (injectionData && injectionData.length > 0) {
                            navigate(`/injections/${injectionData[0].id}`);
                        } else {
                            alert('No injection found for this validation.');
                        }
                    } catch (error) {
                        console.error('Error fetching injection:', error);
                        alert('Failed to check for injection.');
                    }
                }}
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg border border-gray-700 transition-colors text-sm font-medium"
            >
                <span>View Injection</span>
                <ExternalLink size={14} />
            </button>
      </section>

    </div>
  );
};

export default ValidationDetail;
