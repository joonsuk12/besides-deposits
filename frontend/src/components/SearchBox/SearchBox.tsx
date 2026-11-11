"use client";
// 종목 검색창 (이름·코드·초성 검색, 키보드 이동). NewStocks의 SearchBox를 옮긴 것.

import { useState, useEffect, useRef } from "react";

import AutocompleteBox from "./AutocompleteBox/AutocompleteBox";

import { searchStock } from "@/utils/searchStock";
import { fetchStocks, type Stock } from "@/lib/api";

import styles from "./SearchBox.module.css";
import { BiSearch, BiX } from "react-icons/bi";

type Props = {
  searchFunc: (stock: Stock) => void;
};

export default function SearchBox({ searchFunc }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const [inputText, setInputText] = useState("");
  const [showAutoBox, setShowAutoBox] = useState(false);
  const [selectedItem, setSelectedItem] = useState<number | null>(null);
  const [searchList, setSearchList] = useState<Stock[]>([]);
  const [allStocks, setAllStocks] = useState<Stock[]>([]);

  // 전체 종목 목록을 한 번 받아 두고, 검색은 브라우저 안에서 한다
  useEffect(() => {
    fetchStocks()
      .then(setAllStocks)
      .catch(() => {});
  }, []);

  // input 창 바깥 클릭 시 autocomplete box 숨기기
  useEffect(() => {
    const handleDocumentClick = (e: MouseEvent) => {
      if (inputRef.current && !inputRef.current.contains(e.target as Node)) {
        setShowAutoBox(false);
      }
    };

    document.addEventListener("click", handleDocumentClick);
    return () => document.removeEventListener("click", handleDocumentClick);
  }, []);

  // keyboard로 이동
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (selectedItem !== null && showAutoBox) {
        if (e.key === "ArrowUp") {
          e.preventDefault();
          setSelectedItem(selectedItem === 0 ? searchList.length - 1 : selectedItem - 1);
        } else if (e.key === "ArrowDown") {
          e.preventDefault();
          setSelectedItem((selectedItem + 1) % searchList.length);
        } else if (e.key === "Enter" && !e.isComposing) {
          e.preventDefault();
          handleItemClick(selectedItem);
        } else if (e.key === "Escape") {
          setShowAutoBox(false);
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
    // eslint-disable-next-line
  }, [selectedItem, searchList, showAutoBox]);

  // 입력 텍스트에 따라 autocomplete 결과 업데이트
  useEffect(() => {
    if (inputText.trim() !== "") {
      setShowAutoBox(true);
      const autocompleteResults = searchStock(inputText.trim(), allStocks);
      setSearchList(autocompleteResults.slice(0, 20));
      setSelectedItem(autocompleteResults.length > 0 ? 0 : null);
    } else {
      setShowAutoBox(false);
    }
  }, [inputText, allStocks]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [selectedItem]);

  const handleItemClick = (idx: number) => {
    setShowAutoBox(false);
    setInputText("");
    searchFunc(searchList[idx]);
  };

  return (
    <div className={styles["container"]}>
      <div className={styles["header-search"]}>
        <div className={styles["search-icon"]}>
          <BiSearch size="22" />
        </div>
        <input
          type="text"
          placeholder="종목명 / 종목코드 검색"
          ref={inputRef}
          value={inputText}
          onClick={() => inputText.trim() !== "" && setShowAutoBox(true)}
          onChange={(e) => setInputText(e.target.value)}
        />
        {inputText && (
          <div className={styles["erase-button"]} onClick={() => setInputText("")}>
            <BiX size="22" />
          </div>
        )}
      </div>
      {showAutoBox && (
        <AutocompleteBox
          ref={scrollRef}
          stockSearchList={searchList}
          selectedItem={selectedItem}
          handleItemHover={setSelectedItem}
          handleItemClick={handleItemClick}
        />
      )}
    </div>
  );
}
