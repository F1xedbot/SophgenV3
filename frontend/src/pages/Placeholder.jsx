import React from 'react';
import { Construction } from 'lucide-react';

const Placeholder = ({ title }) => {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] text-gray-500 space-y-4">
      <div className="p-6 bg-gray-800 rounded-full border border-gray-700">
        <Construction size={48} className="text-blue-400" />
      </div>
      <h2 className="text-2xl font-bold text-gray-300">{title || 'Under Construction'}</h2>
      <p className="text-gray-400 max-w-md text-center">
        This feature is currently being implemented. Please check back later.
      </p>
    </div>
  );
};

export default Placeholder;
