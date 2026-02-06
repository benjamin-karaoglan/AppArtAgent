"use client";

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';
import { TrendingUp, TrendingDown, Loader2 } from 'lucide-react';

interface MarketTrendData {
  years: number[];
  average_prices: number[];
  year_over_year_changes: number[];
  sample_counts: number[];
  street_name?: string;
  total_sales: number;
  outliers_excluded: number;
}

interface MarketTrendChartProps {
  propertyId: string;
}

export default function MarketTrendChart({ propertyId }: MarketTrendChartProps) {
  const [trendData, setTrendData] = useState<MarketTrendData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const t = useTranslations('property.marketTrend');

  useEffect(() => {
    loadTrendData();
  }, [propertyId]);

  const loadTrendData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get(`/api/properties/${propertyId}/market-trend`);
      setTrendData(response.data);
    } catch (err) {
      console.error('Failed to load market trend:', err);
      setError(t('loadFailed'));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !trendData || trendData.years.length === 0) {
    return (
      <div className="text-sm text-gray-500 text-center py-4">
        {error || t('noData')}
      </div>
    );
  }

  // Find min and max for scaling
  const minPrice = Math.min(...trendData.average_prices);
  const maxPrice = Math.max(...trendData.average_prices);
  const priceRange = maxPrice - minPrice;
  const chartPadding = priceRange * 0.1; // 10% padding

  // Calculate chart dimensions
  const chartHeight = 200;
  const chartWidth = 600;
  const barWidth = chartWidth / trendData.years.length;

  const scaleY = (price: number) => {
    const normalized = (price - minPrice + chartPadding) / (priceRange + 2 * chartPadding);
    return chartHeight - (normalized * chartHeight);
  };

  return (
    <div className="bg-white rounded-lg p-6">
      <div className="mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          {t('title')}{trendData.street_name ? ` - ${trendData.street_name}` : ''}
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          {t('basedOnSales', { count: trendData.total_sales })}{trendData.outliers_excluded > 0 && (
            <span className="font-medium text-orange-600">
              {' '}({t('outliersExcluded', { count: trendData.outliers_excluded })})
            </span>
          )}
        </p>
      </div>

      {/* SVG Chart */}
      <div className="mb-6 overflow-x-auto">
        <svg
          width={chartWidth}
          height={chartHeight + 60}
          className="mx-auto"
          style={{ minWidth: '600px' }}
        >
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((percent) => {
            const y = chartHeight * percent;
            const price = maxPrice + chartPadding - (priceRange + 2 * chartPadding) * percent;
            return (
              <g key={percent}>
                <line
                  x1={0}
                  y1={y}
                  x2={chartWidth}
                  y2={y}
                  stroke="#e5e7eb"
                  strokeDasharray="4 2"
                />
                <text
                  x={-10}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="11"
                  fill="#6b7280"
                >
                  {new Intl.NumberFormat('fr-FR', {
                    style: 'currency',
                    currency: 'EUR',
                    maximumFractionDigits: 0,
                  }).format(price)}
                </text>
              </g>
            );
          })}

          {/* Bars */}
          {trendData.years.map((year, idx) => {
            const x = idx * barWidth;
            const barHeight = chartHeight - scaleY(trendData.average_prices[idx]);
            const y = scaleY(trendData.average_prices[idx]);
            const yoyChange = trendData.year_over_year_changes[idx];
            const isPositive = yoyChange >= 0;

            return (
              <g key={year}>
                {/* Bar */}
                <rect
                  x={x + barWidth * 0.15}
                  y={y}
                  width={barWidth * 0.7}
                  height={barHeight}
                  fill={isPositive ? '#10b981' : '#ef4444'}
                  opacity={0.7}
                  className="hover:opacity-100 transition-opacity cursor-pointer"
                >
                  <title>
                    {year}: {new Intl.NumberFormat('fr-FR', {
                      style: 'currency',
                      currency: 'EUR',
                      maximumFractionDigits: 0,
                    }).format(trendData.average_prices[idx])}/m²
                    {idx > 0 && ` (${yoyChange > 0 ? '+' : ''}${yoyChange.toFixed(1)}%)`}
                    {'\n'}{trendData.sample_counts[idx]} {t('basedOnSales', { count: trendData.sample_counts[idx] }).split(' ').slice(-1)[0]}
                  </title>
                </rect>

                {/* Year label */}
                <text
                  x={x + barWidth / 2}
                  y={chartHeight + 20}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#374151"
                  fontWeight="500"
                >
                  {year}
                </text>

                {/* YoY change indicator */}
                {idx > 0 && (
                  <text
                    x={x + barWidth / 2}
                    y={chartHeight + 38}
                    textAnchor="middle"
                    fontSize="11"
                    fill={isPositive ? '#10b981' : '#ef4444'}
                    fontWeight="600"
                  >
                    {yoyChange > 0 ? '+' : ''}{yoyChange.toFixed(1)}%
                  </text>
                )}

                {/* Sample count */}
                <text
                  x={x + barWidth / 2}
                  y={chartHeight + 54}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#9ca3af"
                >
                  {trendData.sample_counts[idx]}
                </text>
              </g>
            );
          })}

          {/* Line connecting bar tops */}
          <polyline
            points={trendData.years.map((year, idx) => {
              const x = idx * barWidth + barWidth / 2;
              const y = scaleY(trendData.average_prices[idx]);
              return `${x},${y}`;
            }).join(' ')}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            opacity="0.8"
          />

          {/* Data points */}
          {trendData.years.map((year, idx) => {
            const x = idx * barWidth + barWidth / 2;
            const y = scaleY(trendData.average_prices[idx]);
            return (
              <circle
                key={year}
                cx={x}
                cy={y}
                r="4"
                fill="#3b82f6"
                stroke="white"
                strokeWidth="2"
                className="hover:r-6 transition-all cursor-pointer"
              />
            );
          })}
        </svg>
      </div>

      {/* Legend and Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="flex items-center gap-2 p-3 bg-green-50 rounded">
          <TrendingUp className="h-5 w-5 text-green-600" />
          <div>
            <div className="font-medium text-green-900">{t('positiveGrowth')}</div>
            <div className="text-green-700 text-xs">{t('positiveGrowthDesc')}</div>
          </div>
        </div>
        <div className="flex items-center gap-2 p-3 bg-red-50 rounded">
          <TrendingDown className="h-5 w-5 text-red-600" />
          <div>
            <div className="font-medium text-red-900">{t('negativeGrowth')}</div>
            <div className="text-red-700 text-xs">{t('negativeGrowthDesc')}</div>
          </div>
        </div>
        <div className="flex items-center gap-2 p-3 bg-blue-50 rounded">
          <div className="w-5 h-5 bg-blue-500 rounded"></div>
          <div>
            <div className="font-medium text-blue-900">{t('trendLine')}</div>
            <div className="text-blue-700 text-xs">{t('trendLineDesc')}</div>
          </div>
        </div>
      </div>

      {/* Overall trend summary */}
      {trendData.years.length > 1 && (
        <div className="mt-4 p-4 bg-gray-50 rounded border border-gray-200">
          <div className="text-sm font-medium text-gray-900 mb-2">{t('marketSummary')}</div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">{t('earliestPrice', { year: trendData.years[0] })}</span>
              <span className="ml-2 font-semibold">
                {new Intl.NumberFormat('fr-FR', {
                  style: 'currency',
                  currency: 'EUR',
                  maximumFractionDigits: 0,
                }).format(trendData.average_prices[0])}/m²
              </span>
            </div>
            <div>
              <span className="text-gray-600">{t('latestPrice', { year: trendData.years[trendData.years.length - 1] })}</span>
              <span className="ml-2 font-semibold">
                {new Intl.NumberFormat('fr-FR', {
                  style: 'currency',
                  currency: 'EUR',
                  maximumFractionDigits: 0,
                }).format(trendData.average_prices[trendData.average_prices.length - 1])}/m²
              </span>
            </div>
            <div>
              <span className="text-gray-600">{t('totalChange')}</span>
              <span className={`ml-2 font-semibold ${
                trendData.average_prices[trendData.average_prices.length - 1] >= trendData.average_prices[0]
                  ? 'text-green-600'
                  : 'text-red-600'
              }`}>
                {((trendData.average_prices[trendData.average_prices.length - 1] - trendData.average_prices[0]) / trendData.average_prices[0] * 100).toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="text-gray-600">{t('totalSalesAnalyzed')}</span>
              <span className="ml-2 font-semibold">
                {trendData.sample_counts.reduce((a, b) => a + b, 0)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
