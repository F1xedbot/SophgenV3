import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Table from '../components/Table';
import { getGroupedInjections } from '../api';

const Injections = () => {
  const navigate = useNavigate();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');
  const limit = 20;

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await getGroupedInjections(limit, page * limit, search);
        setData(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    const timeoutId = setTimeout(() => {
        fetchData();
    }, 300); // Debounce

    return () => clearTimeout(timeoutId);
  }, [page, search]);

  const handleSearch = (val) => {
      setSearch(val);
      setPage(0); // Reset to first page on search
  };

  const columns = [
    { key: 'func_name', label: 'Function Name' },
    { key: 'injection_count', label: 'Injections', render: (row) => (
        <span className="px-2 py-1 bg-gray-700 rounded text-sm font-mono">{row.injection_count}</span>
    )},
    { key: 'cwe_labels', label: 'CWE Labels', render: (row) => (
        <div className="flex flex-wrap gap-1">
            {row.cwe_labels.split(',').map(t => (
                <span key={t} className="px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded text-xs border border-purple-500/30">{t}</span>
            ))}
        </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-white">Injections</h2>
      <Table 
        columns={columns} 
        data={data} 
        loading={loading} 
        page={page} 
        setPage={setPage} 
        hasMore={data.length === limit}
        search={search}
        onSearch={handleSearch}
        onRowClick={(row) => navigate(`/injections/group/${encodeURIComponent(row.func_name)}`)}
      />
    </div>
  );
};

export default Injections;
