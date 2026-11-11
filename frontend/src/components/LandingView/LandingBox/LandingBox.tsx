'use client'
// NewStocks의 랜딩 섹션(01·02·03)을 그대로 옮긴 것. 로그인 확인만 빠졌다.
import styles from './landingbox.module.css'
import { useEffect, useState } from 'react';
import Image from 'next/image';
import stockimg from '@/assets/stockimg.png'
import valueimg from '@/assets/valueimg.png'
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
              <div className={`${styles['title']} ${styles['scroll-animation']} ${isVisible ? styles['title-animation-show'] : ''}`}><span>주식차트</span>,<span>뉴스</span>,<span>오답노트</span>를 한눈에</div>
              <div className={`${styles['description']} ${styles['scroll-animation']} ${isVisible ? styles['description-animation-show'] : ''}`} >
                <div>국내의 모든 주식 종목 정보 및 뉴스 제공</div>
                <div>밸류체인 존재 시 해외 뉴스 제공</div>
                <div>각 일봉별로 오답노트 작성 기능</div>
                <div>주식 차트에 뉴스 및 오답노트 표시</div>
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
              <div className={`${styles['title']} ${styles['scroll-animation']} ${isVisible ? styles['title-animation-show'] : ''}`} id={styles["right-desc"]}><span>오답노트</span> 작성 및 공유</div>
              <div className={`${styles["description"]} ${styles['scroll-animation']} ${isVisible ? styles['description-animation-show'] : ''}`} id={styles["right-desc"]}>
                <div>나만의 오답노트를 작성하고 주식을 복기</div>
                <div>내용을 공유하고 사람들과 소통</div>
                <div>스크랩과 댓글을 통해 피드백</div>
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
              <div className={`${styles['title']} ${styles['scroll-animation']} ${isVisible ? styles['title-animation-show'] : ''}`}><span>해외 밸류 체인</span> 정보 확인</div>
              <div className={`${styles['description']} ${styles['scroll-animation']} ${isVisible ? styles['description-animation-show'] : ''}`} >
                <div>국내 우량주 종목과 관련된 해외 밸류 체인 기업 정보 제공</div>
                <div></div>
                <div></div>
                <div></div>
              </div>
            </div>
            <div className={`${styles['value-image-box']} ${styles['scroll-animation']} ${isVisible ? styles['title-animation-show'] : ''}`}>
              <Image
                src={valueimg}
                alt="valueimg"
                width={600}
                height={300}
              />
            </div>
          </div>
          <div className={styles["start"]}>
            <div className={styles["Button-width"]}>
              <button onClick={goToStart} className={styles["button-box"]} style={{ color: "#4FE7B0", border: "2px solid #4FE7B0" }}>
                  <div>주식초보나들이 시작하기</div>
                  <HiArrowNarrowRight size="14"/>
              </button>
            </div>
          </div>
        </>
      ) : null}
    </>
  )
}
