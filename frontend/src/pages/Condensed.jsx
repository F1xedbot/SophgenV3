import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Table from '../components/Table';
import { getCondensed } from '../api';

const Condensed = () => {
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
        const res = await getCondensed(limit, page * limit, search);
        setData(res.data);
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

  const columns = [
    { key: 'cwe_label', label: 'CWE' },
    { key: 'support_count', label: 'Support' },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-white">Condensed Knowledge</h2>
      <Table 
        columns={columns} 
        data={data} 
        loading={loading} 
        page={page} 
        setPage={setPage} 
        hasMore={data.length === limit}
        search={search}
        onSearch={handleSearch}
        onRowClick={(row) => navigate(`/condensed/${row.id}`)}
      />
    </div>
  );
};

export default Condensed;
