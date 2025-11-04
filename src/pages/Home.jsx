import React from 'react';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div className="text-center">
      <h1 className="text-4xl font-bold mb-4">Welcome to WeightGame</h1>
      <p className="mb-6 text-gray-600 max-w-xl mx-auto">
        This project helps users stay consistent with healthy habits through gamified daily
        challenges, progress tracking, and motivation features.
      </p>
      <Link
        to="/features"
        className="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
      >
        Explore Features
      </Link>
    </div>
  );
}
