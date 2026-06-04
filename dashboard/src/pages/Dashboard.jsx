import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function Dashboard() {
  const [stats, setStats] = useState({
    original_tokens: 0,
    optimized_tokens: 0,
    total_saved_tokens: 0,
    money_saved: 0.0,
    requests_processed: 0,
    recent_history: []
  });
  
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [chartData, setChartData] = useState([]);
  
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  useEffect(() => {
    let timeoutId;
    let isSubscribed = true;
    
    const fetchStats = async () => {
      if (!isSubscribed) return;
      
      let nextInterval = 2000;
      
      try {
        const response = await fetch('/api/stats');
        
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        
        const data = await response.json();
        setStats(data);
        setIsBackendOnline(true);
        
        setChartData([
          {
            name: 'Cumulative Token Volume',
            original: data.original_tokens,
            optimized: data.optimized_tokens
          }
        ]);
        
      } catch (error) {
        setIsBackendOnline(false);
        nextInterval = 5000;
      }
      
      if (isSubscribed) {
        timeoutId = setTimeout(fetchStats, nextInterval);
      }
    };

    fetchStats();
    
    return () => {
      isSubscribed = false;
      clearTimeout(timeoutId);
    };
  }, []);

  return (
    <div className="space-y-6 relative transition-colors duration-200">
      
      {/* Header with Dark Mode Toggle */}
      <div className="flex justify-between items-center mb-8 bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-slate-800">
        <h1 className="text-2xl font-bold text-blue-600 dark:text-blue-400">🛡️ ContextShield</h1>
        
        <div className="flex items-center space-x-6">
          {/* Connection Status */}
          {!isBackendOnline ? (
            <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs font-bold px-3 py-1.5 rounded-full shadow-sm border border-red-200 dark:border-red-800 animate-pulse flex items-center space-x-2">
              <span className="w-2 h-2 bg-red-500 rounded-full"></span>
              <span>⚠️ Proxy Backend Offline</span>
            </div>
          ) : (
            <div className="bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-bold px-3 py-1.5 rounded-full shadow-sm border border-green-200 dark:border-green-800 flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span>Proxy Live</span>
            </div>
          )}

          {/* Dark Mode Toggle */}
          <button 
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="p-2 rounded-lg bg-gray-100 dark:bg-slate-800 text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors shadow-sm"
          >
            {isDarkMode ? '☀️ Light' : '🌙 Dark'}
          </button>
        </div>
      </div>

      {/* Key Metric Dashboards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="p-6 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-gray-100 dark:border-slate-800 hover:shadow-md transition-shadow">
          <h2 className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-2">Original Context Tokens</h2>
          <p className="text-4xl font-black text-gray-800 dark:text-white">{stats.original_tokens.toLocaleString()}</p>
        </div>
        
        <div className="p-6 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-gray-100 dark:border-slate-800 hover:shadow-md transition-shadow">
          <h2 className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-2">Optimized Transmitted</h2>
          <p className="text-4xl font-black text-blue-600 dark:text-blue-400">{stats.optimized_tokens.toLocaleString()}</p>
        </div>
        
        <div className="p-6 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-green-50 dark:border-green-900/50 hover:shadow-md transition-shadow">
          <h2 className="text-xs font-bold text-green-500 dark:text-green-400 uppercase tracking-wider mb-2">Direct Financial Savings</h2>
          <p className="text-4xl font-black text-green-600 dark:text-green-400">${stats.money_saved.toFixed(4)}</p>
        </div>
      </div>
      
      {/* Interactive Data Visualization */}
      <div className="p-6 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-gray-100 dark:border-slate-800 h-[400px]">
        <h2 className="text-lg font-bold text-gray-800 dark:text-white mb-6">Total Intercepted vs Optimized Context Volume</h2>
        <ResponsiveContainer width="100%" height="90%">
          <BarChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 5 }} barSize={100}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={isDarkMode ? '#334155' : '#e5e7eb'} />
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#6b7280', fontWeight: 500}} />
            <YAxis axisLine={false} tickLine={false} tick={{fill: '#6b7280'}} tickFormatter={(value) => value.toLocaleString()} />
            <Tooltip 
              formatter={(value) => [value.toLocaleString() + " tokens", ""]} 
              cursor={{fill: isDarkMode ? '#1e293b' : '#f3f4f6'}}
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', backgroundColor: isDarkMode ? '#0f172a' : 'white', color: isDarkMode ? 'white' : 'black' }}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            <Bar dataKey="original" fill="#94a3b8" name="Original Bloated Context" radius={[4, 4, 0, 0]} />
            <Bar dataKey="optimized" fill="#22c55e" name="Lean Optimized Payload" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* NEW FEATURE: Recent Activity Log */}
      <div className="p-6 bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-gray-100 dark:border-slate-800 overflow-hidden">
        <h2 className="text-lg font-bold text-gray-800 dark:text-white mb-4">Live Intercept Log</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-500 dark:text-slate-400 uppercase bg-gray-50 dark:bg-slate-800/50">
              <tr>
                <th className="px-6 py-3 rounded-tl-lg">Request ID</th>
                <th className="px-6 py-3">Timestamp</th>
                <th className="px-6 py-3">Original Chars</th>
                <th className="px-6 py-3">Optimized Chars</th>
                <th className="px-6 py-3 rounded-tr-lg">Reduction</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_history && stats.recent_history.length > 0 ? (
                stats.recent_history.map((log) => (
                  <tr key={log.id} className="border-b dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900 dark:text-gray-300">#{log.id}</td>
                    <td className="px-6 py-4 text-gray-500 dark:text-slate-400">{log.time}</td>
                    <td className="px-6 py-4 text-gray-500 dark:text-slate-400">{log.original.toLocaleString()}</td>
                    <td className="px-6 py-4 text-blue-600 dark:text-blue-400 font-semibold">{log.optimized.toLocaleString()}</td>
                    <td className="px-6 py-4">
                      {log.saved_pct > 0 ? (
                        <span className="bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 text-xs font-semibold px-2.5 py-0.5 rounded border border-green-200 dark:border-green-800">
                          -{log.saved_pct}%
                        </span>
                      ) : (
                        <span className="text-gray-400 dark:text-slate-500">0%</span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-gray-400 dark:text-slate-500 italic">
                    No requests intercepted yet. Fire a prompt from your IDE!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Bottom Telemetry Footer */}
      <div className="text-sm flex justify-between px-2 pt-2 border-t border-gray-100 dark:border-slate-800 mt-4">
        <p className="text-gray-500 dark:text-slate-400">Total Requests Intercepted: <span className="font-semibold text-gray-800 dark:text-white">{stats.requests_processed.toLocaleString()}</span></p>
        <p className="text-gray-500 dark:text-slate-400">Total Waste Tokens Eradicated: <span className="font-semibold text-purple-600 dark:text-purple-400">{stats.total_saved_tokens.toLocaleString()}</span></p>
      </div>
      
    </div>
  );
}
