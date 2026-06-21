"""
config.py
환경변수에서 API 자격증명을 로드합니다.
GitHub Codespaces Secrets에 저장된 값을 읽어옵니다.
"""

import os
from dotenv import load_dotenv

# VS Code 로컬 실행 시 .env 파일에서 환경변수 로드
# Codespaces에서는 이미 환경변수가 주입되어 있으므로 무시됨
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def load_config() -> dict:
    """
    환경변수에서 KIS API 설정을 로드합니다.

    필요한 환경변수:
        GH_APPKEY    : KIS 모의투자 APP KEY
        GH_APPSECRET : KIS 모의투자 APP SECRET
        GH_ACCOUNT   : 모의투자 계좌번호 (예: 12345678-01 형태, 하이픈 포함 가능)

    Returns:
        dict: 설정값 딕셔너리
    """
    appkey = os.environ.get("GH_APPKEY", "").strip()
    appsecret = os.environ.get("GH_APPSECRET", "").strip()
    account_raw = os.environ.get("GH_ACCOUNT", "").strip()

    missing = []
    if not appkey:
        missing.append("GH_APPKEY")
    if not appsecret:
        missing.append("GH_APPSECRET")
    if not account_raw:
        missing.append("GH_ACCOUNT")

    if missing:
        raise EnvironmentError(
            f"다음 환경변수가 설정되지 않았습니다: {', '.join(missing)}\n"
            "GitHub Codespaces → Settings → Secrets 에서 확인하세요."
        )

    # 계좌번호 파싱: "12345678-01" → account_no="12345678", account_code="01"
    if "-" in account_raw:
        parts = account_raw.split("-", 1)
        account_no = parts[0]
        account_code = parts[1]
    else:
        # 하이픈 없이 숫자만 입력한 경우 앞 8자리 + 나머지
        account_no = account_raw[:8]
        account_code = account_raw[8:] if len(account_raw) > 8 else "01"

    return {
        "appkey": appkey,
        "appsecret": appsecret,
        "account_no": account_no,        # 8자리 계좌번호
        "account_code": account_code,    # 상품코드 (보통 "01")
        "base_url": "https://openapivts.koreainvestment.com:29443",  # 모의투자 URL
        "target_stock": "005930",        # 삼성전자
        "trade_offset": 2000,            # 매수: 현재가 - 2000, 매도: 현재가 + 2000
        "poll_interval_sec": 30,         # 루프 간격 (초) - 모의투자 rate limit 고려
        "trade_start": "09:10",
        "trade_end": "15:30",
    }
