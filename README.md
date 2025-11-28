# Minecraft 제작 도우미 (Desktop GUI)

마인크래프트 콘텐츠 제작자/개발자를 위한 올인원 도구입니다. 데이터팩·리소스팩 스캐폴딩부터 명령어 빌더, 린트/검사, 배포 자동화, 문서 생성까지 GUI로 처리합니다. 기본 언어는 한국어이며, 상단 언어 선택기로 English 표기로 전환할 수 있습니다.


<img width="2916" height="1530" alt="image" src="https://github.com/user-attachments/assets/bb0ff145-4a68-4b5d-a412-bbeb886c379d" />

## 주요 기능 한눈에 보기
- **탭 검색 + 3줄 탭 바**: 많은 기능을 빠르게 찾을 수 있는 검색/다중행 탭 UI.
- **프로젝트/크리에이터**: 워크스페이스 지정, 로그, 플랜 저장/불러오기, 타이머, 랜덤 챌린지, 월드 백업(zip).
- **계산기/명령어**: 네더↔오버 좌표 변환, 거리/틱 계산, summon/give/tellraw, 고급 명령어(스코어보드/태그/게임룰/이펙트).
- **팩 스캐폴딩/JSON**: 데이터팩·리소스팩 템플릿 생성(load/tick 태그 포함), Loot Table/Recipe/Tag/Advancement/Predicate 스니펫 생성/저장.
- **고급 도구**: 스니펫 mcfunction 생성, pack_format 안내, pack.mcmeta 검사, mcfunction 린트, 워크스페이스 스캔, 모델 텍스처/JSON 스키마 검사.
- **배포/자동화**: 팩 zip 생성, 프로파일 명령어 세트 출력, mcfunction 린트, diff 비교/동기화, pack.mcmeta 일괄 업데이트, README/CHANGELOG 템플릿 생성, 워크스페이스 리포트.
- **콘텐츠 편집**: 일괄 검색/치환, 오프라인 가이드, 언어 키 누락 검사(en_us vs ko_kr), latest.log 오류 추출.
- **제작 보조**: 파티클 궤적(line/circle) mcfunction, 그라디언트 tellraw/title, 아이템 NBT /give 생성, sounds.json 병합, server.properties 편집, 네임스페이스 리네임, 구조 .nbt 뷰어, 함수 호출 그래프.

## 요구 사항
- macOS/Windows/Linux, Python 3.10+ (테스트: 3.13)
- Tkinter가 포함된 Python (Homebrew python-tk@3.13 사용 시 자동 설치)
- 선택: `nbtlib` 설치 시 구조 NBT 상세 뷰 향상 (`pip install nbtlib`)

## 설치/실행
1) 저장소 클론  
```bash
git clone https://github.com/GistKjoon/Minecraft-Content-Production-Program.git
cd Minecraft-Content-Production-Program
```
2) 의존성 설치 + 실행(자동)  
   - macOS/Homebrew: `./setup_and_run.command` 더블클릭 또는
```bash
bash setup_and_run.command
```
   - Homebrew가 없는 환경: Tkinter를 직접 설치 후 `python3 main.py` 실행
3) 수동 설치 스크립트(선택):  
```bash
bash install_dependencies.sh
python3 main.py
```

## 사용 안내 (주요 탭)
- **프로젝트 허브**: 워크스페이스 지정/저장, 데이터/리소스팩 폴더 열기, 로그 출력.
- **크리에이터 유틸**: 플랜 메모 JSON 저장/불러오기, 랜덤 챌린지, 촬영 타이머, 월드 폴더 zip 백업.
- **좌표/시간 계산기**: 네더↔오버월드 변환, 거리 계산, 틱↔초 변환.
- **명령어 & 고급 명령어**: summon/give/tellraw, 스코어보드/태그/게임룰/이펙트, 방송/하드코어 매크로.
- **팩 스캐폴딩 & JSON**: 데이터팩/리소스팩 템플릿 생성(pack.mcmeta, load/tick 태그, 예제 함수/ko_kr), Loot Table·Recipe·Tag·Advancement·Predicate 생성/저장.
- **개발 고급 도구**: mcfunction 스니펫 생성, pack_format 안내, pack.mcmeta 검사, 워크스페이스 JSON/모델/태그/pack 검사.
- **품질/체크리스트**: 녹화/배포 체크리스트, 워크스페이스 스캐너.
- **배포/자동화**: 팩 zip, 프로파일 명령어 출력, mcfunction 린트, diff 비교/동기화, README/CHANGELOG 생성, 워크스페이스 리포트.
- **편집/유지보수**: 문자열 검색/치환, 오프라인 FAQ/베스트 프랙티스.
- **출시 문서**: pack.mcmeta 기반 README/변경 로그 템플릿 생성.
- **통계/인벤토리**: 팩 수, mcfunction/텍스처/lang 개수, 총 용량 요약.
- **서버 설정**: server.properties 주요 키(motd, difficulty, view-distance 등) 편집/저장.
- **레시피 생성**: 3x3 Shaped, Shapeless JSON 생성/저장.
- **파티클/이펙트**: 라인/원형 파티클 경로 mcfunction 생성/저장.
- **텍스트/채팅**: 그라디언트 tellraw/title 생성/복사.
- **태그/메타**: Tag JSON 생성, pack.mcmeta pack_format/description 일괄 적용.
- **비교/동기화**: 폴더 차이(추가/삭제/수정) 확인, src→dst 동기화.
- **마이그레이션/스케줄**: 문자열 치환 기반 버전 마이그레이션(드라이런/적용), /schedule 스니펫 생성.
- **아이템/NBT**: 이름/색상/로어/인챈트 포함 /give 명령 생성.
- **사운드**: sounds.json 이벤트 병합(자막/replace 옵션).
- **로그/언어**: latest.log 에러 추출, lang(en_us vs ko_kr) 누락/초과 키 검사.
- **JSON/모델 검사**: recipe/loot/adv/predicate/tag 스키마 검사, 모델→텍스처 누락 확인.
- **네임스페이스/리포트**: 네임스페이스 리네임(old→new 치환), 워크스페이스 Markdown 리포트.
- **구조/NBT**: 구조 .nbt 정보 표시(nbtlib 사용 시 상세).
- **함수 그래프**: mcfunction 호출 그래프/도달 함수 리스트 생성(시작 함수·깊이 지정).

## 팁
- **언어 전환**: 우측 상단 언어 콤보에서 한국어/English 전환 → 탭 라벨 즉시 변경.
- **탭 검색**: 상단 검색창으로 원하는 탭을 바로 필터링.
- **필수 설정**: 첫 실행 후 워크스페이스 루트를 지정하면 모든 생성/저장 기능이 해당 경로를 사용.
- **백업**: 마이그레이션/네임스페이스 변경 전 월드/팩 폴더 백업을 권장.
- **선택 라이브러리**: 구조 NBT 세부 뷰를 원하면 `pip install nbtlib`.

## 라이선스
- 이 저장소 내 코드/문서의 라이선스는 `LICENSE` 파일을 참조하세요.
