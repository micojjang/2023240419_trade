"""
api_client.py
KIS REST API 공통 HTTP 클라이언트입니다.
헤더 조립, 오류 처리, 재시도 로직을 한 곳에서 관리합니다.
"""

import time
from typing import Any

import requests


class KISApiClient:
    """
    KIS Open API HTTP 클라이언트.
    GET / POST 요청을 공통 헤더와 재시도 로직으로 래핑합니다.
    """

    def __init__(self, config: dict, token: str, logger=None):
        """
        Args:
            config: load_config() 반환값
            token:  get_access_token() 반환값
            logger: logging.Logger (선택)
        """
        self.base_url = config["base_url"]
        self.appkey = config["appkey"]
        self.appsecret = config["appsecret"]
        self.token = token
        self.logger = logger

    def _base_headers(self, tr_id: str) -> dict:
        """공통 요청 헤더를 조립합니다."""
        return {
            "content-type": "application/json",
            "authorization": f"Bearer {self.token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": tr_id,
            "custtype": "P",  # 개인
        }

    def get(
        self,
        path: str,
        tr_id: str,
        params: dict,
        retries: int = 2,
    ) -> Any:
        """
        GET 요청을 보내고 응답 JSON을 반환합니다.

        Args:
            path:    API 경로 (예: /uapi/domestic-stock/v1/quotations/inquire-price)
            tr_id:   KIS 거래ID (예: FHKST01010100)
            params:  쿼리 파라미터 딕셔너리
            retries: 실패 시 재시도 횟수

        Returns:
            dict: 응답 JSON
        """
        url = self.base_url + path
        headers = self._base_headers(tr_id)

        for attempt in range(retries + 1):
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                if self.logger:
                    self.logger.warning(
                        "[API GET] 오류 (시도 %d/%d) tr_id=%s: %s",
                        attempt + 1, retries + 1, tr_id, e,
                    )
                if attempt < retries:
                    time.sleep(2)
                else:
                    raise

    def post(
        self,
        path: str,
        tr_id: str,
        body: dict,
        retries: int = 1,
    ) -> Any:
        """
        POST 요청을 보내고 응답 JSON을 반환합니다.

        Args:
            path:    API 경로
            tr_id:   KIS 거래ID (예: VTTC0802U)
            body:    요청 바디 딕셔너리
            retries: 실패 시 재시도 횟수 (주문은 중복 위험이 있어 기본 1회)

        Returns:
            dict: 응답 JSON
        """
        url = self.base_url + path
        headers = self._base_headers(tr_id)

        for attempt in range(retries + 1):
            try:
                resp = requests.post(url, headers=headers, json=body, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                if self.logger:
                    self.logger.warning(
                        "[API POST] 오류 (시도 %d/%d) tr_id=%s: %s",
                        attempt + 1, retries + 1, tr_id, e,
                    )
                if attempt < retries:
                    time.sleep(2)
                else:
                    raise
