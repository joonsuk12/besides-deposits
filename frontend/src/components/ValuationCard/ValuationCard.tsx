"use client";
// PER·PBR 카드. 이 종목의 PER·PBR을 같은 업종 주요 회사들의 중간값과 비교해 보여준다.
// 데이터는 스스로 불러온다 (차트 화면, 관심종목 화면 어디에 넣어도 한 줄로 쓰도록).

import Link from "next/link";
import { useEffect, useState } from "react";

import { fetchValuation, type Valuation } from "@/lib/api";
import styles from "./ValuationCard.module.css";

const won = (n: number) => Math.round(n).toLocaleString("ko-KR");
const times = (n: number | null) => (n === null ? "-" : `${n.toLocaleString("ko-KR", { maximumFractionDigits: 2 })}배`);

function Gap({ pct }: { pct: number | null }) {
  if (pct === null) return null;
  const cls = Math.abs(pct) < 15 ? styles["same"] : pct < 0 ? styles["low"] : styles["high"];
  const text = Math.abs(pct) < 15 ? "비슷" : pct >= 100 ? `약 ${(pct / 100 + 1).toFixed(1)}배` : `${pct > 0 ? "+" : ""}${pct.toFixed(0)}%`;
  return <span className={`${styles["gap"]} ${cls}`}>{text}</span>;
}

export default function ValuationCard({ code, compact = false }: { code: string; compact?: boolean }) {
  const [v, setV] = useState<Valuation | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setV(null);
    setFailed(false);
    fetchValuation(code).then(setV).catch(() => setFailed(true));
  }, [code]);

  if (failed) return <p className={styles["muted"]}>PER·PBR을 불러오지 못했습니다.</p>;
  if (!v) return <p className={styles["muted"]}>불러오는 중…</p>;
  if (!v.available) return <p className={styles["muted"]}>{v.message}</p>;

  const rows = [
    {
      label: "PER",
      hint: "주가 ÷ 주당순이익(EPS). 1년 이익의 몇 배에 주가가 매겨졌나",
      mine: v.per,
      industry: v.industry_per,
      gap: v.per_gap_pct,
      comment: v.per_comment,
      formula: v.price && v.eps ? `${won(v.price)}원 ÷ EPS ${won(v.eps)}원` : null,
    },
    {
      label: "PBR",
      hint: "주가 ÷ 주당순자산(BPS). 회사가 가진 순자산의 몇 배에 주가가 매겨졌나",
      mine: v.pbr,
      industry: v.industry_pbr,
      gap: v.pbr_gap_pct,
      comment: v.pbr_comment,
      formula: v.price && v.bps ? `${won(v.price)}원 ÷ BPS ${won(v.bps)}원` : null,
    },
  ];

  return (
    <div>
      {v.industry_name && <p className={styles["industry"]}>업종: {v.industry_name} · 비교 기준은 같은 업종 주요 {v.peers.length}곳의 중간값</p>}
      <div className={styles["rows"]}>
        {rows.map((r) => (
          <div key={r.label} className={styles["row"]}>
            <div className={styles["head"]}>
              <b title={r.hint}>{r.label}</b>
              <span className={styles["mine"]}>{times(r.mine)}</span>
              <span className={styles["vs"]}>업종 {times(r.industry)}</span>
              <Gap pct={r.gap} />
            </div>
            {r.comment && <p className={styles["comment"]}>{r.comment}</p>}
            {!compact && r.formula && <p className={styles["formula"]}>계산: {r.formula}</p>}
          </div>
        ))}
      </div>

      {!compact && v.cns_per !== null && (
        <p className={styles["formula"]}>증권사들이 예상한 올해 이익으로 계산하면 PER {times(v.cns_per)}예요.</p>
      )}
      <p className={styles["note"]}>
        낮다고 무조건 싼 것도, 높다고 무조건 비싼 것도 아니에요. 낮으면 성장 기대가 작거나 이익이 한때 늘어난 것일 수 있고,
        높으면 앞으로 많이 클 거라는 기대가 담겨 있을 수 있어요.
      </p>

      {!compact && v.peers.length > 0 && (
        <details className={styles["peers"]}>
          <summary>비교한 회사 {v.peers.length}곳 보기</summary>
          <table>
            <thead>
              <tr>
                <th>회사</th>
                <th>PER</th>
                <th>PBR</th>
              </tr>
            </thead>
            <tbody>
              {v.peers.map((p) => (
                <tr key={p.code}>
                  <td>
                    <Link href={`/${p.code}`}>{p.name}</Link>
                  </td>
                  <td>{p.per === null ? "적자" : times(p.per)}</td>
                  <td>{times(p.pbr)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </div>
  );
}
