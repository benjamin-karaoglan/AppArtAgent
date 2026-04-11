"use client";

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ArrowLeft, TrendingUp, Download } from 'lucide-react';
import Spinner from '@/components/ui/Spinner';
import { Link } from '@/i18n/navigation';
import ProtectedRoute from '@/components/ProtectedRoute';
import Header from '@/components/Header';
import PriceMetricsGrid from '@/components/PriceMetricsGrid';
import MarketTrendChart from '@/components/MarketTrendChart';
import TrendProjectionCard from '@/components/TrendProjectionCard';
import ComparableSalesTable from '@/components/ComparableSalesTable';
import { api, reportsAPI } from '@/lib/api';
import type { Property, PriceAnalysisFull } from '@/types';

function PriceAnalystContent() {
  const t = useTranslations('property');
  const tr = useTranslations('report');
  const params = useParams();
  const propertyId = params.id as string;

  const [property, setProperty] = useState<Property | null>(null);
  const [analysis, setAnalysis] = useState<PriceAnalysisFull | null>(null);
  const [loading, setLoading] = useState(true);
  const [excludedSaleIds, setExcludedSaleIds] = useState<Set<number>>(new Set());
  const [excludedNeighboringIds, setExcludedNeighboringIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadData();
  }, [propertyId]);

  const loadData = async () => {
    try {
      const [propRes, analysisRes] = await Promise.all([
        api.get(`/api/properties/${propertyId}`),
        api.get(`/api/properties/${propertyId}/price-analysis/full`),
      ]);
      setProperty(propRes.data);
      setAnalysis(analysisRes.data);
      setExcludedSaleIds(new Set(analysisRes.data.excluded_sale_ids || []));
      setExcludedNeighboringIds(new Set(analysisRes.data.excluded_neighboring_sale_ids || []));
    } catch (error) {
      console.error('Failed to load price analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  const persistExclusions = useCallback(async (saleIds: number[], neighboringIds: number[]) => {
    try {
      const response = await api.post(`/api/properties/${propertyId}/price-analysis/exclude-sales`, {
        excluded_sale_ids: saleIds,
        excluded_neighboring_sale_ids: neighboringIds,
      });
      const data = response.data;
      setAnalysis(data);
      // Sync exclusion state from backend response (single source of truth)
      setExcludedSaleIds(new Set(data.excluded_sale_ids || []));
      setExcludedNeighboringIds(new Set(data.excluded_neighboring_sale_ids || []));
    } catch (error) {
      console.error('Failed to persist exclusions:', error);
    }
  }, [propertyId]);

  const toggleSaleExclusion = (saleId: number) => {
    const next = new Set(excludedSaleIds);
    if (next.has(saleId)) next.delete(saleId);
    else next.add(saleId);
    setExcludedSaleIds(next);
    persistExclusions(Array.from(next), Array.from(excludedNeighboringIds));
  };

  const toggleNeighboringExclusion = (saleId: number) => {
    const next = new Set(excludedNeighboringIds);
    if (next.has(saleId)) next.delete(saleId);
    else next.add(saleId);
    setExcludedNeighboringIds(next);
    persistExclusions(Array.from(excludedSaleIds), Array.from(next));
  };

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex items-center justify-center h-96">
          <Spinner size={32} className="text-primary-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Back link */}
          <Link
            href={`/properties/${propertyId}`}
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-6"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            {t('priceAnalyst.backToProperty')}
          </Link>

          {/* Page title */}
          <div className="mb-8">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                  <TrendingUp className="h-8 w-8 text-primary-600" />
                  {t('priceAnalyst.title')}
                </h1>
                {property && (
                  <p className="mt-2 text-sm text-gray-600">
                    {property.address} - {property.city} {property.postal_code}
                    {property.asking_price && (
                      <span className="ml-3 font-semibold">{formatCurrency(property.asking_price)}</span>
                    )}
                  </p>
                )}
              </div>
              <a
                href={reportsAPI.downloadPriceAnalysis(Number(propertyId))}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
              >
                <Download className="h-4 w-4 mr-2" />
                {tr('exportPdf')}
              </a>
            </div>
          </div>

          {!analysis?.estimated_value ? (
            <div className="bg-white shadow rounded-lg p-8 text-center">
              <TrendingUp className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">{t('priceAnalyst.summary.noData')}</p>
            </div>
          ) : (
            <div className="space-y-8">
              {/* Metrics Grid */}
              <PriceMetricsGrid
                estimated_value={analysis.estimated_value}
                price_deviation_percent={analysis.price_deviation_percent}
                comparables_count={analysis.comparables_count}
                recommendation={analysis.recommendation}
              />

              {/* Comparable Sales */}
              {analysis.comparable_sales && analysis.comparable_sales.length > 0 && (
                <ComparableSalesTable
                  sales={analysis.comparable_sales}
                  excludedIds={excludedSaleIds}
                  onToggle={toggleSaleExclusion}
                  marketAvgPricePerSqm={analysis.market_avg_price_per_sqm}
                  marketMedianPricePerSqm={analysis.market_median_price_per_sqm}
                  pricePerSqm={analysis.price_per_sqm}
                  comparablesCount={analysis.comparables_count}
                />
              )}

              {/* Trend Projection */}
              {analysis.trend_projection && (
                <TrendProjectionCard
                  trendProjection={analysis.trend_projection}
                  excludedNeighboringIds={excludedNeighboringIds}
                  onToggle={toggleNeighboringExclusion}
                />
              )}

              {/* Market Trend Chart */}
              {analysis.market_trend && analysis.market_trend.years?.length > 0 && (
                <MarketTrendChart propertyId={propertyId} />
              )}

              {/* Last updated */}
              {analysis.updated_at && (
                <p className="text-center text-xs text-gray-400 pt-4">
                  {t('priceAnalyst.lastUpdated', {
                    date: new Date(analysis.updated_at).toLocaleString('fr-FR'),
                  })}
                </p>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function PriceAnalystPage() {
  return (
    <ProtectedRoute>
      <PriceAnalystContent />
    </ProtectedRoute>
  );
}
