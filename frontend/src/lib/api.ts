// 백엔드(FastAPI)를 부르는 함수 모음. 화면 코드는 여기 있는 함수만 쓴다.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8100";

export type Stock = {
  code: string;
  name: string;
  market: string; // KOSPI / KOSDAQ / ETF
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

export type WatchlistItem = {
  code: string;
  name: string;
  market: string;
  date: string | null;
  close: number | null;
  change: number | null;
  change_pct: number | null;
};

async function request<T>(path: string, method = "GET"): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { method });
  if (!res.ok) throw new Error(`요청 실패 (${res.status}): ${path}`);
  return res.json();
}

export const fetchStocks = () => request<Stock[]>("/stocks");
export const fetchStock = (code: string) => request<Stock>(`/stocks/${code}`);
export const fetchWatchlist = () => request<WatchlistItem[]>("/stocks/watchlist");
export const fetchPrices = (code: string, days: number) =>
  request<Price[]>(`/stocks/${code}/prices?days=${days}`);
export const addWatch = (code: string) => request<Stock>(`/stocks/${code}/watch`, "PUT");
export const removeWatch = (code: string) => request<Stock>(`/stocks/${code}/watch`, "DELETE");

// 종목 로고 (NewStocks와 같은 출처). 없는 종목은 회색 원으로 보인다.
export const stockLogoUrl = (code: string) =>
  `https://file.alphasquare.co.kr/media/images/stock_logo/kr/${code}.png`;

// "시작하기": 관심 종목이 있으면 그 종목 차트로, 없으면 삼성전자로 간다.
export async function goToStart() {
  let code = "005930";
  try {
    const list = await fetchWatchlist();
    if (list.length > 0) code = list[list.length - 1].code;
  } catch {
    // 백엔드가 꺼져 있어도 차트 화면으로는 이동한다
  }
  window.location.href = `/${code}`;
}
