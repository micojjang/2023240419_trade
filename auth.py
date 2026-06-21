"""
auth.py
KIS API 인증 토큰 발급 및 당일 재사용 캐시를 관리합니다.
token_cache.json에 저장하여 불필요한 재발급을 방지합니다.
"""

import json
import os
import time
from datetime import date

import requests

CACHE_FILE = os.path.join(os.path.dirname(__file__), "token_cache.json")


def _load_cache() -> dict:
    """캐시 파일이 있으면 읽고, 없으면 빈 dict 반환."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_cache(token: str, issued_date: str) -> None:
    """토큰과 발급 날짜를 캐시 파일에 저장."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({"token": token, "issued_date": issued_date}, f)


def get_access_token(config: dict, logger=None) -> str:
    """
    당일 유효한 액세스 토큰을 반환합니다.
    - 캐시에 오늘 날짜 토큰이 있으면 재사용
    - 없으면 새로 발급 후 캐시에 저장

    Args:
        config: load_config()에서 반환된 설정 딕셔너리
        logger: logging.Logger 인스턴스 (선택)

    Returns:
        str: Bearer 토큰 문자열
    """
    today = str(date.today())
    cache = _load_cache()

    # 당일 캐시 확인
    if cache.get("issued_date") == today and cache.get("token"):
        if logger:
            logger.info("[AUTH] 당일 캐시 토큰 재사용 (issued_date=%s)", today)
        return cache["token"]

    # 새 토큰 발급
    if logger:
        logger.info("[AUTH] 토큰 만료 또는 없음 → 새 토큰 발급 요청")

    url = f"{config['base_url']}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": config["appkey"],
        "appsecret": config["appsecret"],
    }

    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            token = data.get("access_token")
            if not token:
                raise ValueError(f"access_token 필드가 없습니다. 응답: {data}")
            _save_cache(token, today)
            if logger:
                logger.info("[AUTH] 토큰 발급 성공 (issued_date=%s)", today)
            return token
        except requests.RequestException as e:
            if logger:
                logger.warning("[AUTH] 토큰 발급 실패 (시도 %d/3): %s", attempt + 1, e)
            if attempt < 2:
                time.sleep(3)
            else:
                raise
