// 도움말 (주소: /guide). 이 서비스의 기능과 화면 읽는 법을 한곳에 모은다.
// 차트 화면의 "캔들 읽는 법", 공시의 "꼬리표 뜻"처럼 화면마다 흩어진 설명의 원본이다.
// 나중에 서비스를 공개하면 소개 페이지(/intro)와 함께 처음 온 사람의 안내서가 된다.

import Link from "next/link";

import SiteNote from "@/components/SiteNote/SiteNote";
import styles from "./guide.module.css";

const TOC = [
  { id: "what", title: "이 서비스로 할 수 있는 것" },
  { id: "chart", title: "차트 읽는 법" },
  { id: "news", title: "뉴스 보는 법" },
  { id: "report", title: "증권사 리포트 보는 법" },
  { id: "disclosure", title: "공시와 꼬리표" },
  { id: "valuation", title: "PER·PBR 쉽게" },
  { id: "data", title: "데이터는 언제 어디서 오나" },
];

export default function GuidePage() {
  return (
    <div className={styles["page"]}>
      <h1>도움말</h1>
      <p className={styles["lead"]}>
        주식이 처음인 사람이 차트·뉴스·증권사 리포트·공시를 쉽게 훑어볼 수 있게 만든 서비스예요. 화면마다 무엇을 보면 되는지
        정리했어요.
      </p>

      <div className={styles["layout"]}>
        <nav className={styles["toc"]} aria-label="목차">
          <p>목차</p>
          <ol>
            {TOC.map((t) => (
              <li key={t.id}>
                <a href={`#${t.id}`}>{t.title}</a>
              </li>
            ))}
          </ol>
        </nav>

        <div className={styles["body"]}>
          <section id="what">
            <h2>1. 이 서비스로 할 수 있는 것</h2>
            <ul>
              <li>
                <b>홈</b>: 관심종목의 오늘 등락과 최근 3일 새 소식(중요 공시·리포트·많이 다뤄진 뉴스)을 한 화면에서 봐요.
              </li>
              <li>
                <b>차트</b>: 종목을 검색하면 캔들 차트 위에 뉴스(N)·리포트(R)·중요 공시(D)가 나온 날이 표시돼요. 날짜를 누르면 그날
                무슨 일이 있었는지 차트 아래에 나와요.
              </li>
              <li>
                <b>오늘의 리포트</b>: 그날 나온 증권사 리포트를 초보 말투 한 줄 요약과 함께 모아 봐요.
              </li>
              <li>
                <b>관심종목</b>: 차트 화면에서 종목 이름 옆 ☆을 누르면 담겨요. 종목마다 최신 리포트·뉴스·공시·주가 수준을 모아
                봐요.
              </li>
            </ul>
          </section>

          <section id="chart">
            <h2>2. 차트 읽는 법</h2>
            <ul>
              <li>
                막대 하나가 하루예요(일봉). <b className="up">빨간 막대</b>는 그날 시작한 가격보다 오른 채로 끝난 날,{" "}
                <b className="down">파란 막대</b>는 내린 채로 끝난 날이에요. 한국 증시 관례라 미국 사이트와 색이 반대예요.
              </li>
              <li>막대의 두꺼운 부분은 시작 가격(시가)과 끝 가격(종가) 사이, 위아래 가는 선은 그날의 가장 높은·낮은 가격이에요.</li>
              <li>아래쪽 막대는 거래량이에요. 길수록 그날 사고판 주식이 많았다는 뜻이에요.</li>
              <li>
                차트를 넓게 보면(줌 아웃) 막대 하나가 일주일·한 달·일 년으로 바뀌어요(주봉·월봉·연봉). 긴 흐름을 볼 때 편해요.
              </li>
              <li>
                <b className={styles["n"]}>N</b> 뉴스가 있는 날 · <b className={styles["r"]}>R</b> 증권사 리포트가 나온 날 ·{" "}
                <b className={styles["d"]}>D</b> 중요 공시가 나온 날이에요.
              </li>
            </ul>
          </section>

          <section id="news">
            <h2>3. 뉴스 보는 법</h2>
            <ul>
              <li>
                <b>기사 N건</b>: 같은 내용을 다룬 기사 수예요. 여러 언론사가 함께 다룰수록 중요한 소식일 가능성이 커요.
              </li>
              <li>
                <b>좋은 소식(추정)·나쁜 소식(추정)</b>: 제목과 본문의 단어로 분위기를 짐작한 거예요. 틀릴 수 있으니 참고만 하세요.
              </li>
              <li>#실적, #수주 같은 꼬리표는 기사가 무엇에 관한 것인지 보여줘요.</li>
            </ul>
          </section>

          <section id="report">
            <h2>4. 증권사 리포트 보는 법</h2>
            <ul>
              <li>
                <b>🧒 쉽게 말하면</b>: 리포트를 초보 말투로 다시 쓴 한 줄이에요. &quot;자세히&quot;를 누르면 풀어 쓴 설명과 주의할
                점이 나와요.
              </li>
              <li>
                <b>투자의견</b>: 증권사가 붙인 의견이에요. 한국 증권사는 대부분 &quot;매수&quot;를 붙이니, 의견보다 근거를 보는 게
                좋아요.
              </li>
              <li>
                <b>목표주가 ▲ 상향 / ▼ 하향</b>: 같은 증권사의 이전 목표주가와 비교한 거예요. 목표주가를 내렸다면 기대가 줄었다는
                뜻이에요.
              </li>
              <li>
                <b>최근 종가와 차이</b>: 지금 주가가 목표주가까지 얼마나 남았는지예요. 차이가 크다고 꼭 오르는 건 아니에요.
              </li>
            </ul>
          </section>

          <section id="disclosure">
            <h2>5. 공시와 꼬리표</h2>
            <p>공시는 회사가 법에 따라 알려야 하는 중요한 일이에요. 공시 제목을 보고 아래 꼬리표를 붙여요.</p>
            <ul>
              <li>
                <b className="up">좋은 소식 (보통)</b>: 배당, 자사주 매입·소각, 큰 공급 계약처럼 주주에게 보통 좋게 받아들여지는 공시
              </li>
              <li>
                <b className="down">나쁜 소식 (보통)</b>: 유상증자, 전환사채, 계약 해지, 소송·사고처럼 주가에 부담이 될 수 있는 공시
              </li>
              <li>
                <b className={styles["d"]}>내용 확인</b>: 실적 발표, 합병·분할, 시설 투자처럼 큰 일이지만 좋을지 나쁠지는 숫자와
                조건을 봐야 아는 공시
              </li>
              <li>
                <b>참고</b>: 정기 보고서, 임원 지분 보고처럼 자주 나오는 공시. 목록에서는 건수만 보여줘요.
              </li>
            </ul>
            <p className={styles["sub"]}>
              &quot;보통&quot;은 제목만 보고 붙였다는 뜻이에요. 공시의 &quot;자세히&quot;를 누르면 원문에서 무엇을 확인할지 나와요.
            </p>
          </section>

          <section id="valuation">
            <h2>6. PER·PBR 쉽게</h2>
            <ul>
              <li>
                <b>PER</b> = 주가 ÷ 1주당 1년 이익. &quot;회사가 1년에 버는 돈의 몇 배에 주가가 매겨졌나&quot;예요. 적자면
                계산하지 않아요.
              </li>
              <li>
                <b>PBR</b> = 주가 ÷ 1주당 순자산. &quot;회사가 가진 재산(빚을 뺀 것)의 몇 배에 주가가 매겨졌나&quot;예요.
              </li>
              <li>
                같은 업종 주요 회사들의 중간값과 비교해요. 낮다고 무조건 싼 것도, 높다고 무조건 비싼 것도 아니에요.
              </li>
              <li>
                업종마다 주로 보는 지표가 달라요. 은행·지주회사는 PBR, 소프트웨어·화장품은 PER, 반도체는 업황에 따라 둘 다. 차트 화면
                &quot;주가 수준&quot; 탭에 업종별 안내가 나와요.
              </li>
              <li>
                &quot;연간 흐름&quot; 탭에서는 최근 3년과 올해 예상치의 PER·PBR, 매출·영업이익을 볼 수 있고, &quot;회사 소개&quot;
                탭에서는 회사가 무슨 일을 하는지 볼 수 있어요.
              </li>
            </ul>
          </section>

          <section id="data">
            <h2>7. 데이터는 언제 어디서 오나</h2>
            <ul>
              <li>주가: KRX 데이터(pykrx·FinanceDataReader). 평일 장 마감 뒤 하루 한 번 받아요.</li>
              <li>공시: 금융감독원 OpenDART. 6시간마다 새로 확인해요.</li>
              <li>뉴스·증권사 리포트·기업 지표: 네이버 증권. 화면을 열 때와 매일 저녁 정해진 시간에 받아요.</li>
              <li>리포트의 &quot;쉽게 말하면&quot; 요약은 평일 저녁에 Claude가 써서 저장해요. 아직 요약이 없는 리포트도 있어요.</li>
            </ul>
            <p className={styles["sub"]}>
              처음 온 사람을 위한 짧은 소개는 <Link href="/intro">서비스 소개</Link>에 있어요.
            </p>
          </section>
        </div>
      </div>

      <SiteNote />
    </div>
  );
}
