// 백엔드(FastAPI)를 부르는 함수 모음. 화면 코드는 여기 있는 함수만 쓴다.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8100";

export type Stock = {
  code: string;
  name: string;
  is_watched: boolean;
};

export type Price = {
  date: string; // "2026-11-11"
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) throw new Error(`요청 실패 (${res.status}): ${path}`);
  return res.json();
}

export const fetchStocks = () => get<Stock[]>("/stocks");

export const fetchPrices = (code: string, days: number) =>
  get<Price[]>(`/stocks/${code}/prices?days=${days}`);
