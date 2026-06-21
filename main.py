"""
main.py
자동매매 시스템 진입점.
환경변수 로드 → 토큰 발급 → 매매 루프 실행
"""

import sys

from auth import get_access_token
from api_client import KISApiClient
from config import load_config
from logger import setup_logger
from trader import run_trading_loop


def main() -> None:
    # ── 로거 초기화 ───────────────────────────────────────────────────────
    logger = setup_logger("trader")

    # ── 설정 로드 ─────────────────────────────────────────────────────────
    try:
        config = load_config()
        logger.info("[MAIN] 환경변수 로드 완료 | 계좌: %s-%s",
                    config["account_no"], config["account_code"])
    except EnvironmentError as e:
        logger.error("[MAIN] 환경변수 오류:\n%s", e)
        sys.exit(1)

    # ── 토큰 발급 (당일 캐시 재사용) ─────────────────────────────────────
    try:
        token = get_access_token(config, logger)
    except Exception as e:
        logger.error("[MAIN] 토큰 발급 실패: %s", e)
        sys.exit(1)

    # ── API 클라이언트 생성 ───────────────────────────────────────────────
    client = KISApiClient(config, token, logger)

    # ── 자동매매 루프 실행 ────────────────────────────────────────────────
    try:
        run_trading_loop(client, config, logger)
    except KeyboardInterrupt:
        logger.info("[MAIN] 사용자 중단 (Ctrl+C)")
    except Exception as e:
        logger.exception("[MAIN] 예상치 못한 오류: %s", e)
        sys.exit(1)

    logger.info("[MAIN] 프로그램 종료")


if __name__ == "__main__":
    main()
