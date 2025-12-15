'use client';

interface DealCardSimpleProps {
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

export default function DealCardSimple({
  title,
  providerName,
  planName,
  location,
  cpuBrand,
  ramMb,
  storageGb,
  bandwidthGb,
  ipv4,
  ipv6,
  priceAmount,
  priceCurrency,
  billingPeriod,
  orderUrl,
  category,
  providerDomain,
  promoCode,
  promoUrl,
}: DealCardSimpleProps) {
  const periodLabel = billingPeriod === 'month' ? '/mo' : billingPeriod === 'year' ? '/yr' : '';
  const currency = (priceCurrency || 'USD').toUpperCase();

  const formatPrice = () => {
    if (priceAmount == null) return 'Price on request';
    const symbol = currency === 'USD' ? '$' : currency === 'EUR' ? '€' : currency === 'GBP' ? '£' : `${currency} `;
    return `${symbol}${priceAmount.toFixed(2)}${periodLabel}`;
  };

  const formatRam = () => {
    if (!ramMb) return null;
    return ramMb >= 1024 ? `${Math.round(ramMb / 1024)}GB` : `${ramMb}MB`;
  };

  const formatBw = () => {
    if (bandwidthGb == null) return null;
    return bandwidthGb === -1 ? 'Unmetered' : `${bandwidthGb}GB`;
  };

  // Use provider name as title, fallback to plan name or title
  const displayTitle = providerName || planName || title.slice(0, 40);

  const href = promoUrl || orderUrl || (providerDomain ? `https://${providerDomain}` : '#');

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow flex flex-col h-full">
      <div className="flex items-start justify-between gap-3">
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wide bg-primary-50 text-primary-700 border border-primary-100">
          {category || 'hosting'}
        </span>
        <div className="text-right">
          <div className="text-lg font-bold text-gray-900">{formatPrice()}</div>
        </div>
      </div>

      <h3 className="mt-3 font-bold text-gray-900 text-base">
        {displayTitle}
      </h3>

      {planName && providerName && (
        <div className="mt-1 text-sm text-gray-600">
          {planName}
        </div>
      )}

      <div className="mt-3 space-y-1.5 text-sm text-gray-700">
        {location && (
          <div><span className="text-gray-500">Location:</span> {location}</div>
        )}
        {cpuBrand && (
          <div><span className="text-gray-500">CPU:</span> {cpuBrand}</div>
        )}
        {formatRam() && (
          <div><span className="text-gray-500">Memory:</span> {formatRam()}</div>
        )}
        {storageGb != null && (
          <div><span className="text-gray-500">Storage:</span> {storageGb}GB NVMe</div>
        )}
        {formatBw() && (
          <div><span className="text-gray-500">Port:</span> 1 Gbps - {formatBw()} Traffic</div>
        )}
        {(ipv4 != null || ipv6 != null) && (
          <div>
            <span className="text-gray-500">IP:</span>{' '}
            {ipv4 != null && `${ipv4} IPv4`}
            {ipv4 != null && ipv6 && ' + '}
            {ipv6 && 'IPv6'}
          </div>
        )}
      </div>

      {promoCode && (
        <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded-lg">
          <div className="text-xs text-green-600 font-medium mb-0.5">Promo Code</div>
          <div className="text-sm font-bold text-green-900">{promoCode}</div>
        </div>
      )}

      <div className="mt-auto pt-4">
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex w-full justify-center items-center px-3 py-2 rounded-lg text-sm font-semibold bg-primary-600 text-white hover:bg-primary-700 transition-colors"
        >
          {promoCode ? 'Get Deal & Use Code' : 'Link to the configurator'}
        </a>
      </div>
    </div>
  );
}
