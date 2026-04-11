import type { MetadataRoute } from 'next'

const BASE_URL = 'https://appartagent.com'

export default function sitemap(): MetadataRoute.Sitemap {
  const locales = ['fr', 'en']

  const publicPages = [
    { path: '', priority: 1.0, changeFrequency: 'weekly' as const },
    { path: '/auth/login', priority: 0.5, changeFrequency: 'yearly' as const },
    { path: '/auth/register', priority: 0.5, changeFrequency: 'yearly' as const },
    { path: '/legal/privacy', priority: 0.3, changeFrequency: 'yearly' as const },
    { path: '/legal/terms', priority: 0.3, changeFrequency: 'yearly' as const },
  ]

  return publicPages.flatMap((page) =>
    locales.map((locale) => ({
      url: `${BASE_URL}/${locale}${page.path}`,
      lastModified: new Date(),
      changeFrequency: page.changeFrequency,
      priority: page.priority,
      alternates: {
        languages: Object.fromEntries(
          locales.map((l) => [l, `${BASE_URL}/${l}${page.path}`])
        ),
      },
    }))
  )
}
