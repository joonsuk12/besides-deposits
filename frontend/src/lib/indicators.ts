// 보조지표 계산. 차트에 보이는 봉(일·주·월·연)의 종가 배열을 받아 같은 길이의 배열을 돌려준다.
// 계산할 수 없는 앞부분(기간이 덜 찬 곳)은 null.
// 서버를 거치지 않고 화면에서 바로 계산한다 (일봉 10년치 = 약 2,500개라 순식간).

export type Series = (number | null)[];

/** 단순 이동평균: 최근 n개 종가의 평균 */
export function sma(values: number[], n: number): Series {
  const out: Series = [];
  let sum = 0;
  for (let i = 0; i < values.length; i++) {
    sum += values[i];
    if (i >= n) sum -= values[i - n];
    out.push(i >= n - 1 ? sum / n : null);
  }
  return out;
}

/** 지수 이동평균: 최근 값에 더 큰 무게를 둔 평균 (MACD 계산용) */
export function ema(values: Series, n: number): Series {
  const out: Series = [];
  const k = 2 / (n + 1);
  let prev: number | null = null;
  let seed: number[] = [];
  for (const v of values) {
    if (v === null) {
      out.push(null);
      continue;
    }
    if (prev === null) {
      // 처음 n개는 단순 평균으로 시작값을 만든다
      seed.push(v);
      if (seed.length === n) {
        prev = seed.reduce((a, b) => a + b, 0) / n;
        seed = [];
        out.push(prev);
      } else out.push(null);
      continue;
    }
    prev = v * k + prev * (1 - k);
    out.push(prev);
  }
  return out;
}

/** 볼린저밴드: 가운데 n일 이동평균, 위아래로 표준편차 k배 */
export function bollinger(values: number[], n = 20, k = 2): { mid: Series; upper: Series; lower: Series } {
  const mid = sma(values, n);
  const upper: Series = [];
  const lower: Series = [];
  for (let i = 0; i < values.length; i++) {
    const m = mid[i];
    if (m === null) {
      upper.push(null);
      lower.push(null);
      continue;
    }
    let v = 0;
    for (let j = i - n + 1; j <= i; j++) v += (values[j] - m) ** 2;
    const sd = Math.sqrt(v / n);
    upper.push(m + k * sd);
    lower.push(m - k * sd);
  }
  return { mid, upper, lower };
}

/** RSI(상대강도지수): 최근 n개 동안 오른 폭이 전체 움직임의 몇 %인지. 70 이상 과열, 30 이하 침체 */
export function rsi(values: number[], n = 14): Series {
  const out: Series = [null];
  let gain = 0;
  let loss = 0;
  for (let i = 1; i < values.length; i++) {
    const ch = values[i] - values[i - 1];
    const g = Math.max(ch, 0);
    const l = Math.max(-ch, 0);
    if (i <= n) {
      gain += g;
      loss += l;
      if (i < n) {
        out.push(null);
        continue;
      }
      gain /= n;
      loss /= n;
    } else {
      // 와일더 방식 평균 (증권사 앱과 같은 방식)
      gain = (gain * (n - 1) + g) / n;
      loss = (loss * (n - 1) + l) / n;
    }
    out.push(loss === 0 ? 100 : 100 - 100 / (1 + gain / loss));
  }
  return out;
}

/** MACD: 12개 지수평균 − 26개 지수평균. signal은 MACD의 9개 지수평균, hist는 둘의 차이 */
export function macd(values: number[], fast = 12, slow = 26, signalN = 9): { macd: Series; signal: Series; hist: Series } {
  const f = ema(values, fast);
  const s = ema(values, slow);
  const line: Series = values.map((_, i) => (f[i] !== null && s[i] !== null ? (f[i] as number) - (s[i] as number) : null));
  const signal = ema(line, signalN);
  const hist: Series = line.map((v, i) => (v !== null && signal[i] !== null ? v - (signal[i] as number) : null));
  return { macd: line, signal, hist };
}

/** 스토캐스틱(슬로우): 최근 n개 봉의 최고·최저 사이에서 지금 종가가 어디쯤인지(0~100). %K를 k번, %D를 d번 평균 */
export function stochastic(
  highs: number[],
  lows: number[],
  closes: number[],
  n = 14,
  k = 3,
  d = 3,
): { k: Series; d: Series } {
  const fast: Series = closes.map((c, i) => {
    if (i < n - 1) return null;
    const hh = Math.max(...highs.slice(i - n + 1, i + 1));
    const ll = Math.min(...lows.slice(i - n + 1, i + 1));
    return hh === ll ? 50 : ((c - ll) / (hh - ll)) * 100;
  });
  const avg = (vals: Series, m: number): Series =>
    vals.map((_, i) => {
      const win = vals.slice(Math.max(0, i - m + 1), i + 1);
      return win.length < m || win.some((v) => v === null) ? null : (win as number[]).reduce((a, b) => a + b, 0) / m;
    });
  const slowK = avg(fast, k);
  return { k: slowK, d: avg(slowK, d) };
}

/**
 * 일목균형표. 길이는 봉 수 + shift (선행스팬은 앞으로 shift칸 밀려 미래 자리까지 그린다).
 * - 전환선: 최근 9개 (최고+최저)/2   - 기준선: 최근 26개 (최고+최저)/2
 * - 선행스팬1: (전환선+기준선)/2를 26칸 앞으로   - 선행스팬2: 최근 52개 (최고+최저)/2를 26칸 앞으로
 * - 후행스팬: 종가를 26칸 뒤로
 */
export function ichimoku(highs: number[], lows: number[], closes: number[], shift = 26) {
  const mid = (n: number): Series =>
    closes.map((_, i) =>
      i < n - 1 ? null : (Math.max(...highs.slice(i - n + 1, i + 1)) + Math.min(...lows.slice(i - n + 1, i + 1))) / 2,
    );
  const len = closes.length + shift;
  const pad = (vals: Series) => [...vals, ...Array<null>(len - vals.length).fill(null)];
  const tenkan = mid(9);
  const kijun = mid(26);
  const spanB = mid(52);
  const spanA: Series = Array<null>(shift).fill(null);
  const spanB2: Series = Array<null>(shift).fill(null);
  for (let i = 0; i < closes.length; i++) {
    spanA.push(tenkan[i] !== null && kijun[i] !== null ? ((tenkan[i] as number) + (kijun[i] as number)) / 2 : null);
    spanB2.push(spanB[i]);
  }
  const lagging: Series = pad(closes.slice(shift));
  return { tenkan: pad(tenkan), kijun: pad(kijun), spanA, spanB: spanB2, lagging };
}
