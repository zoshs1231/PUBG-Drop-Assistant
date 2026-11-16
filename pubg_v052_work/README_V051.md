# v0.5.1 - HTTPS 인증서 오류 수정

- Windows: truststore로 운영체제 인증서 저장소 사용
- 다른 환경: certifi CA 인증서 사용
- SSL 검증 비활성화하지 않음
- 기존 지도 캐시/기능 유지

## Windows 빌드
기존 EXE는 수정되지 않습니다. 새 ZIP을 풀고 `build_windows.bat`을 실행해 새 `dist\PUBG_Drop_Assistant.exe`를 생성하세요.

인증서 오류가 계속되면 Windows Update 및 PC의 보안 소프트웨어 HTTPS 검사 설정을 확인하세요. 회사/학교 프록시 환경에서는 관리자에게 신뢰 루트 인증서 설치를 문의하세요.
