"use client";
// ETF 정보 카드. ETF는 회사가 아니라 여러 자산을 담은 바구니라 PER·PBR 대신 이것을 보여준다.
// 탭: 한눈에(따라가는 지수·보수·괴리율·수익률) / 담긴 것(종목 TOP10·자산·업종 비중) / 돈의 흐름(자금 유입·분배금)
// compact: 관심종목 화면용 한 줄 요약

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchEtf, type Etf, type EtfWeight } from "@/lib/api";
import styles from "./EtfCard.module.css";

const TABS = [
  { key: "basic", label: "🧺 한눈에" },
  { key: "holdings", label: "📦 담긴 것" },
  { key: "flow", label: "💸 돈의 흐름" },
] as const;
type TabKey = (typeof TABS)[number]["key"];

const pct = (v: number | string | null, sign = true) => {
  if (v === null || v === "" || v === undefined) return "-";
  const n = typeof v === "number" ? v : Number(v);
  if (Number.isNaN(n)) return String(v);
  return `${sign && n > 0 ? "+" : ""}${n.toLocaleString("ko-KR", { maximumFractionDigits: 2 })}%`;
};
const tone = (v: number | string | null) => (typeof v === "number" ? (v > 0 ? "up" : v < 0 ? "down" : "") : "");

function Bars({ items, linkable = false }: { items: EtfWeight[]; linkable?: boolean }) {
  const max = Math.max(...items.map((i) => i.weight), 1);
  return (
    <ul className={styles["bars"]}>
      {items.map((i) => (
        <li key={i.name}>
          <span className={styles["bar-name"]}>
            {linkable && i.code ? <Link href={`/${i.code}`}>{i.name}</Link> : i.name}
          </span>
          {i.weight > 0 ? (
            <>
              <span className={styles["bar-track"]}>
                <span className={styles["bar-fill"]} style={{ width: `${(i.weight / max) * 100}%` }} />
              </span>
              <span className={styles["bar-val"]}>{pct(i.weight, false)}</span>
            </>
          ) : (
            <span className={styles["bar-val"]}>비중 정보 없음</span>
          )}
        </li>
      ))}
    </ul>
  );
}

export default function EtfCard({ code, compact = false }: { code: string; compact?: boolean }) {
  const [e, setE] = useState<Etf | null>(null);
  const [failed, setFailed] = useState(false);
  const [tab, setTab] = useState<TabKey>("basic");

  useEffect(() => {
    setE(null);
    setFailed(false);
    fetchEtf(code)
      .then(setE)
      .catch(() => setFailed(true));
  }, [code]);

  // 한 줄 요약(compact)은 다른 문단·버튼 안에 들어가므로 <p> 대신 <span>을 쓴다 (<p> 안에 <p>는 HTML 오류)
  const Msg = ({ text }: { text: string | null }) =>
    compact ? <span className={styles["compact"]}>{text}</span> : <p className={styles["muted"]}>{text}</p>;
  if (failed) return <Msg text="ETF 정보를 불러오지 못했습니다." />;
  if (!e) return <Msg text="불러오는 중…" />;
  if (!e.available) return <Msg text={e.message} />;

  const y1 = e.returns.find((r) => r.label === "1년");

  if (compact)
    return (
      <span className={styles["compact"]}>
        <b>{e.base_index}</b> 추종 · 보수 연 {e.total_fee}% · 1년{" "}
        <span className={tone(y1?.value ?? null)}>{pct(y1?.value ?? null)}</span>
        {e.holdings[0] && ` · 가장 많이 담은 것: ${e.holdings[0].name}`}
      </span>
    );

  return (
    <div>
      <div className={styles["tabs"]} role="tablist">
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            className={tab === t.key ? styles["on"] : ""}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "basic" && (
        <>
          <p className={styles["lead"]}>
            <b>{e.base_index}</b>{e.base_index?.endsWith("지수") ? "" : " 지수"}를 따라가는 ETF예요. {e.issuer && `운용사 ${e.issuer}.`}{" "}
            {e.listed_date && `${e.listed_date.slice(0, 4)}년 상장.`} {e.total_nav && `순자산 ${e.total_nav}.`}
          </p>
          <dl className={styles["facts"]}>
            <div>
              <dt title="1년 동안 맡기면 떼어 가는 수수료">총보수</dt>
              <dd>연 {e.total_fee ?? "-"}%</dd>
            </div>
            <div>
              <dt title="ETF 가격과 실제 담긴 자산 가치(NAV)의 차이">괴리율</dt>
              <dd>{pct(e.deviation_rate)}</dd>
            </div>
            <div>
              <dt title="따라가는 지수와 얼마나 다르게 움직였는지">추적오차</dt>
              <dd>{e.tracking_error ?? "-"}%</dd>
            </div>
          </dl>
          <ul className={styles["notes"]}>
            {e.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
          <table className={styles["returns"]}>
            <thead>
              <tr>
                {e.returns.map((r) => (
                  <th key={r.label}>{r.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                {e.returns.map((r) => (
                  <td key={r.label} className={tone(r.value)}>
                    {pct(r.value)}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
          {e.summary && <p className={styles["muted"]}>운용 목표: {e.summary}</p>}
        </>
      )}

      {tab === "holdings" && (
        <>
          {e.holdings.length > 0 && (
            <>
              <h4 className={styles["sub-h"]}>많이 담은 것 TOP {e.holdings.length}</h4>
              <Bars items={e.holdings} linkable />
            </>
          )}
          {e.assets.length > 0 && (
            <>
              <h4 className={styles["sub-h"]}>자산 종류</h4>
              <Bars items={e.assets} />
            </>
          )}
          {e.sectors.length > 0 && (
            <>
              <h4 className={styles["sub-h"]}>업종</h4>
              <Bars items={e.sectors.slice(0, 8)} />
            </>
          )}
          <p className={styles["muted"]}>
            종목 이름을 누르면 그 종목 차트로 가요. 비중이 한두 종목에 몰려 있으면 그 종목 주가에 크게 흔들려요.
          </p>
        </>
      )}

      {tab === "flow" && (
        <>
          <h4 className={styles["sub-h"]}>투자자 돈이 들어왔나 (순유입)</h4>
          {e.inflows.length === 0 && <p className={styles["muted"]}>정보가 없어요.</p>}
          <dl className={styles["facts"]}>
            {e.inflows.map((f) => (
              <div key={f.label}>
                <dt>최근 {f.label}</dt>
                <dd className={f.value?.startsWith("-") ? "down" : "up"}>{f.value}</dd>
              </div>
            ))}
          </dl>
          <h4 className={styles["sub-h"]}>분배금 (ETF가 주는 배당)</h4>
          <p className={styles["lead"]}>
            {e.dividend_yield
              ? `최근 1년 분배금은 가격의 약 ${e.dividend_yield}%예요.${e.dividend_months ? ` 올해는 ${e.dividend_months}에 줬어요.` : ""}`
              : "최근 1년 동안 분배금이 없었어요. 금·원자재 ETF는 보통 분배금이 없어요."}
          </p>
          <p className={styles["muted"]}>
            순유입은 이 ETF를 새로 산 돈에서 판 돈을 뺀 것이에요. 많이 들어온다고 오른다는 뜻은 아니지만, 사람들의
            관심을 보여줘요.
          </p>
        </>
      )}
    </div>
  );
}
