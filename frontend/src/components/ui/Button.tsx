import React from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'accent' | 'ghost' | 'danger' | 'link';
type ButtonSize = 'sm' | 'md';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-primary-600 hover:bg-primary-700 text-white border border-transparent focus:ring-primary-500',
  secondary:
    'bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 focus:ring-primary-500',
  accent:
    'bg-accent-600 hover:bg-accent-700 text-white border border-transparent focus:ring-accent-500',
  ghost:
    'bg-transparent hover:bg-gray-100 text-gray-700 border border-transparent focus:ring-primary-500',
  danger:
    'bg-white hover:bg-danger-50 text-danger-700 border border-danger-300 focus:ring-danger-500',
  link:
    'bg-transparent hover:bg-transparent text-primary-600 hover:text-primary-700 border-none underline-offset-2 hover:underline focus:ring-primary-500 !px-0 !py-0',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'text-sm px-3 py-1.5',
  md: 'text-sm px-4 py-2',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  icon,
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="mr-2 flex-shrink-0">{icon}</span>}
      {children}
    </button>
  );
}
