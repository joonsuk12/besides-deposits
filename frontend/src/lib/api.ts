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

export type Report = {
  nid: string;
  item_code: string;
  item_name: string;
  broker: string;
  title: string;
  write_date: string;
  url: string;
  opinion: string | null;
  opinion_type: "buy" | "neutral" | "sell" | null;
  goal_price: number | null;
  prev_goal_price: number | null;
  goal_change: "상향" | "하향" | "유지" | "처음" | null;
  close: number | null;
  gap_pct: number | null;
  headline: string | null;
  points: string[];
  risks: string[];
  terms: { term: string; meaning: string }[];
  // Claude가 초보 말투로 다시 쓴 요약 (아직 없으면 null)
  easy: { one_liner: string; story: string; watch_out: string | null } | null;
};

export type ReportFeed = { date: string; total: number; reports: Report[] };

export type News = {
  id: string;
  stock_code: string;
  office: string;
  title: string;
  url: string;
  published_at: string;
  date: string;
  summary: string;
  cluster_size: number;
  related_titles: string[];
  tone: "good" | "bad" | "neutral";
  topics: string[];
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

export const fetchReportFeed = (date?: string) => request<ReportFeed>(`/reports${date ? `?date=${date}` : ""}`);
export const fetchStockReports = (code: string, limit = 10) =>
  request<Report[]>(`/reports/stock/${code}?limit=${limit}`);
export const fetchStockNews = (code: string, days = 90) => request<News[]>(`/news/stock/${code}?days=${days}`);

export type Valuation = {
  available: boolean;
  message: string | null;
  price: number | null;
  price_date: string | null;
  eps: number | null;
  bps: number | null;
  per: number | null;
  pbr: number | null;
  cns_per: number | null;
  industry_name: string | null;
  industry_per: number | null;
  industry_pbr: number | null;
  per_gap_pct: number | null;
  pbr_gap_pct: number | null;
  per_comment: string | null;
  pbr_comment: string | null;
  focus: "per" | "pbr" | "both" | "none" | null;
  focus_title: string | null;
  focus_reason: string | null;
  focus_also: string[];
  focus_caution: string | null;
  peers: { code: string; name: string; per: number | null; pbr: number | null }[];
};

export const fetchValuation = (code: string) => request<Valuation>(`/valuation/stock/${code}`);

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

export type Disclosure = {
  rcept_no: string;
  stock_code: string;
  corp_name: string;
  title: string;
  filer: string;
  date: string;
  url: string;
  category: string;
  level: "warn" | "good" | "key" | "info";
  explain: string;
  why: string | null;
  checks: string[];
  is_correction: boolean;
  by_company: boolean;
};

export type DisclosureList = { available: boolean; message: string | null; items: Disclosure[] };

export const fetchStockDisclosures = (code: string, days = 180) =>
  request<DisclosureList>(`/disclosures/stock/${code}?days=${days}`);
