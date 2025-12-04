import React from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';

const Table = ({ columns, data, loading, page, setPage, hasMore, search, onSearch, onRowClick, enableSelection, selectedIds, onSelectionChange }) => {
  
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      onSelectionChange(data.map(row => row.id));
    } else {
      onSelectionChange([]);
    }
  };

  const handleSelectRow = (id) => {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter(sid => sid !== id));
    } else {
      onSelectionChange([...selectedIds, id]);
    }
  };

  if (loading && data.length === 0) {
    return (
      <div className="w-full h-64 flex items-center justify-center text-gray-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
        Loading data...
      </div>
    );
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden shadow-xl flex flex-col">
      {/* Top Controls: Search & Pagination */}
      <div className="bg-gray-900 px-6 py-4 border-b border-gray-700 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-64">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search size={16} className="text-gray-500" />
            </div>
            <input 
                type="text" 
                value={search}
                placeholder="Search..." 
                className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2.5 placeholder-gray-500"
                onChange={(e) => onSearch && onSearch(e.target.value)}
            />
        </div>

        {/* Pagination */}
        <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-400">
                Page {page + 1}
            </span>
            <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-400 hidden sm:inline">
                    {data.length > 0 ? `${data.length} entries` : 'No data'}
                </span>
                <div className="flex space-x-1">
                    <button
                        onClick={() => setPage(p => Math.max(0, p - 1))}
                        disabled={page === 0}
                        className="p-1.5 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-400 transition-colors"
                    >
                        <ChevronLeft size={18} />
                    </button>
                    <button
                        onClick={() => setPage(p => p + 1)}
                        disabled={!hasMore}
                        className="p-1.5 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-400 transition-colors"
                    >
                        <ChevronRight size={18} />
                    </button>
                </div>
            </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-900 text-gray-400 uppercase tracking-wider font-medium">
            <tr>
              {enableSelection && (
                <th className="px-6 py-4 border-b border-gray-700 w-10">
                  <input 
                    type="checkbox" 
                    className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900"
                    checked={data.length > 0 && selectedIds.length === data.length}
                    onChange={handleSelectAll}
                  />
                </th>
              )}
              {columns.map((col) => (
                <th key={col.key} className="px-6 py-4 border-b border-gray-700 whitespace-nowrap">
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {loading ? (
                 <tr>
                    <td colSpan={columns.length + (enableSelection ? 1 : 0)} className="px-6 py-8 text-center text-gray-500">
                        <div className="flex justify-center items-center">
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500 mr-2"></div>
                            Refreshing...
                        </div>
                    </td>
                 </tr>
            ) : data.length === 0 ? (
                <tr>
                    <td colSpan={columns.length + (enableSelection ? 1 : 0)} className="px-6 py-8 text-center text-gray-500">
                        No results found.
                    </td>
                </tr>
            ) : (
                (Array.isArray(data) ? data : []).map((row, i) => (
                <tr 
                    key={i} 
                    onClick={() => onRowClick && onRowClick(row)}
                    className={`border-b border-gray-700 hover:bg-gray-700 transition-colors ${onRowClick ? 'cursor-pointer' : ''}`}
                >
                    {enableSelection && (
                        <td className="px-6 py-4 w-10" onClick={(e) => e.stopPropagation()}>
                          <input 
                            type="checkbox" 
                            className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900"
                            checked={selectedIds.includes(row.id)}
                            onChange={() => handleSelectRow(row.id)}
                          />
                        </td>
                    )}
                    {columns.map((col) => (
                    <td key={col.key} className="px-6 py-4 text-gray-300 whitespace-pre-wrap max-w-xs truncate">
                        {col.render ? col.render(row) : row[col.key]}
                    </td>
                    ))}
                </tr>
                ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Table;
