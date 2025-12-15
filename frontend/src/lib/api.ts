import axios from 'axios';
import { PaginatedDealsResponse, FilterOptions, Source } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export async function fetchDeals(filters: FilterOptions = {}): Promise<PaginatedDealsResponse> {
  const response = await api.get('/deals', { params: filters });
  return response.data;
}

export async function fetchDealById(id: string) {
  const response = await api.get(`/deals/${id}`);
  return response.data;
}

export async function fetchSources(): Promise<Source[]> {
  const response = await api.get('/sources');
  return response.data;
}

export async function fetchCategories(): Promise<string[]> {
  const response = await api.get('/categories');
  return response.data.categories;
}

export async function fetchCurrencies(): Promise<string[]> {
  const response = await api.get('/currencies');
  return response.data.currencies;
}

export async function fetchStats() {
  const response = await api.get('/stats');
  return response.data;
}

export default api;
