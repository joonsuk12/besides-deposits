'use client'
// 소개 페이지 (주소: /intro). 처음 온 사람에게 서비스를 소개하는 랜딩 화면. NewStocks 랜딩을 옮기고 문구를 바꿨다.
// 혼자 쓸 때는 홈(/)이 첫 화면이고, 나중에 서비스를 공개하면 로그인 전 첫 화면으로 쓴다.
import { BRAND } from "@/lib/brand";
import styles from './intro.module.css'
import LandingView from '@/components/LandingView/LandingView'
import Footer from '@/components/Footer/Footer'
import graphimg from '@/assets/graphimg.png'
import Image from 'next/image';
import { HiArrowNarrowRight } from 'react-icons/hi';
import { goToStart } from '@/lib/api';

export default function IntroPage() {
  return (
    <div className={styles.main}>
      <div>
        <div className={styles["landing-main-image"]}>
        <div className={styles["chart"]}>
          <Image
            src={graphimg}
            alt="stockimg"
            priority
          />
        </div>
        </div>
        <div className={styles["landing-main-container"]}>
          <div className={styles["title-animation"]}>
            <div className={styles["title-mini"]}>주식 초보를 위한 첫 나들이 🚶</div>
            <div className={styles["title-main"]}><span>{BRAND.ko}</span></div>
            <div className={styles["title"]}><span>차트</span> · <span>뉴스</span> · <span>리포트</span>를 쉽게</div>
          </div>
          <div className={styles["head-description"]}>
            <div>차트 위에 그날의 뉴스를, 어려운 증권사 리포트는 쉬운 요약으로</div>
            <div>처음이어도 천천히 둘러보세요</div>
          </div>
          <div className={styles["title-botton-box"]}>
            <div className={styles["Button-width"]}>
              <button onClick={goToStart} className={styles["button-box"]} style={{ color: "#4FE7B0", border: "2px solid #4FE7B0" }}>
                <div>시작하기</div>
                <HiArrowNarrowRight size="14"/>
              </button>
            </div>
          </div>
        </div>
      </div>

      <LandingView />

      <Footer />
    </div>
  )
}
