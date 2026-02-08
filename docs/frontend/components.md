# Components

Reusable React components used throughout the AppArt Agent frontend.

## Design System Components (`src/components/ui/`)

Shared UI primitives that enforce consistent styling across all pages. Import from the barrel export:

```tsx
import { Button, Badge, Card, SectionHeader, StatCard } from '@/components/ui';
```

### Button

**File**: `src/components/ui/Button.tsx`

Standardized button with variant-based styling.

```tsx
<Button variant="primary" icon={<Plus className="h-5 w-5" />}>Add Property</Button>
<Button variant="secondary">Cancel</Button>
<Button variant="accent">Open Studio</Button>
<Button variant="ghost">Show More</Button>
<Button variant="danger">Delete</Button>
<Button variant="link">Learn More</Button>
<Button variant="primary" size="sm">Small</Button>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'primary' \| 'secondary' \| 'accent' \| 'ghost' \| 'danger' \| 'link'` | `'primary'` | Visual style |
| `size` | `'sm' \| 'md'` | `'md'` | Button size |
| `icon` | `ReactNode` | — | Icon rendered before children |
| `disabled` | `boolean` | `false` | Disabled state |

#### Variant Colors

| Variant | Background | Text | Ring |
|---------|-----------|------|------|
| `primary` | `primary-600` | white | `primary-500` |
| `secondary` | white (border `gray-300`) | `gray-700` | `primary-500` |
| `accent` | `accent-600` | white | `accent-500` |
| `ghost` | transparent → `primary-50` | `primary-600` | `primary-500` |
| `danger` | white (border `danger-300`) | `danger-700` | `danger-500` |
| `link` | transparent | `primary-600` | none |

### Badge

**File**: `src/components/ui/Badge.tsx`

Status indicators and labels.

```tsx
<Badge variant="success">LOW</Badge>
<Badge variant="warning">MEDIUM</Badge>
<Badge variant="danger">HIGH</Badge>
<Badge variant="info">3 documents</Badge>
<Badge variant="accent">AI Generated</Badge>
<Badge variant="neutral">Draft</Badge>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'success' \| 'warning' \| 'danger' \| 'info' \| 'accent' \| 'neutral'` | `'neutral'` | Visual style |
| `size` | `'sm' \| 'md'` | `'md'` | Badge size |

### Card

**File**: `src/components/ui/Card.tsx`

Consistent card wrapper.

```tsx
<Card>Default padding (p-6)</Card>
<Card padding="sm">Small padding (p-4)</Card>
<Card padding="none">No padding</Card>
```

### SectionHeader

**File**: `src/components/ui/SectionHeader.tsx`

Section title with icon and optional action button, used in property detail sections.

```tsx
<SectionHeader
  icon={<Sparkles className="h-5 w-5" />}
  title="AI Property Analysis"
  action={<Button variant="secondary" size="sm">Manage Documents</Button>}
/>
```

### StatCard

**File**: `src/components/ui/StatCard.tsx`

Dashboard statistics card with icon.

```tsx
<StatCard icon={<Home className="h-5 w-5" />} label="Total Properties" value={12} />
```

## Application Components

### Header

**File**: `src/components/Header.tsx`

Main navigation header with locale switcher.

- Logo and brand name
- Navigation links (Dashboard, Properties)
- Language toggle (FR/EN)
- User name and logout button
- Uses `primary-600` for brand color, `gray-300` borders for buttons

### InfoTooltip

**File**: `src/components/InfoTooltip.tsx`

Click-activated informational tooltip for explaining features.

```tsx
<InfoTooltip title="Simple Analysis" content={<p>Historical sales data...</p>} />
```

### MarketTrendChart

**File**: `src/components/MarketTrendChart.tsx`

SVG chart showing price trends over time with bar chart and trend line.

- Bars colored with `success-*` (positive) and `danger-*` (negative) tokens
- Trend line uses `primary-*`
- Legend with `success-50`, `danger-50`, `primary-50` backgrounds

### ProtectedRoute

**File**: `src/components/ProtectedRoute.tsx`

Authentication guard — redirects to login if not authenticated.

### AppArtLogo

**File**: `src/components/AppArtLogo.tsx`

SVG logo component with configurable size and color.

## Color Token Reference

**All components use semantic color tokens.** Never use raw Tailwind colors (`blue-600`, `red-500`, etc.).

| Token | Palette | Usage |
|-------|---------|-------|
| `primary-*` | Blue (#2563eb) | Main CTAs, links, active states, focus rings |
| `accent-*` | Indigo (#4f46e5) | Secondary features: studio, photos, documents, AI |
| `success-*` | Emerald (#10b981) | Positive states, confirmations |
| `warning-*` | Amber (#f59e0b) | Warnings, outliers, caution states |
| `danger-*` | Red (#dc2626) | Errors, destructive actions, high risk |

Defined in `tailwind.config.js`. Utility CSS classes in `globals.css`.

## Common Patterns

### Loading States

```tsx
<Loader2 className="h-8 w-8 animate-spin text-primary-600" />
```

### Error Display

```tsx
<div className="rounded-md bg-danger-50 p-4">
  <p className="text-sm text-danger-700">{error}</p>
</div>
```

### Form Inputs

```tsx
<input className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-primary-500 focus:ring-1 focus:ring-primary-500" />
```
