import React from 'react';

interface SectionHeaderProps {
  title: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export default function SectionHeader({ title, icon, action, className = '' }: SectionHeaderProps) {
  return (
    <div className={`flex items-center justify-between mb-4 ${className}`}>
      <h2 className="text-lg font-semibold text-gray-900 flex items-center">
        {icon && <span className="mr-2 text-accent-600">{icon}</span>}
        {title}
      </h2>
      {action && <div>{action}</div>}
    </div>
  );
}
