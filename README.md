# KIS API 자동매매 시스템

한국투자증권 KIS Open API를 활용한 모의투자 자동매매 시스템입니다.

## 프로젝트 구조

```
samsung_auto_trader/
├── main.py           # 진입점
├── config.py         # 환경변수 로드 및 설정
├── auth.py           # 토큰 발급 + 당일 캐시 재사용
├── api_client.py     # KIS REST API 공통 HTTP 클라이언트
├── market_data.py    # 현재가 + 등락률 조회
├── account.py        # 잔고 및 보유종목 조회
├── orders.py         # 매수/매도 주문
├── strategy.py       # RSI + 등락률 복합 전략
├── trader.py         # 매매 루프 (복수 종목)
├── visualize.py      # 거래 결과 차트 생성
├── logger.py         # 로깅 + trade_log.csv 기록
├── requirements.txt
├── .env.example
└── screenshots/
```

## 환경 설정

`.env.example`을 복사해 `.env` 파일 생성 후 실제 값 입력:

```bash
cp .env.example .env
```

```
GH_APPKEY=실제_APP_KEY
GH_APPSECRET=실제_APP_SECRET
GH_ACCOUNT=50xxxxxxxx-01
```

## 설치

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 실행

```bash
# 자동매매 실행 (09:10~15:30 매매 시간대에만 주문)
python main.py

# 거래 결과 시각화 (main.py 실행 후)
python visualize.py
```

## 시스템 구조

```
토큰 발급 (당일 캐시) → 종목별 현재가 + 등락률 조회
→ RSI + 등락률 복합 전략 판단
→ BUY 신호: 현재가 - 2,000원 지정가 매수
→ 보유 시: 현재가 + 2,000원 지정가 매도
→ 잔고 재확인 → CSV 로그 → 30초 대기 → 반복
```

## 매매 전략

| 조건 | 내용 |
|------|------|
| 1차 조건 | 전일 대비 등락률 -1% 이하 (단기 낙폭 과대) |
| 2차 조건 | 가격 히스토리 15개 이상 시 RSI 추가 확인 |
| RSI > 50 | 매수 보류 (추세 반전 미확인) |
| RSI ≤ 50 | 매수 실행 (과매도 확인) |

전략 목적: 수익률 최적화가 아닌 자동매매 파이프라인 검증.

## 관찰 종목

- 삼성전자 (005930)
- SK하이닉스 (000660)

## 거래 기록

| 파일 | 내용 |
|------|------|
| `trade_log.csv` | 전체 주문/잔고 이벤트 기록 |
| `trader.log` | 실행 로그 |
| `screenshots/price_chart.png` | 가격 추이 + 매매 결정 차트 |

## 보안

API key는 `.env`에만 저장. `.gitignore`에 포함되어 GitHub에 올라가지 않습니다.
