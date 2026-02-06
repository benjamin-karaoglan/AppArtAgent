// Root layout - minimal, no <html> or <body> tags
// Those are handled by [locale]/layout.tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
