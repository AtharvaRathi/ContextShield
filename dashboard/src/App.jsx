import React from 'react';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-950 text-gray-900 dark:text-gray-100 transition-colors duration-200">
      <main className="p-4 md:p-8 max-w-7xl mx-auto">
        <Dashboard />
      </main>
    </div>
  );
}

export default App;
