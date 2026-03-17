"use client";

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { TrendingUp } from 'lucide-react';
import Spinner from '@/components/ui/Spinner';
import { Link } from '@/i18n/navigation';
import SectionHeader from '@/components/ui/SectionHeader';
import { api } from '@/lib/api';
import type { PriceAnalysisSummary as PriceAnalysisSummaryType } from '@/types';

interface PriceAnalysisSummaryProps {
  propertyId: string;
  hasRequiredFields: boolean;
}

export default function PriceAnalysisSummary({ propertyId, hasRequiredFields }: PriceAnalysisSummaryProps) {
  const t = useTranslations('property.priceAnalyst');
  const [data, setData] = useState<PriceAnalysisSummaryType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!hasRequiredFields) {
      setLoading(false);
      return;
    }
    loadSummary();
  }, [propertyId, hasRequiredFields]);

  const loadSummary = async () => {
    try {
      const response = await api.get(`/api/properties/${propertyId}/price-analysis`);
      setData(response.data);
    } catch (error) {
      console.error('Failed to load price analysis summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);

  return (
    <div className="bg-white shadow rounded-lg p-6 mb-8">
      <SectionHeader
        title={t('summary.title')}
        icon={<TrendingUp className="h-5 w-5" />}
        action={
          <Link
            href={`/properties/${propertyId}/price-analyst`}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-500 bg-white hover:border-primary-600 hover:text-primary-600 hover:bg-primary-50 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <TrendingUp className="h-4 w-4 mr-2" />
            {t('summary.viewFull')}
          </Link>
        }
      />

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Spinner size={24} className="text-primary-600" />
        </div>
      ) : !hasRequiredFields ? (
        <p className="text-sm text-gray-500 py-4">{t('summary.completeInfo')}</p>
      ) : !data?.estimated_value ? (
        <p className="text-sm text-gray-500 py-4">{t('summary.noData')}</p>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="border-l-4 border-primary-500 pl-4">
              <dt className="text-sm font-medium text-gray-500">{t('metrics.estimatedValue')}</dt>
              <dd className="mt-1 text-xl font-semibold text-gray-900">
                {formatCurrency(data.estimated_value)}
              </dd>
            </div>

            <div className="border-l-4 border-warning-500 pl-4">
              <dt className="text-sm font-medium text-gray-500">{t('metrics.deviation')}</dt>
              <dd className={`mt-1 text-xl font-semibold ${
                (data.price_deviation_percent ?? 0) > 0 ? 'text-danger-600' : 'text-success-600'
              }`}>
                {(data.price_deviation_percent ?? 0) > 0 ? '+' : ''}
                {data.price_deviation_percent?.toFixed(1)}%
              </dd>
            </div>

            <div className="border-l-4 border-accent-500 pl-4">
              <dt className="text-sm font-medium text-gray-500">{t('metrics.recommendation')}</dt>
              <dd className="mt-1 text-lg font-semibold text-gray-900">
                {data.recommendation}
              </dd>
            </div>
          </div>

          {data.estimated_value_2025 && data.trend_used != null && (
            <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-4 text-sm">
              <span className="text-gray-500">{t('metrics.projection', { year: new Date().getFullYear() })}:</span>
              <span className="font-semibold text-accent-600">
                {formatCurrency(data.estimated_value_2025)}
              </span>
              <span className={`font-medium ${data.trend_used > 0 ? 'text-success-600' : 'text-danger-600'}`}>
                ({data.trend_used > 0 ? '+' : ''}{data.trend_used.toFixed(2)}%/yr)
              </span>
            </div>
          )}
        </>
      )}
    </div>
  );
}
