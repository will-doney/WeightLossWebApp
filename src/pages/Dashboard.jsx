import React from 'react';

export default function Dashboard() {
  return (
    <div>
      <h2 className="text-3xl font-bold mb-4">Progress Dashboard</h2>
      <p className="mb-4">This is a placeholder dashboard for showing user progress.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 bg-white rounded shadow-sm">Graph placeholder</div>
        <div className="p-4 bg-white rounded shadow-sm">Badges placeholder</div>
      </div>
    </div>
  );
}
