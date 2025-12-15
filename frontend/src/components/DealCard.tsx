'use client';

import { Deal } from '@/types';
import { formatDistanceToNow } from 'date-fns';

interface DealCardProps {
  deal: Deal;
}

export default function DealCard({ deal }: DealCardProps) {
  const primaryItem = deal.deal_items.find((item) => item.is_primary) || deal.deal_items[0];
  
  const formatPrice = (item: any) => {
    if (!item || !item.price_amount) return 'Price on request';
    
    const currency = item.price_currency || 'USD';
    const period = item.billing_period === 'month' ? '/mo' : 
                   item.billing_period === 'year' ? '/yr' : '';
    
    return `${currency} ${item.price_amount.toFixed(2)}${period}`;
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Recently';
    try {
      return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
    } catch {
      return 'Recently';
    }
  };

  const getCategoryColor = (category: string | null) => {
    const colors: { [key: string]: string } = {
      shared: 'bg-blue-100 text-blue-800',
      reseller: 'bg-purple-100 text-purple-800',
      vps: 'bg-green-100 text-green-800',
      dedicated: 'bg-red-100 text-red-800',
      cloud: 'bg-indigo-100 text-indigo-800',
      colo: 'bg-yellow-100 text-yellow-800',
      other: 'bg-gray-100 text-gray-800',
    };
    return colors[category || 'other'] || colors.other;
  };

  const formatSpecs = (item: any) => {
    const specs = [];
    if (item.ram_mb) specs.push(`${item.ram_mb >= 1024 ? (item.ram_mb / 1024).toFixed(0) + 'GB' : item.ram_mb + 'MB'} RAM`);
    if (item.storage_gb) specs.push(`${item.storage_gb}GB Storage`);
    if (item.bandwidth_gb) {
      if (item.bandwidth_gb === -1) {
        specs.push('Unlimited BW');
      } else {
        specs.push(`${item.bandwidth_gb}GB BW`);
      }
    }
    if (item.cpu) specs.push(`${item.cpu} CPU`);
    return specs.join(' • ');
  };

  // Get title - prefer deal title, fallback to provider name
  const displayTitle = deal.title && deal.title !== 'Unknown' && deal.title !== 'Deal Post' 
    ? deal.title 
    : deal.provider_name || 'Hosting Deal';

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-start justify-between gap-2 mb-2">
          <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${getCategoryColor(deal.category)}`}>
            {deal.category || 'other'}
          </span>
          <span className="text-xs text-gray-500">{formatDate(deal.posted_at)}</span>
        </div>
        
        <h3 className="font-bold text-lg text-gray-900 line-clamp-2 min-h-[3.5rem]">
          {displayTitle}
        </h3>
        
        {deal.provider_name && deal.provider_name !== 'Unknown' && (
          <p className="text-sm text-gray-600 mt-1">
            {deal.provider_name}
            {deal.provider_domain && <span className="text-gray-400 ml-1">• {deal.provider_domain}</span>}
          </p>
        )}
      </div>

      {/* Body */}
      <div className="p-4 flex-grow flex flex-col justify-between">
        <div className="space-y-3">
          {/* Location */}
          {primaryItem?.location && (
            <div className="flex items-center text-sm text-gray-600">
              <span className="mr-2">📍</span>
              {primaryItem.location}
            </div>
          )}

          {/* Highlights */}
          {deal.highlights && deal.highlights.length > 0 && (
            <div className="space-y-1">
              {deal.highlights.slice(0, 3).map((highlight: string, idx: number) => (
                <div key={idx} className="text-xs text-gray-600 flex items-start">
                  <span className="text-green-500 mr-1">✓</span>
                  <span className="line-clamp-1">{highlight}</span>
                </div>
              ))}
            </div>
          )}

          {/* Specs */}
          {primaryItem && formatSpecs(primaryItem) && (
            <div className="text-sm text-gray-700 font-medium">
              {formatSpecs(primaryItem)}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-4 pt-4 border-t border-gray-100">
          {primaryItem && (
            <div className="flex items-end justify-between">
              <div>
                <div className="text-2xl font-bold text-primary-600">
                  {formatPrice(primaryItem)}
                </div>
                {primaryItem.price_monthly_normalized && primaryItem.billing_period !== 'month' && (
                  <div className="text-xs text-gray-500">
                    ${primaryItem.price_monthly_normalized.toFixed(2)}/mo
                  </div>
                )}
              </div>
              
              <a
                href={primaryItem?.order_url || (deal.provider_domain ? `https://${deal.provider_domain}` : '#')}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary btn-sm whitespace-nowrap"
              >
                View Deal
              </a>
            </div>
          )}
          
          {/* Multiple plans indicator */}
          {deal.deal_items.length > 1 && (
            <div className="text-xs text-gray-500 mt-2">
              +{deal.deal_items.length - 1} more {deal.deal_items.length === 2 ? 'plan' : 'plans'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
