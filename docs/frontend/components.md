# Components

Reusable React components used throughout the Appartment Agent frontend.

## Component Overview

| Component | Purpose |
|-----------|---------|
| `Header` | Navigation header |
| `InfoTooltip` | Informational tooltips |
| `MarketTrendChart` | Price trend visualization |
| `ProtectedRoute` | Route authentication guard |
| `Providers` | Context providers wrapper |

## Header

**File**: `src/components/Header.tsx`

Main navigation header with user menu.

```tsx
import { Header } from '@/components/Header';

// Usage
<Header />
```

### Features

- Logo and brand name
- Navigation links
- User authentication state
- Logout button

### Implementation

```tsx
"use client";

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white shadow">
      <nav className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link href="/" className="text-xl font-bold text-indigo-600">
          Appartment Agent
        </Link>
        
        {user ? (
          <div className="flex items-center gap-4">
            <Link href="/dashboard">Dashboard</Link>
            <span className="text-gray-600">{user.email}</span>
            <button onClick={logout} className="text-red-600">
              Logout
            </button>
          </div>
        ) : (
          <div className="flex gap-4">
            <Link href="/auth/login">Login</Link>
            <Link href="/auth/register" className="bg-indigo-600 text-white px-4 py-2 rounded">
              Get Started
            </Link>
          </div>
        )}
      </nav>
    </header>
  );
}
```

## InfoTooltip

**File**: `src/components/InfoTooltip.tsx`

Informational tooltips for explaining features.

```tsx
import { InfoTooltip } from '@/components/InfoTooltip';

// Usage
<InfoTooltip title="Simple Analysis">
  Historical sales at this exact address from DVF data.
</InfoTooltip>
```

### Props

| Prop | Type | Description |
|------|------|-------------|
| `title` | string | Tooltip title |
| `children` | ReactNode | Tooltip content |
| `position` | 'top' \| 'bottom' \| 'left' \| 'right' | Tooltip position |

### Implementation

```tsx
"use client";

import { useState } from 'react';

interface InfoTooltipProps {
  title: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function InfoTooltip({ 
  title, 
  children, 
  position = 'top' 
}: InfoTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        className="text-gray-400 hover:text-gray-600"
        aria-label="More information"
      >
        <InfoIcon className="w-4 h-4" />
      </button>
      
      {isOpen && (
        <div className={`absolute z-10 p-3 bg-white rounded-lg shadow-lg border
          ${position === 'top' ? 'bottom-full mb-2' : ''}
          ${position === 'bottom' ? 'top-full mt-2' : ''}
        `}>
          <h4 className="font-semibold text-gray-900">{title}</h4>
          <div className="text-sm text-gray-600 mt-1">
            {children}
          </div>
        </div>
      )}
    </div>
  );
}
```

## MarketTrendChart

**File**: `src/components/MarketTrendChart.tsx`

Interactive chart showing 5-year price trends.

```tsx
import { MarketTrendChart } from '@/components/MarketTrendChart';

// Usage
<MarketTrendChart 
  data={trendData}
  postalCode="75006"
/>
```

### Props

| Prop | Type | Description |
|------|------|-------------|
| `data` | TrendData[] | Price trend data points |
| `postalCode` | string | Area code for label |
| `height` | number | Chart height in pixels |

### Data Format

```tsx
interface TrendData {
  year: number;
  avg_price_per_sqm: number;
  transactions: number;
  yoy_change?: number;
}
```

### Features

- Line chart with price per m²
- Year-over-year percentage change
- Hover tooltips with details
- Responsive sizing

## ProtectedRoute

**File**: `src/components/ProtectedRoute.tsx`

Authentication guard for protected pages.

```tsx
import { ProtectedRoute } from '@/components/ProtectedRoute';

// Usage in layout
<ProtectedRoute>
  {children}
</ProtectedRoute>
```

### Behavior

1. Check authentication state
2. Show loading spinner while checking
3. Redirect to login if not authenticated
4. Render children if authenticated

## Providers

**File**: `src/components/Providers.tsx`

Wraps the application with necessary context providers.

```tsx
import { Providers } from '@/components/Providers';

// Usage in root layout
<Providers>
  {children}
</Providers>
```

### Included Providers

```tsx
"use client";

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      retry: 1,
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        {children}
      </AuthProvider>
    </QueryClientProvider>
  );
}
```

## Common Patterns

### Form Components

```tsx
// Reusable input component
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function Input({ label, error, ...props }: InputProps) {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        className={`w-full px-3 py-2 border rounded-md
          ${error ? 'border-red-500' : 'border-gray-300'}
          focus:outline-none focus:ring-2 focus:ring-indigo-500
        `}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-500">{error}</p>
      )}
    </div>
  );
}
```

### Loading States

```tsx
// Skeleton loader
export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
  );
}

// Usage
<Skeleton className="h-8 w-1/4 mb-4" />
```

### Error Display

```tsx
// Error message component
interface ErrorMessageProps {
  title: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ title, message, onRetry }: ErrorMessageProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <h3 className="text-red-800 font-semibold">{title}</h3>
      <p className="text-red-600 mt-1">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 text-red-700 underline hover:no-underline"
        >
          Try again
        </button>
      )}
    </div>
  );
}
```

### Button Variants

```tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
}

export function Button({ 
  variant = 'primary', 
  loading,
  children,
  ...props 
}: ButtonProps) {
  const variants = {
    primary: 'bg-indigo-600 text-white hover:bg-indigo-700',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  };

  return (
    <button
      className={`px-4 py-2 rounded-md font-medium transition-colors
        ${variants[variant]}
        ${loading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      disabled={loading}
      {...props}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <Spinner className="w-4 h-4" />
          Loading...
        </span>
      ) : (
        children
      )}
    </button>
  );
}
```

## Styling Guidelines

### Tailwind Classes

- Use semantic color names (`indigo-600` for primary)
- Maintain consistent spacing (`p-4`, `gap-4`)
- Use responsive prefixes when needed (`md:flex`)

### Dark Mode (Future)

Components should support dark mode:

```tsx
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
  ...
</div>
```
