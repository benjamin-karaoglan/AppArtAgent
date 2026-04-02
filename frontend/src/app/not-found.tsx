import Link from 'next/link'
import { SearchX } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <SearchX className="w-16 h-16 text-gray-400 mx-auto mb-6" />
        <h1 className="text-4xl font-bold text-gray-900 mb-2">404</h1>
        <p className="text-lg text-gray-600 mb-8">
          This page doesn&apos;t exist or has been moved.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/"
            className="px-6 py-2.5 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
          >
            Go Home
          </Link>
        </div>
      </div>
    </div>
  )
}
