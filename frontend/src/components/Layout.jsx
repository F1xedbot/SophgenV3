import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  ShieldAlert, 
  CheckCircle, 
  BookOpen, 
  FileText, 
  Zap, 
  Layers, 
  Microscope, 
  ClipboardCheck, 
  PlayCircle 
} from 'lucide-react';

const Layout = ({ children }) => {
  const location = useLocation();

  const navSections = [
    {
      title: 'Dashboard',
      items: [
        { path: '/', label: 'Dashboard', icon: LayoutDashboard }
      ]
    },
    {
      title: 'My Collections',
      items: [
        { path: '/injections', label: 'Injections', icon: ShieldAlert },
        { path: '/validations', label: 'Validations', icon: CheckCircle },
        { path: '/research', label: 'Research', icon: BookOpen },
        { path: '/condensed', label: 'Knowledge', icon: FileText },
      ]
    },
    {
      title: 'Generation',
      items: [
        { path: '/generation', label: 'New Generation', icon: Zap }
      ]
    },
    {
      title: 'Batch Job',
      items: [
        { path: '/batch/injection', label: 'Batch Injection', icon: Layers },
        { path: '/batch/research', label: 'Batch Research', icon: Microscope },
        { path: '/batch/validation', label: 'Batch Validation', icon: ClipboardCheck },
        { path: '/batch/full', label: 'Batch Full', icon: PlayCircle },
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col overflow-y-auto">
        <div className="p-6 sticky top-0 bg-gray-800 z-10">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            SophGenV3
          </h1>
        </div>
        
        <nav className="flex-1 px-4 space-y-8 pb-8">
          {navSections.map((section, idx) => (
            <div key={idx}>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-4">
                {section.title}
              </h3>
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-all duration-200 ${
                        isActive
                          ? 'bg-blue-900 text-blue-400 border border-blue-500 shadow-lg shadow-blue-900/20'
                          : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                      }`}
                    >
                      <Icon size={18} />
                      <span className="font-medium text-sm">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
