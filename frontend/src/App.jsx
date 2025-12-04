import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Injections from './pages/Injections';
import InjectionGroup from './pages/InjectionGroup';
import InjectionDetail from './pages/InjectionDetail';
import Validations from './pages/Validations';
import ValidationGroup from './pages/ValidationGroup';
import ValidationDetail from './pages/ValidationDetail';
import Research from './pages/Research';
import ResearchDetail from './pages/ResearchDetail';
import Condensed from './pages/Condensed';
import CondensedDetail from './pages/CondensedDetail';
import Placeholder from './pages/Placeholder';
import Generation from './pages/Generation';

const App = () => {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/injections" element={<Injections />} />
          <Route path="/injections/group/:func_name" element={<InjectionGroup />} />
          <Route path="/injections/:id" element={<InjectionDetail />} />
          <Route path="/validations" element={<Validations />} />
          <Route path="/validations/group/:func_name" element={<ValidationGroup />} />
          <Route path="/validations/:id" element={<ValidationDetail />} />
          <Route path="/research" element={<Research />} />
          <Route path="/research/:id" element={<ResearchDetail />} />
          <Route path="/condensed" element={<Condensed />} />
          <Route path="/condensed/:id" element={<CondensedDetail />} />
          
          {/* Generation */}
          <Route path="/generation" element={<Generation />} />
          
          {/* Batch Jobs */}
          <Route path="/batch/injection" element={<Placeholder title="Batch Injection" />} />
          <Route path="/batch/research" element={<Placeholder title="Batch Research" />} />
          <Route path="/batch/validation" element={<Placeholder title="Batch Validation" />} />
          <Route path="/batch/full" element={<Placeholder title="Batch Full Pipeline" />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
