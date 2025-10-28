"use client";

import ProtectedRoute from '@/components/ProtectedRoute';
import Header from '@/components/Header';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

function PhotosContent() {
  const params = useParams();
  const propertyId = params.id as string;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <Link
            href={`/properties/${propertyId}`}
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-6"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Property
          </Link>

          <div className="bg-white shadow rounded-lg p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Photo Upload & AI Analysis</h1>
            <p className="text-gray-600">
              Photo analysis feature coming soon! You'll be able to:
            </p>
            <ul className="mt-4 list-disc list-inside text-gray-600 space-y-2">
              <li>Upload apartment photos</li>
              <li>Get AI-powered style suggestions</li>
              <li>Visualize renovation potential</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function PhotosPage() {
  return (
    <ProtectedRoute>
      <PhotosContent />
    </ProtectedRoute>
  );
}
