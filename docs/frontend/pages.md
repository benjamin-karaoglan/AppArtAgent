# Pages & Routes

AppArt Agent uses Next.js 14 App Router for file-based routing.

## Route Structure

```
/                           # Landing page
├── /auth
│   ├── /login              # Login form
│   └── /register           # Registration form
├── /dashboard              # Main dashboard (protected)
└── /properties
    ├── /new                # Create property (protected)
    └── /[id]               # Property detail (protected)
        ├── /documents      # Document management
        ├── /photos         # Photo management
        └── /redesign-studio # Photo redesign
```

## Pages

### Landing Page (`/`)

**File**: `src/app/page.tsx`

Public landing page with:

- Hero section
- Feature highlights
- Call-to-action buttons

### Authentication

#### Login (`/auth/login`)

**File**: `src/app/auth/login/page.tsx`

- Email/password form
- JWT token storage
- Redirect to dashboard on success

#### Register (`/auth/register`)

**File**: `src/app/auth/register/page.tsx`

- Registration form
- Email validation
- Auto-login after registration

### Dashboard (`/dashboard`)

**File**: `src/app/dashboard/page.tsx`

Protected route showing:

- Property list
- Quick stats
- Recent activity
- Create property button

### Properties

#### New Property (`/properties/new`)

**File**: `src/app/properties/new/page.tsx`

Property creation form:

- Address input
- Price and surface area
- Property type selection

#### Property Detail (`/properties/[id]`)

**File**: `src/app/properties/[id]/page.tsx`

Property overview with:

- Property information
- Price analysis results
- Market trend chart
- Document summary
- Navigation to sub-pages

```tsx
// Dynamic route parameter
export default function PropertyPage({ 
  params 
}: { 
  params: { id: string } 
}) {
  const propertyId = params.id;
  // ...
}
```

#### Documents (`/properties/[id]/documents`)

**File**: `src/app/properties/[id]/documents/page.tsx`

Document management:

- Bulk upload dropzone
- Document list with status
- Classification results
- Analysis viewer
- Synthesis summary

```tsx
// Document upload state
const [uploading, setUploading] = useState(false);
const [progress, setProgress] = useState<BulkUploadProgress | null>(null);

// Upload handler
const handleUpload = async (files: FileList) => {
  setUploading(true);
  const result = await api.bulkUpload(propertyId, files);
  pollStatus(result.workflow_id);
};
```

#### Photos (`/properties/[id]/photos`)

**File**: `src/app/properties/[id]/photos/page.tsx`

Photo management:

- Photo upload
- Gallery view
- Room type tagging
- Link to redesign studio

#### Redesign Studio (`/properties/[id]/redesign-studio`)

**File**: `src/app/properties/[id]/redesign-studio/page.tsx`

AI-powered photo redesign:

- Photo selection
- Style chooser
- Preference configuration
- Before/after comparison
- Redesign history

```tsx
// Redesign request
const requestRedesign = async (photoId: number, style: string) => {
  const result = await api.post(`/photos/${photoId}/redesign`, {
    style,
    preferences: selectedPreferences
  });
  setRedesignId(result.redesign_id);
  pollRedesignStatus(result.redesign_id);
};
```

## Protected Routes

Routes under `/dashboard` and `/properties` require authentication.

### ProtectedRoute Component

```tsx
// src/components/ProtectedRoute.tsx
"use client";

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
}
```

### Usage in Layout

```tsx
// src/app/dashboard/layout.tsx
import { ProtectedRoute } from '@/components/ProtectedRoute';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <Header />
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
    </ProtectedRoute>
  );
}
```

## Route Navigation

### Link Component

```tsx
import Link from 'next/link';

<Link 
  href={`/properties/${property.id}`}
  className="text-indigo-600 hover:text-indigo-800"
>
  View Property
</Link>
```

### Programmatic Navigation

```tsx
import { useRouter } from 'next/navigation';

const router = useRouter();

// Navigate
router.push('/dashboard');

// Replace (no history entry)
router.replace('/auth/login');

// Back
router.back();
```

## Loading States

Each route can have a `loading.tsx` file:

```tsx
// src/app/properties/[id]/loading.tsx
export default function Loading() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/4 mb-4" />
      <div className="h-64 bg-gray-200 rounded" />
    </div>
  );
}
```

## Error Handling

Each route can have an `error.tsx` file:

```tsx
// src/app/properties/[id]/error.tsx
"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="text-center py-8">
      <h2 className="text-xl font-semibold text-red-600">
        Something went wrong
      </h2>
      <p className="text-gray-600 mt-2">{error.message}</p>
      <button
        onClick={reset}
        className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded"
      >
        Try again
      </button>
    </div>
  );
}
```

## Metadata

Dynamic metadata for SEO:

```tsx
// src/app/properties/[id]/page.tsx
import { Metadata } from 'next';

export async function generateMetadata({ 
  params 
}: { 
  params: { id: string } 
}): Promise<Metadata> {
  const property = await fetchProperty(params.id);
  
  return {
    title: `${property.address} | AppArt Agent`,
    description: `Property analysis for ${property.address}, ${property.city}`,
  };
}
```
