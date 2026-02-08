import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  className?: string;
}

export default function StatCard({ label, value, icon, className = '' }: StatCardProps) {
  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center">
        {icon && (
          <div className="flex-shrink-0 mr-4">
            <div className="h-10 w-10 rounded-lg bg-primary-50 flex items-center justify-center text-primary-600">
              {icon}
            </div>
          </div>
        )}
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}
