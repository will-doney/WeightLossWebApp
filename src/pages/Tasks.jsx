import React from 'react';

export default function Tasks() {
  const tasks = [
    { id: 1, task: '10-minute walk' },
    { id: 2, task: 'Drink 2 liters of water' },
    { id: 3, task: 'Stretch for 5 minutes' },
  ];

  return (
    <div>
      <h2 className="text-3xl font-bold mb-4">Daily Tasks</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {tasks.map((c) => (
          <div key={c.id} className="bg-white p-4 rounded shadow-sm hover:shadow-md transition">
            <h3 className="font-semibold">{c.task}</h3>
            <p className="text-sm text-gray-500 mt-2">
              Teammate can add completion tracking, progress points, or streaks here.
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
