import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Table from '../components/Table';
import { getGroupedValidations } from '../api';

const Validations = () => {
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
        const res = await getGroupedValidations(limit, page * limit, search);
        setData(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    const timeoutId = setTimeout(() => {
        fetchData();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [page, search]);

  const handleSearch = (val) => {
      setSearch(val);
      setPage(0);
  };

  const getScoreColor = (score) => {
    // Gradient from Red (0) to Green (1)
    if (score < 0.5) return 'text-red-400';
    if (score < 0.8) return 'text-yellow-400';
    return 'text-green-400';
  };

  const columns = [
    { key: 'func_name', label: 'Function Name' },
    { key: 'validation_count', label: 'Validations', render: (row) => (
        <span className="px-2 py-1 bg-gray-700 rounded text-sm font-mono">{row.validation_count}</span>
    )},
    { key: 'pass_rate', label: 'Pass Rate', render: (row) => (
        <div className="w-full bg-gray-700 rounded-full h-2.5 dark:bg-gray-700 relative">
            <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${row.pass_rate}%` }}></div>
            <span className="absolute top-3 text-xs text-gray-400">{row.pass_rate.toFixed(1)}%</span>
        </div>
    )},
    { key: 'plausibility_score', label: 'Plausibility', render: (row) => (
        <span className={`font-bold ${getScoreColor(row.plausibility_score)}`}>
            {(row.plausibility_score * 10).toFixed(1)}
        </span>
    )},
    { key: 'effectiveness_score', label: 'Effectiveness', render: (row) => (
        <span className={`font-bold ${getScoreColor(row.effectiveness_score)}`}>
            {(row.effectiveness_score * 10).toFixed(1)}
        </span>
    )},
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-white">Validations</h2>
      <Table 
        columns={columns} 
        data={data} 
        loading={loading} 
        page={page} 
        setPage={setPage} 
        hasMore={data.length === limit}
        search={search}
        onSearch={handleSearch}
        onRowClick={(row) => navigate(`/validations/group/${encodeURIComponent(row.func_name)}`)}
      />
    </div>
  );
};

export default Validations;
