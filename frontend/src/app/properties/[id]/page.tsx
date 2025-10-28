"use client";

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Header from '@/components/Header';
import { api } from '@/lib/api';
import { ArrowLeft, TrendingUp, FileText, Upload, Loader2 } from 'lucide-react';
import Link from 'next/link';
import type { Property } from '@/types';

function PropertyDetailContent() {
  const params = useParams();
  const router = useRouter();
  const propertyId = params.id as string;

  const [property, setProperty] = useState<Property | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [priceAnalysis, setPriceAnalysis] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    loadProperty();
  }, [propertyId]);

  const loadProperty = async () => {
    try {
      const response = await api.get(`/api/properties/${propertyId}`);
      setProperty(response.data);
    } catch (error) {
      console.error('Failed to load property:', error);
      setError('Failed to load property details');
    } finally {
      setLoading(false);
    }
  };

  const analyzePrice = async () => {
    setAnalyzing(true);
    setError('');

    try {
      const response = await api.post(`/api/properties/${propertyId}/analyze-price`);
      setPriceAnalysis(response.data);

      // Reload property to get updated values
      await loadProperty();
    } catch (err: any) {
      console.error('Price analysis error:', err);
      setError(err.response?.data?.detail || 'Failed to analyze price');
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      </div>
    );
  }

  if (!property) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-7xl mx-auto py-6 px-4">
          <p className="text-red-600">Property not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Back button */}
          <Link
            href="/dashboard"
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-6"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Link>

          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">{property.address}</h1>
            <p className="mt-2 text-sm text-gray-600">
              {property.city} {property.postal_code}
            </p>
          </div>

          {error && (
            <div className="mb-6 rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Property Details Grid */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-8">
            {/* Property Info Card */}
            <div className="bg-white shadow rounded-lg p-6 lg:col-span-2">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Property Information</h2>
              <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                {property.property_type && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Type</dt>
                    <dd className="mt-1 text-sm text-gray-900">{property.property_type}</dd>
                  </div>
                )}
                {property.asking_price && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Asking Price</dt>
                    <dd className="mt-1 text-sm text-gray-900 font-semibold">
                      {new Intl.NumberFormat('fr-FR', {
                        style: 'currency',
                        currency: 'EUR',
                      }).format(property.asking_price)}
                    </dd>
                  </div>
                )}
                {property.surface_area && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Surface Area</dt>
                    <dd className="mt-1 text-sm text-gray-900">{property.surface_area} m²</dd>
                  </div>
                )}
                {property.rooms && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Rooms</dt>
                    <dd className="mt-1 text-sm text-gray-900">{property.rooms} pièces</dd>
                  </div>
                )}
                {property.floor !== null && property.floor !== undefined && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Floor</dt>
                    <dd className="mt-1 text-sm text-gray-900">{property.floor}</dd>
                  </div>
                )}
                {property.building_year && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Building Year</dt>
                    <dd className="mt-1 text-sm text-gray-900">{property.building_year}</dd>
                  </div>
                )}
                {property.price_per_sqm && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Price per m²</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {new Intl.NumberFormat('fr-FR', {
                        style: 'currency',
                        currency: 'EUR',
                      }).format(property.price_per_sqm)}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Quick Actions Card */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
              <div className="space-y-3">
                <button
                  onClick={analyzePrice}
                  disabled={analyzing || !property.asking_price || !property.surface_area}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {analyzing ? (
                    <>
                      <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <TrendingUp className="h-5 w-5 mr-2" />
                      Analyze Price
                    </>
                  )}
                </button>

                <button
                  onClick={() => router.push(`/properties/${propertyId}/documents`)}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <FileText className="h-5 w-5 mr-2" />
                  Manage Documents
                </button>

                <button
                  onClick={() => router.push(`/properties/${propertyId}/photos`)}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <Upload className="h-5 w-5 mr-2" />
                  Upload Photos
                </button>
              </div>
            </div>
          </div>

          {/* Price Analysis Results */}
          {(priceAnalysis || property.estimated_value) && (
            <div className="bg-white shadow rounded-lg p-6 mb-8">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Price Analysis</h2>

              <div className="grid grid-cols-1 gap-6 sm:grid-cols-3 mb-6">
                {property.estimated_value && (
                  <div className="border-l-4 border-blue-500 pl-4">
                    <dt className="text-sm font-medium text-gray-500">Estimated Value</dt>
                    <dd className="mt-1 text-2xl font-semibold text-gray-900">
                      {new Intl.NumberFormat('fr-FR', {
                        style: 'currency',
                        currency: 'EUR',
                      }).format(property.estimated_value)}
                    </dd>
                  </div>
                )}

                {priceAnalysis?.price_deviation_percent !== undefined && (
                  <div className="border-l-4 border-yellow-500 pl-4">
                    <dt className="text-sm font-medium text-gray-500">Price Deviation</dt>
                    <dd className={`mt-1 text-2xl font-semibold ${
                      priceAnalysis.price_deviation_percent > 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {priceAnalysis.price_deviation_percent > 0 ? '+' : ''}
                      {priceAnalysis.price_deviation_percent.toFixed(1)}%
                    </dd>
                  </div>
                )}

                {priceAnalysis?.comparable_sales && (
                  <div className="border-l-4 border-green-500 pl-4">
                    <dt className="text-sm font-medium text-gray-500">Comparable Sales</dt>
                    <dd className="mt-1 text-2xl font-semibold text-gray-900">
                      {priceAnalysis.comparable_sales.length}
                    </dd>
                  </div>
                )}
              </div>

              {property.recommendation && (
                <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                  <p className="text-sm text-blue-800">
                    <span className="font-medium">Recommendation:</span> {property.recommendation}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function PropertyDetailPage() {
  return (
    <ProtectedRoute>
      <PropertyDetailContent />
    </ProtectedRoute>
  );
}
