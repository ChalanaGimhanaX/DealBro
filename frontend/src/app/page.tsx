'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import DealsFilter from '@/components/DealsFilter';
import DealCardSimple from '@/components/DealCardSimple';
import Pagination from '@/components/Pagination';
import { Deal, FilterOptions, DealItem } from '@/types';
import { fetchDeals } from '@/lib/api';

// Flattened deal item for display
interface FlatDealItem {
  id: string;
  title: string;
  providerName: string | null;
  planName: string | null;
  location: string | null;
  cpuBrand: string | null;
  ramMb: number | null;
  storageGb: number | null;
  bandwidthGb: number | null;
  ipv4: number | null;
  ipv6: boolean | null;
  priceAmount: number | null;
  priceCurrency: string | null;
  billingPeriod: string | null;
  orderUrl: string | null;
  category: string | null;
  providerDomain: string | null;
  promoCode?: string | null;
  promoUrl?: string | null;
}

export default function Home() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState<FilterOptions>({});

  // Flatten deals - each deal_item becomes a separate card
  const flattenedDeals = useMemo(() => {
    const items: FlatDealItem[] = [];
    
    deals.forEach((deal) => {
      if (!deal.deal_items || deal.deal_items.length === 0) return;
      
      deal.deal_items.forEach((item, idx) => {
        items.push({
          id: `${deal.id}-${item.id || idx}`,
          title: deal.title || 'Hosting Deal',
          providerName: item.provider_name || deal.provider_name || null,
          planName: item.plan_name || null,
          location: item.location,
          cpuBrand: item.cpu_brand || null,
          ramMb: item.ram_mb,
          storageGb: item.storage_gb,
          bandwidthGb: item.bandwidth_gb,
          ipv4: item.ipv4 ?? null,
          ipv6: item.ipv6 ?? null,
          priceAmount: item.price_amount,
          priceCurrency: item.price_currency,
          billingPeriod: item.billing_period,
          orderUrl: item.order_url,
          category: deal.category,
          providerDomain: item.provider_domain ?? deal.provider_domain ?? null,
          promoCode: item.promo_code ?? null,
          promoUrl: item.promo_url ?? null,
        });
      });
    });
    
    return items;
  }, [deals]);

  const loadDeals = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetchDeals({ ...filters, page, page_size: 50 }); // Fetch more since we flatten
      setDeals(response.items);
      setTotalPages(response.pages);
      setTotal(response.total);
    } catch (err) {
      setError('Failed to load deals. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    loadDeals();
  }, [loadDeals]);

  const handleFilterChange = useCallback((newFilters: FilterOptions) => {
    setFilters(newFilters);
    setPage(1);
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-extrabold text-gray-900">
            Hosting Deals
          </h2>
          <p className="text-gray-500 mt-1">
            {flattenedDeals.length} configurations from {total} posts
          </p>
        </div>
      </div>

      <DealsFilter onFilterChange={handleFilterChange} />

      {loading && (
        <div className="text-center py-16">
          <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-gray-200 border-t-gray-900"></div>
          <p className="mt-4 text-gray-500 font-medium">Loading deals...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-2xl">
          {error}
        </div>
      )}

      {!loading && !error && flattenedDeals.length === 0 && (
        <div className="text-center py-16 bg-gray-50 rounded-2xl">
          <p className="text-gray-500 font-medium">No deals found. Try adjusting your filters.</p>
        </div>
      )}

      {!loading && !error && flattenedDeals.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {flattenedDeals.map((item) => (
            <DealCardSimple
              key={item.id}
              title={item.title}
              providerName={item.providerName}
              planName={item.planName}
              location={item.location}
              cpuBrand={item.cpuBrand}
              ramMb={item.ramMb}
              storageGb={item.storageGb}
              bandwidthGb={item.bandwidthGb}
              ipv4={item.ipv4}
              ipv6={item.ipv6}
              priceAmount={item.priceAmount}
              priceCurrency={item.priceCurrency}
              billingPeriod={item.billingPeriod}
              orderUrl={item.orderUrl}
              category={item.category}
              providerDomain={item.providerDomain}
              promoCode={item.promoCode}
              promoUrl={item.promoUrl}
            />
          ))}
        </div>
      )}

      {!loading && totalPages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
