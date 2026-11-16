# PUBG Drop Assistant v0.5 (오프라인)

## 주요 기능
- 지도 선택: Erangel, Miramar, Taego, Vikendi, Deston, Rondo, Sanhok, Paramo, Karakin, Haven(과거 지도).
- 지도별 크기에 맞춰 클릭 좌표와 거리 환산. 지도 이미지는 저작권 및 배포 제약으로 포함하지 않음. **선택한 지도와 정확히 맞는 정사각형 전체 지도 이미지를 직접 불러오세요.**
- 에란겔 사용자 1회 실측값에 기반한 참고 구간 표시, 커뮤니티 접근 거리/급강하 전환 거리 안내.
- 경로와 목표 사이의 기하학적 이탈 후보 계산. 600m 접근 불가능하면 다른 반경 또는 최단 접근점 사용.
- 녹화 영상 분석, CSV, 프로젝트 저장·불러오기 유지.
- 게임 실시간 캡처/게임 내 오버레이/자동 조작 없음.

## 중요 한계
1. 맵별 물리 데이터가 검증된 것이 아닙니다. 일부 지도는 범용 커뮤니티 기준을 사용합니다.
2. 표시되는 200~210km/h는 HUD 목표 속도이며 수평 속도가 아닙니다.
3. '400m 고도에서 Shift'처럼 특정 절대 고도를 강제하는 것은 지형에 따라 잘못될 수 있어 구현하지 않았습니다.
4. 현재 계산은 **착륙 시간 최소화 물리 시뮬레이션이 아닙니다.** 비행기 속도 기본값도 미검증 가정입니다.
5. Haven은 과거 지도이므로 현재 매치에서 제공되지 않을 수 있습니다.

## 참고자료
- https://www.youtube.com/watch?v=HM2XSzs5kMA (2022년 커뮤니티 가이드; Erangel/Miramar, Sanhok, Taego 관련 설명)
- https://support.pubg.com/hc/en-us/articles/115004171393-Parachute-System (공식 조작 설명)
- https://senseos.gg/guides/pubg-battlegrounds/map-sizes/ (2026년 맵 크기 비교)

## 실행
`run_windows.bat` / `build_windows.bat` 사용. Python 3.11~3.12 권장.
