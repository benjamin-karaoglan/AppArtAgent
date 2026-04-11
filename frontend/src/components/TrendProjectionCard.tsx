"use client";

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { ChevronDown, ChevronUp, Info } from 'lucide-react';

interface NeighboringSale {
  id: number;
  address: string;
  sale_date: string;
  sale_price: number;
  surface_area?: number;
  price_per_sqm?: number;
  is_outlier?: boolean;
}

interface TrendProjection {
  estimated_value_2025?: number;
  projected_price_per_sqm?: number;
  trend_used?: number;
  trend_source?: string;
  trend_sample_size?: number;
  base_sale_date?: string;
  base_price_per_sqm?: number;
  neighboring_sales?: NeighboringSale[];
}

interface TrendProjectionCardProps {
  trendProjection: TrendProjection;
  excludedNeighboringIds: Set<number>;
  onToggle: (saleId: number) => void;
}

export default function TrendProjectionCard({
  trendProjection,
  excludedNeighboringIds,
  onToggle,
}: TrendProjectionCardProps) {
  const t = useTranslations('property');
  const [showNeighboringSales, setShowNeighboringSales] = useState(false);

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);

  if (!trendProjection.estimated_value_2025) return null;

  return (
    <div className="bg-gradient-to-r from-accent-50 to-primary-50 shadow rounded-lg p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">{t('trend.title', { year: new Date().getFullYear() })}</h2>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 mb-6">
        <div className="border-l-4 border-accent-600 pl-4 bg-white p-4 rounded">
          <dt className="text-sm font-medium text-gray-500 flex items-center">
            {t('trend.projectedValue', { year: new Date().getFullYear() })}
            <div className="relative inline-block ml-1 group/info">
              <span className="text-gray-400 group-hover/info:text-gray-600 cursor-help">
                <Info className="h-3.5 w-3.5" />
              </span>
              <div className="absolute z-10 left-0 top-full mt-1 w-72 p-3 bg-white border border-gray-200 rounded-lg shadow-lg text-xs text-gray-600 leading-relaxed opacity-0 invisible group-hover/info:opacity-100 group-hover/info:visible transition-opacity duration-150">
                {t('trend.projectedValueInfo')}
              </div>
            </div>
          </dt>
          <dd className="mt-1 text-2xl font-semibold text-accent-600">
            {formatCurrency(trendProjection.estimated_value_2025)}
          </dd>
          {trendProjection.projected_price_per_sqm && (
            <dd className="mt-1 text-sm text-gray-500">
              {formatCurrency(trendProjection.projected_price_per_sqm)}/m²
            </dd>
          )}
        </div>

        <div className="border-l-4 border-accent-500 pl-4 bg-white p-4 rounded">
          <dt className="text-sm font-medium text-gray-500">{t('trend.marketTrend')}</dt>
          <dd className={`mt-1 text-2xl font-semibold ${
            (trendProjection.trend_used ?? 0) > 0 ? 'text-success-600' : 'text-danger-600'
          }`}>
            {(trendProjection.trend_used ?? 0) > 0 ? '+' : ''}
            {trendProjection.trend_used?.toFixed(2)}% /year
          </dd>
          <dd className="mt-1">
            <button
              onClick={() => setShowNeighboringSales(!showNeighboringSales)}
              className="text-sm text-primary-600 hover:text-primary-800 flex items-center gap-1"
            >
              {t('trend.basedOnSales', { count: trendProjection.trend_sample_size ?? 0 })}
              {showNeighboringSales ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </dd>
        </div>
      </div>

      {showNeighboringSales && trendProjection.neighboring_sales && (
        <div className="bg-white p-4 rounded mb-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            {t('trend.neighboringSalesTitle', { count: trendProjection.neighboring_sales.length })}
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('comparables.include')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('comparables.saleDate')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('comparables.address')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('comparables.surface')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('comparables.salePrice')}</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('comparables.pricePerSqm')}</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {trendProjection.neighboring_sales.map((sale) => (
                  <tr
                    key={sale.id}
                    className={`hover:bg-gray-50 ${sale.is_outlier ? 'bg-warning-50' : ''} ${excludedNeighboringIds.has(sale.id) ? 'opacity-50' : ''}`}
                  >
                    <td className="px-2 py-2 whitespace-nowrap text-center">
                      <input
                        type="checkbox"
                        checked={!excludedNeighboringIds.has(sale.id)}
                        onChange={() => onToggle(sale.id)}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
                        title={sale.is_outlier ? t('comparables.outlierDetected') : t('comparables.includeInTrend')}
                      />
                      {sale.is_outlier && (
                        <div className="text-xs text-warning-600 mt-1">{t('comparables.outlier')}</div>
                      )}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-gray-900">
                      {new Date(sale.sale_date).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-3 py-2 text-gray-900">{sale.address}</td>
                    <td className="px-3 py-2 whitespace-nowrap text-gray-900">{sale.surface_area} m²</td>
                    <td className="px-3 py-2 whitespace-nowrap text-gray-900">
                      {formatCurrency(sale.sale_price)}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-gray-900">
                      {sale.price_per_sqm ? formatCurrency(sale.price_per_sqm) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {trendProjection.base_sale_date && (
        <div className="bg-white p-4 rounded">
          <h3 className="text-sm font-medium text-gray-700 mb-2">{t('trend.baseSale')}</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">{t('trend.date')}</span>
              <span className="ml-2 font-medium text-gray-900">
                {new Date(trendProjection.base_sale_date).toLocaleDateString('fr-FR')}
              </span>
            </div>
            {trendProjection.base_price_per_sqm && (
              <div>
                <span className="text-gray-500">{t('trend.pricePerSqm')}</span>
                <span className="ml-2 font-medium text-gray-900">
                  {formatCurrency(trendProjection.base_price_per_sqm)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
