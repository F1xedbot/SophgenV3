import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getResearchById } from '../api';
import { ArrowLeft, Calendar } from 'lucide-react';

const ResearchDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getResearchById(id);
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
    return <div className="text-center text-red-400 mt-10">Research entry not found.</div>;
  }

  const parseArray = (str) => {
    try {
      return JSON.parse(str || '[]');
    } catch (e) {
      return [];
    }
  };

  const vulnerablePatterns = parseArray(data.vulnerable_code_patterns);
  const injectionPoints = parseArray(data.code_injection_points);

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-10">
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
                <h1 className="text-4xl font-bold text-white mb-2">
                    <span className="text-blue-400">{data.cwe_id}</span>: {data.cwe_name}
                </h1>
                <div className="flex items-center text-gray-500 text-sm">
                    <Calendar size={14} className="mr-2" />
                    {data.timestamp}
                </div>
            </div>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-8">
        
        {/* Typical Code Context */}
        <section className="bg-gray-800/50 p-6 rounded-xl border border-gray-700">
            <h3 className="text-xl font-semibold text-white mb-4">Typical Code Context</h3>
            <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">{data.typical_code_context}</p>
        </section>

        {/* Minimal Code Modification */}
        <section className="bg-gray-800/50 p-6 rounded-xl border border-gray-700">
            <h3 className="text-xl font-semibold text-white mb-4">Minimal Code Modification</h3>
            <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">{data.minimal_code_modification}</p>
        </section>

        {/* Vulnerable Patterns */}
        <section className="bg-gray-800/50 p-6 rounded-xl border border-gray-700">
            <h3 className="text-xl font-semibold text-white mb-4">Vulnerable Code Patterns</h3>
            <div className="space-y-4">
                {vulnerablePatterns.length > 0 ? (
                    vulnerablePatterns.map((pattern, idx) => (
                        <div key={idx} className="bg-gray-900 p-4 rounded-lg border border-red-500/20">
                            <pre className="overflow-x-auto text-sm text-gray-300 font-mono whitespace-pre-wrap">
                                {pattern}
                            </pre>
                        </div>
                    ))
                ) : (
                    <p className="text-gray-500 italic">No patterns listed.</p>
                )}
            </div>
        </section>

        {/* Injection Points */}
        <section className="bg-gray-800/50 p-6 rounded-xl border border-gray-700">
            <h3 className="text-xl font-semibold text-white mb-4">Code Injection Points</h3>
            <div className="space-y-4">
                {injectionPoints.length > 0 ? (
                    injectionPoints.map((point, idx) => (
                        <div key={idx} className="bg-gray-900 p-4 rounded-lg border border-yellow-500/20">
                            <pre className="overflow-x-auto text-sm text-gray-300 font-mono whitespace-pre-wrap">
                                {point}
                            </pre>
                        </div>
                    ))
                ) : (
                    <p className="text-gray-500 italic">No injection points listed.</p>
                )}
            </div>
        </section>

      </div>
    </div>
  );
};

export default ResearchDetail;
