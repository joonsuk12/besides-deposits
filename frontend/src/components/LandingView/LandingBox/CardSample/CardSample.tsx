// 시작 페이지 02 섹션의 예시 카드. NewStocks의 오답노트 카드 모양을 그대로 쓰고, 내용만 리포트 요약으로 바꿨다.
import styles from './cardsample.module.css'

import { BsBookmark } from "react-icons/bs";

import stockimg from '@/assets/stockimg.png'
import Image from 'next/image';

interface CardSampleProps {
  title: string;    // 리포트 제목
  content: string;  // 초보용 한 줄 결론
  author: string;   // 증권사
  stock: string;    // 종목
  date: string;
  tags: string[];
}

export default function CardSample({ title, content, author, stock, date, tags }: CardSampleProps) {
  return (
    <div className={styles['card-container']} id={styles['landing-container']}>
      <div className={styles['image-container']}>
        <Image
          src={stockimg}
          alt="차트 예시"
        /></div>

      <div className={styles['title-container']}>
        <div className={styles['title-left']}>
          <div className={styles['stock-box']}>
            <div className={styles['stock-img']}></div>
            <div className={styles['stock-name']}>{stock}</div>
          </div>
          <div className={styles['title']}>{title}</div>
        </div>

        <div className={styles['title-right']}>
          <BsBookmark size="17" />
        </div>
      </div>

      <div className={styles['content-container']}>
        <div className={styles['content']}>💡 {content}</div>
      </div>

      <div className={styles['content-bottom-container']}>
        <div className={styles['profile-container']}>
          <div className={styles['stock-img']}></div>
          <div className={styles['profile-name']}>{author}</div>
        </div>

        <div className={styles['time']}>{date}</div>
      </div>

      <div className={styles['bottom-container']}>
        <div className={styles['tag-container']}>
          {tags.map((tag) => <div key={tag}>{tag}</div>)}
        </div>
      </div>
    </div>
  );
}
