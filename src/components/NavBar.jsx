import React from 'react';
import { NavLink } from 'react-router-dom';

export default function NavBar() {
  const links = [
    { to: '/', label: 'Home' },
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/tasks', label: 'Tasks' },
    { to: '/myavatar', label: 'Avatar' },
    { to: '/settings', label: 'Settings' },
  ];

  return (
    <header className="bg-white shadow-sm sticky top-0 z-10">
      <div className="max-w-5xl mx-auto flex justify-between items-center p-4">
        <h1 className="text-xl font-bold text-blue-600">WeightGame</h1>
        <nav className="flex gap-4">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `px-2 py-1 rounded hover:text-blue-600 ${
                  isActive ? 'text-blue-600 font-semibold' : 'text-gray-700'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
