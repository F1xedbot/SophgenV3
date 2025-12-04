import React, { useState, useRef, useEffect } from 'react';
import { Tag, BookOpen, FileText, ChevronDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const CWETag = ({ cweLabel, className = "" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleResearchClick = async () => {
    try {
      const response = await fetch(`/api/v1/db/researches?search=${cweLabel}`);
      const data = await response.json();
      if (data && data.length > 0) {
        navigate(`/research/${data[0].id}`);
      } else {
        alert('Research details not found for this CWE.');
      }
    } catch (error) {
      console.error('Error fetching research:', error);
      alert('Failed to fetch research details.');
    }
    setIsOpen(false);
  };

  const handleKnowledgeClick = async () => {
    try {
      const response = await fetch(`/api/v1/db/condensed?search=${cweLabel}`);
      const data = await response.json();
      if (data && data.length > 0) {
        navigate(`/condensed/${data[0].id}`);
      } else {
        alert('Condensed knowledge not found for this CWE.');
      }
    } catch (error) {
      console.error('Error fetching knowledge:', error);
      alert('Failed to fetch knowledge details.');
    }
    setIsOpen(false);
  };

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium transition-colors ${className} ${isOpen ? 'ring-2 ring-purple-500/50' : ''}`}
      >
        <Tag size={14} />
        <span>{cweLabel}</span>
        <ChevronDown size={12} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-48 bg-gray-800 border border-gray-700 rounded-xl shadow-xl z-50 overflow-hidden animate-fadeIn">
          <div className="p-2 space-y-1">
            <button
              onClick={handleResearchClick}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors text-left"
            >
              <BookOpen size={16} className="text-blue-400" />
              Research Details
            </button>
            <button
              onClick={handleKnowledgeClick}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-colors text-left"
            >
              <FileText size={16} className="text-green-400" />
              Knowledge Details
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CWETag;
