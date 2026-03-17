"use client";

import { useTranslations } from 'next-intl';
import { Info } from 'lucide-react';

interface PriceMetricsGridProps {
  estimated_value?: number;
  price_deviation_percent?: number;
  comparables_count?: number;
  recommendation?: string;
}

function InfoBucket({ text }: { text: string }) {
  return (
    <div className="relative inline-block ml-1 group/info">
      <span className="text-gray-400 group-hover/info:text-gray-600 cursor-help">
        <Info className="h-3.5 w-3.5" />
      </span>
      <div className="absolute z-10 left-0 top-full mt-1 w-64 p-3 bg-white border border-gray-200 rounded-lg shadow-lg text-xs text-gray-600 leading-relaxed opacity-0 invisible group-hover/info:opacity-100 group-hover/info:visible transition-opacity duration-150">
        {text}
      </div>
    </div>
  );
}

export default function PriceMetricsGrid({
  estimated_value,
  price_deviation_percent,
  comparables_count,
  recommendation,
}: PriceMetricsGridProps) {
  const t = useTranslations('property.priceAnalyst.metrics');

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div className="bg-white rounded-lg shadow p-5 border-l-4 border-primary-500">
        <dt className="text-sm font-medium text-gray-500 flex items-center">
          {t('estimatedValue')}
          <InfoBucket text={t('estimatedValueInfo')} />
        </dt>
        <dd className="mt-1 text-2xl font-semibold text-gray-900">
          {estimated_value != null ? formatCurrency(estimated_value) : '-'}
        </dd>
      </div>

      <div className="bg-white rounded-lg shadow p-5 border-l-4 border-warning-500">
        <dt className="text-sm font-medium text-gray-500 flex items-center">
          {t('deviation')}
          <InfoBucket text={t('deviationInfo')} />
        </dt>
        <dd className={`mt-1 text-2xl font-semibold ${
          price_deviation_percent != null
            ? price_deviation_percent > 0 ? 'text-danger-600' : 'text-success-600'
            : 'text-gray-900'
        }`}>
          {price_deviation_percent != null
            ? `${price_deviation_percent > 0 ? '+' : ''}${price_deviation_percent.toFixed(1)}%`
            : '-'}
        </dd>
      </div>

      <div className="bg-white rounded-lg shadow p-5 border-l-4 border-success-500">
        <dt className="text-sm font-medium text-gray-500 flex items-center">
          {t('comparables')}
          <InfoBucket text={t('comparablesInfo')} />
        </dt>
        <dd className="mt-1 text-2xl font-semibold text-gray-900">
          {comparables_count ?? '-'}
        </dd>
      </div>

      <div className="bg-white rounded-lg shadow p-5 border-l-4 border-accent-500">
        <dt className="text-sm font-medium text-gray-500">{t('recommendation')}</dt>
        <dd className="mt-1 text-sm font-semibold text-gray-900 leading-snug">
          {recommendation || '-'}
        </dd>
      </div>
    </div>
  );
}
