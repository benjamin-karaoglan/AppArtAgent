"use client";

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Building2, ChevronDown, ChevronUp } from 'lucide-react';
import type { DVFRecord } from '@/types';

interface ComparableSalesTableProps {
  sales: DVFRecord[];
  excludedIds: Set<number>;
  onToggle: (saleId: number) => void;
  marketAvgPricePerSqm?: number;
  marketMedianPricePerSqm?: number;
  pricePerSqm?: number;
  comparablesCount?: number;
}

export default function ComparableSalesTable({
  sales,
  excludedIds,
  onToggle,
  marketAvgPricePerSqm,
  marketMedianPricePerSqm,
  pricePerSqm,
  comparablesCount,
}: ComparableSalesTableProps) {
  const t = useTranslations('property');
  const [expandedSales, setExpandedSales] = useState<Set<number>>(new Set());

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);

  const toggleExpand = (saleId: number) => {
    const next = new Set(expandedSales);
    if (next.has(saleId)) next.delete(saleId);
    else next.add(saleId);
    setExpandedSales(next);
  };

  if (!sales.length) return null;

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-4">
        {t('comparables.title', { total: sales.length, included: comparablesCount ?? sales.length })}
      </h2>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('comparables.include')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('comparables.saleDate')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('comparables.address')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('comparables.surface')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('comparables.salePrice')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('comparables.pricePerSqm')}</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sales.map((sale) => {
              const isMultiUnit = sale.unit_count && sale.unit_count > 1;
              const isExpanded = expandedSales.has(sale.id);
              const displayPricePerSqm = sale.price_per_sqm;

              return (
                <tr key={sale.id}>
                  <td colSpan={6} className="p-0">
                    <table className="min-w-full">
                      <tbody>
                        <tr
                          className={`hover:bg-gray-50 ${sale.is_outlier ? 'bg-warning-50' : ''} ${excludedIds.has(sale.id) ? 'opacity-50' : ''} ${isMultiUnit ? 'border-l-4 border-l-primary-500' : ''}`}
                        >
                          <td className="px-3 py-4 whitespace-nowrap text-center w-16">
                            <input
                              type="checkbox"
                              checked={!excludedIds.has(sale.id)}
                              onChange={() => onToggle(sale.id)}
                              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer"
                              title={sale.is_outlier ? t('comparables.outlierDetected') : t('comparables.includeInAnalysis')}
                            />
                            {sale.is_outlier && (
                              <div className="text-xs text-warning-600 mt-1">{t('comparables.outlier')}</div>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {new Date(sale.sale_date).toLocaleDateString('fr-FR')}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900">
                            <div className="flex items-start gap-2">
                              <div className="flex-1">
                                {sale.address || '-'}<br />
                                <span className="text-gray-500">{sale.city} {sale.postal_code}</span>
                              </div>
                              {isMultiUnit && (
                                <button
                                  onClick={() => toggleExpand(sale.id)}
                                  className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-primary-700 bg-primary-50 rounded hover:bg-primary-100"
                                >
                                  <Building2 className="h-3 w-3" />
                                  {t('comparables.units', { count: sale.unit_count ?? 1 })}
                                  {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                                </button>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {sale.surface_area} m²
                            {isMultiUnit && sale.rooms && (
                              <div className="text-xs text-gray-500">{t('comparables.rooms')}: {sale.rooms}</div>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                            {formatCurrency(sale.sale_price)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {displayPricePerSqm ? formatCurrency(displayPricePerSqm) : '-'}
                            {isMultiUnit && (
                              <div className="text-xs text-primary-600 font-medium">{t('comparables.grouped')}</div>
                            )}
                          </td>
                        </tr>
                        {isMultiUnit && isExpanded && sale.lots_detail && (
                          <tr className="bg-primary-50">
                            <td colSpan={6} className="px-6 py-4">
                              <div className="text-xs font-medium text-gray-700 mb-2 uppercase">
                                {t('comparables.individualUnits', { count: sale.unit_count ?? 1 })}
                              </div>
                              <div className="bg-white rounded border border-primary-200 overflow-hidden">
                                <table className="min-w-full text-xs">
                                  <thead className="bg-gray-50">
                                    <tr>
                                      <th className="px-3 py-2 text-left font-medium text-gray-500">{t('comparables.unit')}</th>
                                      <th className="px-3 py-2 text-left font-medium text-gray-500">{t('comparables.type')}</th>
                                      <th className="px-3 py-2 text-left font-medium text-gray-500">{t('comparables.surface')}</th>
                                      <th className="px-3 py-2 text-left font-medium text-gray-500">{t('comparables.rooms')}</th>
                                      <th className="px-3 py-2 text-left font-medium text-gray-500">{t('comparables.individualPricePerSqm')}</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-gray-200">
                                    {sale.lots_detail.map((lot, lotIdx) => (
                                      <tr key={lotIdx} className="hover:bg-gray-50">
                                        <td className="px-3 py-2 text-gray-700">{t('comparables.unit')} {lotIdx + 1}</td>
                                        <td className="px-3 py-2 text-gray-600">{lot.lot_type || '-'}</td>
                                        <td className="px-3 py-2 text-gray-900">{lot.surface_area ? `${lot.surface_area} m²` : '-'}</td>
                                        <td className="px-3 py-2 text-gray-900">{lot.rooms || '-'}</td>
                                        <td className="px-3 py-2 text-gray-900">
                                          {lot.price_per_sqm ? formatCurrency(lot.price_per_sqm) : '-'}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                                {displayPricePerSqm && (
                                  <div className="px-3 py-2 bg-gray-50 text-xs text-gray-600 border-t border-gray-200">
                                    {t('comparables.groupedNote', { price: formatCurrency(displayPricePerSqm) })}
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {marketAvgPricePerSqm && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">{t('comparables.marketAvgPrice')}</dt>
              <dd className="mt-1 text-lg font-semibold text-gray-900">
                {formatCurrency(marketAvgPricePerSqm)}
              </dd>
            </div>
            {pricePerSqm && (
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('comparables.yourPrice')}</dt>
                <dd className="mt-1 text-lg font-semibold text-gray-900">
                  {formatCurrency(pricePerSqm)}
                </dd>
              </div>
            )}
            {marketMedianPricePerSqm && (
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('comparables.marketMedianPrice')}</dt>
                <dd className="mt-1 text-lg font-semibold text-gray-900">
                  {formatCurrency(marketMedianPricePerSqm)}
                </dd>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
