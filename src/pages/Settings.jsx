import React from 'react';

export default function Settings() {
  const settings = [
    'Notification Preferences',
    'Privacy Settings',
    'Account Management',
    'Theme Selection',
    'Data Export Options',
  ];

  return (
    <div>
      <h2 className="text-3xl font-bold mb-4">App Settings</h2>
      <ul className="list-disc pl-6 space-y-2 text-gray-700">
        {settings.map((setting, i) => (
          <li key={i}>{setting}</li>
        ))}
      </ul>
      <p className="mt-6 text-gray-500 text-sm">
      </p>
    </div>
  );
}
