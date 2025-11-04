import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="text-center py-12">
      <h2 className="text-4xl font-bold mb-4">404 — Page Not Found</h2>
      <p className="mb-4 text-gray-600">Oops! Looks like that page doesn’t exist.</p>
      <Link
        to="/"
        className="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
      >
        Go Home
      </Link>
    </div>
  );
}
