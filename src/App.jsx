import React from 'react';
import { Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Home from './pages/Home';
import Settings from './pages/Settings';
import Dashboard from './pages/Dashboard';
import Tasks from './pages/Tasks';
import MyAvatar from './pages/MyAvatar';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900">
      <NavBar />
      <main className="flex-grow max-w-5xl mx-auto p-6 w-full">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/myavatar" element={<MyAvatar />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="bg-white border-t mt-6 p-4 text-center text-sm text-gray-500">
        © {new Date().getFullYear()} WeightGame — Team Project Base
      </footer>
    </div>
  );
}
