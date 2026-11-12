import styles from './allcardsimage.module.css'
import Carousel from 'react-multi-carousel';
import 'react-multi-carousel/lib/styles.css';
import CardSample from '../CardSample/CardSample'
import { FaSortAmountDown } from 'react-icons/fa'

interface CardData {
  title: string;
  content: string;
  author: string;
  stock: string;
  date: string;
  tags: string[];
}

export default function AllCardsImage() {

  // 화면 소개용 예시. 실제 리포트가 아니다.
  const cardData: CardData[] = [
    { title: '(예시) 업황 회복 구간 진입', content: '제품 가격이 오르면서 다음 분기 이익이 늘 것이라는 의견', author: '○○증권', stock: '반도체 A사', date: '예시', tags: ['#목표주가 상향', '#실적'] },
    { title: '(예시) 수주가 실적을 이끈다', content: '쌓아 둔 주문이 많아 몇 년간 매출이 안정적일 것이라는 의견', author: '△△증권', stock: '기계 B사', date: '예시', tags: ['#수주', '#의견 유지'] },
    { title: '(예시) 비용 부담은 아직', content: '매출은 늘지만 원가가 올라 이익 개선은 늦어질 수 있다는 의견', author: '□□증권', stock: '소비재 C사', date: '예시', tags: ['#목표주가 하향', '#리스크'] },
    { title: '(예시) 배당 매력 부각', content: '이익의 상당 부분을 배당으로 돌려줄 계획이라는 점에 주목', author: '◇◇증권', stock: '금융 D사', date: '예시', tags: ['#배당', '#주주환원'] },
    { title: '(예시) 신제품 효과 기대', content: '새 제품이 잘 팔리면 점유율이 오를 수 있다는 의견', author: '☆☆증권', stock: '전자 E사', date: '예시', tags: ['#신제품', '#점유율'] }
  ];

  return (
    <div className={styles["image-container"]}>

      <div className={styles["sort-button-box"]}>
        <div>
          <div className={styles["button"]}>📄 오늘의 리포트</div>
          <div className={styles["button"]}>🔎 종목선택</div>
        </div>

        <div className={styles["button"]}>최신순<FaSortAmountDown id={styles["button-icon"]}/></div>
      </div>
      <Carousel
        additionalTransfrom={0}
        arrows={false}
        autoPlay
        autoPlaySpeed={2500}
        centerMode={false}
        className=""
        containerClass="container-with-dots"
        dotListClass=""
        draggable
        focusOnSelect={false}
        infinite
        itemClass=""
        keyBoardControl
        minimumTouchDrag={80}
        pauseOnHover
        renderArrowsWhenDisabled={false}
        renderButtonGroupOutside={false}
        renderDotsOutside={false}
        responsive={{
          desktop: {
            breakpoint: {
              max: 3000,
              min: 1600
            },
            items: 4,
            partialVisibilityGutter: 25
          },
          mobile: {
            breakpoint: {
              max: 1080,
              min: 0
            },
            items: 2,
            partialVisibilityGutter: 25
          },
          tablet: {
            breakpoint: {
              max: 1600,
              min: 1080
            },
            items: 3,
            partialVisibilityGutter: 25
          }
        }}
        rewind={false}
        rewindWithAnimation={false}
        rtl={false}
        shouldResetAutoplay
        showDots={false}
        sliderClass=""
        slidesToSlide={2}
        swipeable
      >
        {cardData.map((card, index) => (
          <CardSample key={index} {...card} />
        ))}
      </Carousel>
    </div>
  )
}