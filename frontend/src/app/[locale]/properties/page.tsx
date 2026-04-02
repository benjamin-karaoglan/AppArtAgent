"use client";

import { useState, useEffect } from 'react';
import { useRouter } from '@/i18n/navigation';
import { useTranslations } from 'next-intl';
import ProtectedRoute from '@/components/ProtectedRoute';
import Header from '@/components/Header';
import { api } from '@/lib/api';
import { Plus, Home, Trash2, FileText, Sparkles, TrendingUp, ArrowRight } from 'lucide-react';
import Spinner from '@/components/ui/Spinner';
import type { Property } from '@/types';

function PropertiesContent() {
  const t = useTranslations('properties');
  const tc = useTranslations('common');
  const router = useRouter();
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletePropertyId, setDeletePropertyId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadProperties();
  }, []);

  const loadProperties = async () => {
    try {
      const response = await api.get('/api/properties/');
      setProperties(response.data);
    } catch (error) {
      console.error('Failed to load properties:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, propertyId: number) => {
    e.stopPropagation();
    setDeletePropertyId(propertyId);
  };

  const confirmDelete = async () => {
    if (!deletePropertyId) return;

    setDeleting(true);
    try {
      await api.delete(`/api/properties/${deletePropertyId}`);
      await loadProperties();
      setDeletePropertyId(null);
    } catch (error) {
      console.error('Failed to delete property:', error);
      alert(t('deleteFailed'));
    } finally {
      setDeleting(false);
    }
  };

  const cancelDelete = () => {
    if (!deleting) {
      setDeletePropertyId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Header Section */}
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {t('title')}
              </h1>
              <p className="mt-2 text-sm text-gray-600">
                {t('subtitle')}
              </p>
            </div>
            <button
              onClick={() => router.push('/properties/new')}
              className="inline-flex items-center justify-center min-w-[10rem] px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <Plus className="h-5 w-5 mr-2" />
              {t('addProperty')}
            </button>
          </div>

          {/* Properties Grid */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              {loading ? (
                <div className="text-center py-12">
                  <Spinner size={32} className="inline-block text-primary-600" />
                  <p className="mt-2 text-sm text-gray-500">{t('loading')}</p>
                </div>
              ) : properties.length === 0 ? (
                <div className="py-8 px-4">
                  <div className="text-center mb-8">
                    <Home className="mx-auto h-12 w-12 text-primary-400 mb-3" />
                    <h3 className="text-lg font-semibold text-gray-900">{t('empty.title')}</h3>
                    <p className="mt-1 text-sm text-gray-500">{t('empty.subtitle')}</p>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto mb-8">
                    {[
                      { icon: <FileText className="h-5 w-5" />, text: t('empty.feature1') },
                      { icon: <Sparkles className="h-5 w-5" />, text: t('empty.feature2') },
                      { icon: <TrendingUp className="h-5 w-5" />, text: t('empty.feature3') },
                    ].map((feature, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
                        <span className="text-primary-500">{feature.icon}</span>
                        {feature.text}
                      </div>
                    ))}
                  </div>
                  <div className="text-center">
                    <button
                      onClick={() => router.push('/properties/new')}
                      className="inline-flex items-center px-6 py-3 border border-transparent shadow-sm text-base font-medium rounded-lg text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                    >
                      <Plus className="h-5 w-5 mr-2" />
                      {t('addProperty')}
                      <ArrowRight className="h-5 w-5 ml-2" />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {properties.map((property) => (
                    <div
                      key={property.id}
                      onClick={() => router.push(`/properties/${property.id}`)}
                      className="relative border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                    >
                      <button
                        onClick={(e) => handleDeleteClick(e, property.id)}
                        className="absolute top-2 right-2 p-2 text-gray-400 hover:text-danger-600 hover:bg-danger-50 rounded-md transition-colors"
                        title={tc('delete')}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                      <h4 className="text-lg font-medium text-gray-900 mb-2 pr-8">
                        {property.address}
                      </h4>
                      <p className="text-sm text-gray-500 mb-2">
                        {property.city} {property.postal_code}
                      </p>
                      {property.asking_price && (
                        <p className="text-lg font-semibold text-primary-600">
                          {new Intl.NumberFormat('fr-FR', {
                            style: 'currency',
                            currency: 'EUR',
                          }).format(property.asking_price)}
                        </p>
                      )}
                      <div className="mt-3 flex items-center text-sm text-gray-500">
                        {property.surface_area && (
                          <span>{property.surface_area}m²</span>
                        )}
                        {property.rooms && (
                          <span className="ml-3">{tc('rooms', { count: property.rooms })}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Delete Confirmation Modal */}
          {deletePropertyId && (
            <div className="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
              <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                {/* Background overlay */}
                <div
                  className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
                  aria-hidden="true"
                  onClick={cancelDelete}
                ></div>

                {/* Center modal */}
                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                {/* Modal panel */}
                <div className="relative inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
                  <div className="sm:flex sm:items-start">
                    <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-danger-100 sm:mx-0 sm:h-10 sm:w-10">
                      <Trash2 className="h-6 w-6 text-danger-600" aria-hidden="true" />
                    </div>
                    <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                      <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                        {t('deleteTitle')}
                      </h3>
                      <div className="mt-2">
                        <p className="text-sm text-gray-500">
                          {t('deleteMessage')}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                    <button
                      type="button"
                      disabled={deleting}
                      onClick={confirmDelete}
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-danger-600 text-base font-medium text-white hover:bg-danger-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-danger-500 sm:ml-3 sm:w-auto sm:min-w-[6.5rem] sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {deleting ? tc('deleting') : tc('delete')}
                    </button>
                    <button
                      type="button"
                      disabled={deleting}
                      onClick={cancelDelete}
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:w-auto sm:min-w-[6.5rem] sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {tc('cancel')}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function PropertiesPage() {
  return (
    <ProtectedRoute>
      <PropertiesContent />
    </ProtectedRoute>
  );
}
