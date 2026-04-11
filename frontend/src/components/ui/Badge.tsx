import React from 'react';

type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'accent' | 'neutral';
type BadgeSize = 'sm' | 'md';

interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  success: 'bg-success-50 text-success-700',
  warning: 'bg-warning-50 text-warning-700 border border-warning-200',
  danger: 'bg-danger-50 text-danger-700',
  info: 'bg-primary-50 text-primary-700',
  accent: 'bg-accent-50 text-accent-700',
  neutral: 'bg-gray-100 text-gray-700',
};

const sizeClasses: Record<BadgeSize, string> = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
};

export default function Badge({
  variant = 'neutral',
  size = 'sm',
  icon,
  children,
  className = '',
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {icon && <span className="mr-1 flex-shrink-0">{icon}</span>}
      {children}
    </span>
  );
}
