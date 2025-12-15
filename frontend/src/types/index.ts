export interface Source {
  id: string;
  name: string;
  base_url: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface DealItem {
  id: string;
  provider_name: string | null;
  plan_name?: string | null;
  provider_domain: string | null;
  price_amount: number | null;
  price_currency: string | null;
  billing_period: string | null;
  price_monthly_normalized: number | null;
  location: string | null;
  cpu: string | null;
  cpu_brand?: string | null;
  cpu_cores?: number | null;
  ram_mb: number | null;
  storage_gb: number | null;
  bandwidth_gb: number | null;
  ipv4?: number | null;
  ipv6?: boolean | null;  promo_code?: string | null;
  promo_url?: string | null;  order_url: string | null;
  is_primary: boolean;
}

export interface Deal {
  id: string;
  source_id: string;
  title: string;
  author: string | null;
  posted_at: string | null;
  category: string | null;
  is_duplicate: boolean;
  provider_name?: string | null;
  provider_domain?: string | null;
  highlights?: string[];
  source: Source;
  deal_items: DealItem[];
}

export interface PaginatedDealsResponse {
  items: Deal[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface FilterOptions {
  category?: string;
  min_price?: number;
  max_price?: number;
  billing_period?: string;
  currency?: string;
  location?: string;
  source_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}
