import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCondensedById } from '../api';
import { ArrowLeft, Calendar, Tag, Hash, ThumbsUp, CheckCircle, XCircle, Code, Lightbulb } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const CondensedDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getCondensedById(id);
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
    return <div className="text-center text-red-400 mt-10">Condensed knowledge not found.</div>;
  }

  const parseArray = (str) => {
    try {
      return JSON.parse(str || '[]');
    } catch (e) {
      return [];
    }
  };

  const examples = parseArray(data.examples);
  const reasons = parseArray(data.reasons);

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
                <h1 className="text-4xl font-bold text-white mb-2 font-mono">
                    {data.cwe_label}
                </h1>
                <div className="flex flex-wrap items-center gap-4 text-gray-500 text-sm">
                    <span className="flex items-center">
                        <Hash size={14} className="mr-1" /> ID: {data.id}
                    </span>
                    <span className="flex items-center">
                        <Calendar size={14} className="mr-1" /> {data.timestamp}
                    </span>
                </div>
            </div>
            
            <div className="px-6 py-3 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 rounded-full text-blue-400">
                    <ThumbsUp size={20} />
                </div>
                <div>
                    <div className="text-xs text-blue-300 uppercase font-bold tracking-wider">Support</div>
                    <div className="text-2xl font-bold text-white">{data.support_count}</div>
                </div>
            </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* What Works */}
          <section className="space-y-4">
              <div className="flex items-center gap-2 text-green-400 font-bold text-lg border-b border-gray-700 pb-2">
                  <CheckCircle size={20} /> What Works
              </div>
              <div className="bg-gray-800 p-6 rounded-xl text-gray-300 leading-relaxed shadow-lg">
                  <div className="prose prose-invert max-w-none prose-sm">
                    <ReactMarkdown>{data.works_text}</ReactMarkdown>
                  </div>
              </div>
          </section>

          {/* What to Avoid */}
          <section className="space-y-4">
              <div className="flex items-center gap-2 text-red-400 font-bold text-lg border-b border-gray-700 pb-2">
                  <XCircle size={20} /> What to Avoid
              </div>
              <div className="bg-gray-800 p-6 rounded-xl text-gray-300 leading-relaxed shadow-lg">
                  <div className="prose prose-invert max-w-none prose-sm">
                    <ReactMarkdown>{data.avoid_text}</ReactMarkdown>
                  </div>
              </div>
          </section>
      </div>

      {/* Examples & Reasons */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Examples */}
          <section className="space-y-4">
              <div className="flex items-center gap-2 text-yellow-400 font-bold text-lg border-b border-gray-700 pb-2">
                  <Code size={20} /> Examples
              </div>
              <div className="space-y-4">
                  {examples.length > 0 ? (
                      examples.map((ex, idx) => (
                          <div key={idx} className="bg-gray-900 p-4 rounded-lg border border-gray-700 font-mono text-sm text-gray-300 overflow-x-auto whitespace-pre-wrap shadow-inner">
                              {ex}
                          </div>
                      ))
                  ) : (
                      <div className="text-gray-500 italic">No examples provided.</div>
                  )}
              </div>
          </section>

          {/* Reasons */}
          <section className="space-y-4">
              <div className="flex items-center gap-2 text-purple-400 font-bold text-lg border-b border-gray-700 pb-2">
                  <Lightbulb size={20} /> Reasons
              </div>
              <div className="space-y-4">
                  {reasons.length > 0 ? (
                      reasons.map((reason, idx) => (
                          <div key={idx} className="bg-gray-800 p-4 rounded-lg text-gray-300 flex gap-3 shadow-md">
                              <div className="mt-1 text-purple-400 flex-shrink-0">•</div>
                              <div>{reason}</div>
                          </div>
                      ))
                  ) : (
                      <div className="text-gray-500 italic">No reasons provided.</div>
                  )}
              </div>
          </section>
      </div>

    </div>
  );
};

export default CondensedDetail;
