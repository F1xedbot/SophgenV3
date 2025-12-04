import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Table from '../components/Table';
import { getValidations, deleteValidations } from '../api';
import { ArrowLeft, CheckCircle, XCircle, Trash2 } from 'lucide-react';

const ValidationGroup = () => {
  const { func_name } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [selectedIds, setSelectedIds] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const limit = 20;

  const fetchData = async () => {
    setLoading(true);
    try {
      // If searchQuery is present, treat it as ref_hash
      const res = await getValidations(limit, page * limit, func_name, searchQuery || undefined);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, func_name, searchQuery]);

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete ${selectedIds.length} items?`)) return;
    
    try {
        await deleteValidations(selectedIds);
        setSelectedIds([]);
        fetchData(); // Refresh data
    } catch (error) {
        console.error("Failed to delete items", error);
        alert("Failed to delete items");
    }
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'ref_hash', label: 'Ref Hash', render: (row) => <span className="font-mono text-xs">{row.ref_hash}</span> },
    { key: 'cwe_label', label: 'CWE' },
    { key: 'is_valid', label: 'Status', render: (row) => (
        <div className={`flex items-center gap-2 ${row.is_valid ? 'text-green-400' : 'text-red-400'}`}>
            {row.is_valid ? <CheckCircle size={16} /> : <XCircle size={16} />}
            {row.is_valid ? 'Valid' : 'Invalid'}
        </div>
    )},
    { key: 'timestamp', label: 'Timestamp' },
  ];

  return (
    <div className="space-y-6">
       <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
            <button 
                onClick={() => navigate(-1)} 
                className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
            >
                <ArrowLeft size={20} />
            </button>
            <h2 className="text-3xl font-bold text-white font-mono">{func_name}</h2>
        </div>

        {selectedIds.length > 0 && (
            <button
                onClick={handleDelete}
                className="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg border border-red-500/30 transition-colors"
            >
                <Trash2 size={16} />
                <span>Delete ({selectedIds.length})</span>
            </button>
        )}
      </div>
      
      <Table 
        columns={columns} 
        data={data} 
        loading={loading} 
        page={page} 
        setPage={setPage} 
        hasMore={data.length === limit}
        onRowClick={(row) => navigate(`/validations/${row.id}`)}
        enableSelection={true}
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
        onSearch={setSearchQuery}
      />
    </div>
  );
};

export default ValidationGroup;
