"use client";

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Header from '@/components/Header';
import { api } from '@/lib/api';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

interface PropertyFormData {
  address: string;
  postal_code?: string;
  city?: string;
  department?: string;
  asking_price?: number;
  surface_area?: number;
  rooms?: number;
  property_type?: string;
  floor?: number;
  building_year?: number;
}

function NewPropertyContent() {
  const router = useRouter();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PropertyFormData>();

  const onSubmit = async (data: PropertyFormData) => {
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/api/properties/', data);
      const property = response.data;

      // Redirect to the property detail page
      router.push(`/properties/${property.id}`);
    } catch (err: any) {
      console.error('Property creation error:', err);
      setError(err.response?.data?.detail || 'Failed to create property. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-3xl mx-auto py-6 sm:px-6 lg:px-8">
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
            <h1 className="text-3xl font-bold text-gray-900">Add New Property</h1>
            <p className="mt-2 text-sm text-gray-600">
              Enter the property details to start your analysis
            </p>
          </div>

          {/* Form */}
          <div className="bg-white shadow rounded-lg">
            <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              {/* Address Section */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Property Location
                </h3>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="address" className="block text-sm font-medium text-gray-700">
                      Address <span className="text-red-500">*</span>
                    </label>
                    <input
                      id="address"
                      type="text"
                      {...register('address', {
                        required: 'Address is required',
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="123 rue de la Paix"
                    />
                    {errors.address && (
                      <p className="mt-1 text-sm text-red-600">{errors.address.message}</p>
                    )}
                  </div>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    <div>
                      <label htmlFor="postal_code" className="block text-sm font-medium text-gray-700">
                        Postal Code
                      </label>
                      <input
                        id="postal_code"
                        type="text"
                        {...register('postal_code')}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="75001"
                      />
                    </div>

                    <div>
                      <label htmlFor="city" className="block text-sm font-medium text-gray-700">
                        City
                      </label>
                      <input
                        id="city"
                        type="text"
                        {...register('city')}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="Paris"
                      />
                    </div>

                    <div>
                      <label htmlFor="department" className="block text-sm font-medium text-gray-700">
                        Department
                      </label>
                      <input
                        id="department"
                        type="text"
                        {...register('department')}
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        placeholder="75"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Property Details Section */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Property Details
                </h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label htmlFor="property_type" className="block text-sm font-medium text-gray-700">
                      Property Type
                    </label>
                    <select
                      id="property_type"
                      {...register('property_type')}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-gray-900 bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value="">Select type</option>
                      <option value="Appartement">Appartement</option>
                      <option value="Maison">Maison</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="asking_price" className="block text-sm font-medium text-gray-700">
                      Asking Price (€)
                    </label>
                    <input
                      id="asking_price"
                      type="number"
                      {...register('asking_price', {
                        valueAsNumber: true,
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="250000"
                    />
                  </div>

                  <div>
                    <label htmlFor="surface_area" className="block text-sm font-medium text-gray-700">
                      Surface Area (m²)
                    </label>
                    <input
                      id="surface_area"
                      type="number"
                      step="0.01"
                      {...register('surface_area', {
                        valueAsNumber: true,
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="65"
                    />
                  </div>

                  <div>
                    <label htmlFor="rooms" className="block text-sm font-medium text-gray-700">
                      Number of Rooms
                    </label>
                    <input
                      id="rooms"
                      type="number"
                      {...register('rooms', {
                        valueAsNumber: true,
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="3"
                    />
                  </div>

                  <div>
                    <label htmlFor="floor" className="block text-sm font-medium text-gray-700">
                      Floor
                    </label>
                    <input
                      id="floor"
                      type="number"
                      {...register('floor', {
                        valueAsNumber: true,
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="2"
                    />
                  </div>

                  <div>
                    <label htmlFor="building_year" className="block text-sm font-medium text-gray-700">
                      Building Year
                    </label>
                    <input
                      id="building_year"
                      type="number"
                      {...register('building_year', {
                        valueAsNumber: true,
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 text-gray-900 bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="1990"
                    />
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => router.push('/dashboard')}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Creating...' : 'Create Property'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function NewPropertyPage() {
  return (
    <ProtectedRoute>
      <NewPropertyContent />
    </ProtectedRoute>
  );
}
