// 글꼴. Pretendard(한글·숫자 모두 깔끔한 무료 글꼴, OFL 라이선스)를 npm 패키지에서 우리 서버로 직접 내보낸다.
// next/font/local이 빌드할 때 파일을 복사하고 미리 불러오기(preload)까지 해 준다. 외부 CDN 요청 없음.
import localFont from "next/font/local";

export const pretendard = localFont({
  src: "../../node_modules/pretendard/dist/web/variable/woff2/PretendardVariable.woff2",
  display: "swap",
  weight: "45 920",
  variable: "--font-pretendard",
});
