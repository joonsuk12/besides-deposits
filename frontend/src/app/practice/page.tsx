// 예전 타임머신 연습장 주소. 2026-11-25부터 읽기 퀴즈(/quiz)로 바뀌어서 그쪽으로 보낸다.
// (타임머신의 "그때 사실 읽기"는 퀴즈의 한 유형으로 들어갔다.)
import { redirect } from "next/navigation";

export default function PracticePage() {
  redirect("/quiz");
}
