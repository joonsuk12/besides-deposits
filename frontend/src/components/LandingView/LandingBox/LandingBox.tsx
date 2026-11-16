'use client'
// NewStocks의 랜딩 섹션(01·02·03) 화면을 옮긴 것. 문구는 이 서비스(차트·뉴스 / 리포트 요약 / 관심종목)에 맞게 바꿨다.
import { BRAND } from "@/lib/brand";
import styles from './landingbox.module.css'
import { useEffect, useState } from 'react';
import Image from 'next/image';
import stockimg from '@/assets/stockimg.png'
import AllCardsImage from './AllCardsImage/AllCardsImage'
import { HiArrowNarrowRight } from 'react-icons/hi';
import { goToStart } from '@/lib/api';

type Props = {
  position: number | 0,
  right: 1 | 2 | 3
}

export default function LandingBox({ position, right }: Props) {
  const [ isVisible, setIsVisible ] = useState(false);

  useEffect(() => {
    // 스크롤 이벤트 리스너 추가
    const handleScroll = () => {
        const scrollY = window.scrollY;

        if (scrollY >= position) {
            setIsVisible(true);
        } else {
            setIsVisible(false);
        }
    };

    window.addEventListener('scroll', handleScroll);

    return () => {
        window.removeEventListener('scroll', handleScroll);
    };
  // eslint-disable-next-line
  }, []);

  return (
    <>
       {right === 1 ? (
        <>
          <div className={styles["landing-containers-num"]}>01</div>
          <div className={styles["landing-containers"]}>
            <div className={styles["content-box"]}>
              <div className={`${styles['title']} ${styles['scroll-animation']} ${isVisible ? styles['title-animation-show'] : ''}`}><span>차트</span>와 <span>뉴스</span>를 한눈에</div>
              <div className={`${styles['description']} ${styles['scroll-animation']} ${isVisible ? styles['description-animation-show'] : ''}`} >
                <div>코스피·코스닥·ETF 전 종목 검색 (초성 검색도 돼요)</div>
                <div>캔들 차트에 마우스를 올리면 그날의 가격이 보여요</div>
                <div>날짜를 누르면 그날 나온 뉴스를 함께 확인</div>
                <div>빨간 막대·파란 막대 읽는 법부터 차근차근</div>
              </div>
            </div>
            <div className={`${styles['stock-image-box']} ${styles['scroll-animation']} ${isVisible ? styles['title-animation-show'] : ''}`}>
              <Image
                src={stockimg}
                alt="stockimg"
              />
            </div>
          </div>
        </>
      ) : right === 2 ? (
        <>
          <div className={`${styles["landing-containers"]} ${styles['scroll-animation']} ${isVisible ? styles['title-animation-show'] : ''}`}>
          <div className={styles["landing-containers-num"]} id={styles["right-num"]}>02</div>
            <div className={styles["landing-iamge-box"]}>
              <AllCardsImage />
            </div>

            <div className={styles["content-box"]} id={styles["right-item"]}>
              <div className={`${styles['title']} ${styles['scroll-animation']} ${isVisible ? styles['title-animation-show'] : ''}`} id={styles["right-desc"]}><span>증권사 리포트</span>를 쉬운 말로</div>
              <div className={`${styles["description"]} ${styles['scroll-animation']} ${isVisible ? styles['description-animation-show'] : ''}`} id={styles["right-desc"]}>
                <div>매일 나오는 애널리스트 리포트를 한 줄 결론으로</div>
                <div>목표주가가 올랐는지 내렸는지, 그 이유는 무엇인지</div>
                <div>처음 보는 용어는 쉬운 설명을 곁들여서</div>
              </div>
              <div id={styles["right-item"]} style={{ width: "120px" }}>
              </div>
            </div>
          </div>
        </>
      ) : right === 3 ? (
        <>
          <div className={`${styles["landing-containers"]} ${styles['scroll-animation']} ${isVisible ? styles['title-animation-show'] : ''}`}>
          <div className={styles["landing-containers-num"]}>03</div>
            <div className={styles["content-box"]}>
              <div className={`${styles['title']} ${styles['scroll-animation']} ${isVisible ? styles['title-animation-show'] : ''}`}><span>내 관심종목</span> 모아보기</div>
              <div className={`${styles['description']} ${styles['scroll-animation']} ${isVisible ? styles['description-animation-show'] : ''}`} >
                <div>차트에서 ☆ 한 번이면 관심종목에 쏙</div>
                <div>종목마다 최근 리포트와 공시를 한곳에서</div>
                <div>실적·증자 같은 중요한 공시는 무엇이 중요한지 쉽게</div>
              </div>
            </div>
            <div className={`${styles['value-image-box']} ${styles['scroll-animation']} ${isVisible ? styles['title-animation-show'] : ''}`}>
              {/* 관심종목 화면을 흉내 낸 예시 그림 */}
              <div className={styles['watch-mock']}>
                {[['반도체 A사', '+2.31%', 'up'], ['기계 B사', '-0.84%', 'down'], ['금융 D사', '+0.52%', 'up']].map(([name, pct, tone]) => (
                  <div key={name} className={styles['watch-mock-row']}>
                    <span>⭐ {name}</span>
                    <span className={tone}>{pct}</span>
                    <span className={styles['watch-mock-tags']}>📄 리포트 2 · 📢 공시 1</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className={styles["start"]}>
            <div className={styles["Button-width"]}>
              <button onClick={goToStart} className={styles["button-box"]} style={{ color: "#4FE7B0", border: "2px solid #4FE7B0" }}>
                  <div>{BRAND.ko} 시작하기</div>
                  <HiArrowNarrowRight size="14"/>
              </button>
            </div>
          </div>
        </>
      ) : null}
    </>
  )
}
