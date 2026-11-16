'use client';
import { BRAND } from "@/lib/brand";
import styles from './landingfooter.module.css'
import { useEffect, useState } from 'react';
import Link from 'next/link';
import Button from '../../Button/Button'

export default function LandingFooter() {
  const [ isVisible, setIsVisible ] = useState(false);

  useEffect(() => {
    // 스크롤 이벤트 리스너 추가
    const handleScroll = () => {
        const scrollY = window.scrollY;

        if (scrollY >= 1300) {
            setIsVisible(true);
        } else {
            setIsVisible(false);
        }
    };

    window.addEventListener('scroll', handleScroll);

    return () => {
        window.removeEventListener('scroll', handleScroll);
    };
  }, [])

  return (
    <>
      <div className={`${styles["footer"]} ${styles['scroll-animation']} ${isVisible ? styles['footer-animation-show'] : ''}`}>
        <div className={styles["footer-contents"]}>
          <div className={styles["footer-box"]}>
            <div className={styles["footer-title"]}><span>{BRAND.ko}</span></div>
            <div className={styles["footer-content"]}>주식 초보의 첫 나들이길</div>
            <div className={styles["footer-content"]}>혼자 쓰는 개인용 서비스</div>
          </div>

          <div className={styles["footer-box"]}>
            <div className={styles["footer-title"]}><span>바로</span> 가기</div>
            <div className={styles["Button-width"]}><Link href="/watchlist"><Button text="내 관심종목" kindof="arrow" highlight={false}></Button></Link></div>
          </div>


          <div>
            <div className={styles["footer-title"]}>알아두세요</div>
            <div className={styles["footer-content"]}>리포트 요약은 내용 전달용입니다</div>
            <div className={styles["footer-content"]}>매수·매도를 권유하지 않습니다</div>
          </div>
        </div>
      </div>

    </>
  )
}