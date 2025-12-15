'use client';

import { useState, useEffect, useCallback } from 'react';
import { FilterOptions } from '@/types';
import { fetchCurrencies } from '@/lib/api';

interface DealsFilterProps {
  onFilterChange: (filters: FilterOptions) => void;
}

export default function DealsFilter({ onFilterChange }: DealsFilterProps) {
  const [currencies, setCurrencies] = useState<string[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [billingPeriod, setBillingPeriod] = useState('');
  const [currency, setCurrency] = useState('');
  const [location, setLocation] = useState('');
  const [category, setCategory] = useState('');

  useEffect(() => {
    loadFilterOptions();
  }, []);

  const loadFilterOptions = async () => {
    try {
      const currs = await fetchCurrencies();
      setCurrencies(currs);
    } catch (err) {
      console.error('Failed to load filter options', err);
    }
  };

  const applyFilters = useCallback(() => {
    const filters: FilterOptions = {};
    
    if (minPrice) filters.min_price = parseFloat(minPrice);
    if (maxPrice) filters.max_price = parseFloat(maxPrice);
    if (billingPeriod) filters.billing_period = billingPeriod;
    if (currency) filters.currency = currency;
    if (location) filters.location = location;
    if (category) {
      // UI alias: "webhosting" maps to backend "shared".
      filters.category = category === 'webhosting' ? 'shared' : category;
    }
    
    onFilterChange(filters);
  }, [minPrice, maxPrice, billingPeriod, currency, location, category, onFilterChange]);

  useEffect(() => {
    const timer = setTimeout(() => {
      applyFilters();
    }, 300);
    
    return () => clearTimeout(timer);
  }, [minPrice, maxPrice, billingPeriod, currency, location, category, applyFilters]);

  const handleReset = () => {
    setMinPrice('');
    setMaxPrice('');
    setBillingPeriod('');
    setCurrency('');
    setLocation('');
    setCategory('');
  };

  const hasFilters = minPrice || maxPrice || billingPeriod || currency || location || category;

  const categories = [
    { value: '', label: 'All Types' },
    { value: 'vps', label: 'VPS' },
    { value: 'dedicated', label: 'Dedicated' },
    { value: 'shared', label: 'Shared' },
    { value: 'webhosting', label: 'Web Hosting' },
    { value: 'cloud', label: 'Cloud' },
    { value: 'reseller', label: 'Reseller' },
  ];

  return (
    <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
      {/* Quick Filters Row */}
      <div className="p-4 flex flex-wrap items-center gap-3">
        {/* Category Pills */}
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat.value}
              onClick={() => setCategory(cat.value)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                category === cat.value
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="flex-grow" />

        {/* More Filters Toggle */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition"
        >
          <svg className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          More Filters
        </button>

        {hasFilters && (
          <button
            onClick={handleReset}
            className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 transition"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Expanded Filters */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-2 border-t border-gray-100 grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Min Price</label>
            <input
              type="number"
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="$0"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Max Price</label>
            <input
              type="number"
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="$500"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Billing</label>
            <select
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              value={billingPeriod}
              onChange={(e) => setBillingPeriod(e.target.value)}
            >
              <option value="">All</option>
              <option value="month">Monthly</option>
              <option value="year">Yearly</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Currency</label>
            <select
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
            >
              <option value="">All</option>
              {currencies.map((curr) => (
                <option key={curr} value={curr}>{curr}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1.5">Location</label>
            <input
              type="text"
              className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="US, EU..."
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>
        </div>
      )}
    </div>
  );
}