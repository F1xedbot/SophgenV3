import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getInjectionById } from '../api';
import CWETag from '../components/CWETag';
import { ArrowLeft, Calendar, Tag, Hash, Code, ExternalLink } from 'lucide-react';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';

const InjectionDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getInjectionById(id);
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
    return <div className="text-center text-red-400 mt-10">Injection entry not found.</div>;
  }

  const parseArray = (str) => {
    try {
      return JSON.parse(str || '[]');
    } catch (e) {
      return [];
    }
  };

  const tags = parseArray(data.tags);

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
        </div>
      </div>

      {/* Tags */}
      {tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
              {tags.map((tag, idx) => (
                  <span key={idx} className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm border border-blue-500/30">
                      {tag}
                  </span>
              ))}
          </div>
      )}


      {/* Code Comparison */}
      <div className="bg-gray-800/50 rounded-xl border border-gray-700 overflow-hidden">
          <div className="bg-gray-900/50 px-4 py-3 border-b border-gray-700 font-semibold text-gray-300 flex items-center justify-between">
              <div className="flex items-center">
                  <Code size={16} className="mr-2" /> Code Transformation
              </div>
              <div className="text-xs text-gray-500">
                  Left: Original | Right: Transformed
              </div>
          </div>
          <div className="p-0">
            <ReactDiffViewer 
                oldValue={data.original_pattern} 
                newValue={data.transformed_code} 
                splitView={true}
                compareMethod={DiffMethod.WORDS}
                useDarkTheme={true}
                styles={{
                    variables: {
                        dark: {
                            diffViewerBackground: '#111827', // gray-900
                            diffViewerColor: '#d1d5db', // gray-300
                            addedBackground: '#064e3b', // green-900
                            addedColor: '#34d399', // green-400
                            removedBackground: '#7f1d1d', // red-900
                            removedColor: '#f87171', // red-400
                            wordAddedBackground: '#065f46',
                            wordRemovedBackground: '#991b1b',
                            gutterBackground: '#1f2937', // gray-800
                            gutterColor: '#6b7280', // gray-500
                        }
                    },
                    lineNumber: {
                        color: '#6b7280',
                    },
                    contentText: {
                        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                        fontSize: '0.875rem',
                        lineHeight: '1.5',
                    }
                }}
            />
          </div>
      </div>

      {/* LLM Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <section className="bg-gray-800/50 p-6 rounded-xl border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-3 text-blue-400">Modification</h3>
              <p className="text-gray-300 text-sm leading-relaxed">{data.modification}</p>
          </section>

          <section className="bg-gray-800/50 p-6 rounded-xl border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-3 text-purple-400">Camouflage</h3>
              <p className="text-gray-300 text-sm leading-relaxed">{data.camouflage}</p>
          </section>

          <section className="bg-gray-800/50 p-6 rounded-xl border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-3 text-red-400">Attack Vector</h3>
              <p className="text-gray-300 text-sm leading-relaxed">{data.attack_vec}</p>
          </section>
      </div>

      {/* Metadata */}
      <section className="bg-gray-800/30 p-4 rounded-xl border border-gray-700/50 flex flex-wrap items-center gap-6 text-sm text-gray-400">
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
                        const response = await fetch(`/api/v1/db/validations?ref_hash=${data.ref_hash}`);
                        const validationData = await response.json();
                        if (validationData && validationData.length > 0) {
                            navigate(`/validations/${validationData[0].id}`);
                        } else {
                            alert('No validation found for this injection.');
                        }
                    } catch (error) {
                        console.error('Error fetching validation:', error);
                        alert('Failed to check for validation.');
                    }
                }}
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg border border-gray-700 transition-colors text-sm font-medium"
            >
                <span>View Validation</span>
                <ExternalLink size={14} />
            </button>
      </section>

    </div>
  );
};

export default InjectionDetail;
