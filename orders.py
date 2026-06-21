"""
orders.py
모의투자 매수/매도 주문을 처리합니다.
"""

from typing import Optional
from api_client import KISApiClient


def place_buy_order(
    client: KISApiClient,
    config: dict,
    stock_code: str,
    price: int,
    quantity: int = 1,
    logger=None,
) -> Optional[dict]:
    """
    지정가 매수 주문을 제출합니다.

    Args:
        client:     KISApiClient
        config:     load_config() 반환값
        stock_code: 종목코드 (예: "005930")
        price:      주문가격 (원) — current_price - trade_offset
        quantity:   주문수량 (기본 1주)
        logger:     logging.Logger (선택)

    Returns:
        dict: 응답 JSON (실패 시 None)
    """
    path = "/uapi/domestic-stock/v1/trading/order-cash"
    tr_id = "VTTC0802U"  # 모의투자 현금 매수

    body = {
        "CANO": config["account_no"],
        "ACNT_PRDT_CD": config["account_code"],
        "PDNO": stock_code,
        "ORD_DVSN": "00",              # 00 = 지정가
        "ORD_QTY": str(quantity),
        "ORD_UNPR": str(price),        # 주문단가
    }

    if logger:
        logger.info(
            "[ORDER] 매수 주문 요청 | %s | %s원 × %d주",
            stock_code, f"{price:,}", quantity,
        )

    try:
        resp = client.post(path, tr_id, body)
        rt_cd = resp.get("rt_cd", "?")
        msg = resp.get("msg1", "")

        if rt_cd == "0":
            order_no = resp.get("output", {}).get("ODNO", "N/A")
            if logger:
                logger.info(
                    "[ORDER] 매수 주문 접수 완료 | 주문번호: %s | %s",
                    order_no, msg,
                )
        else:
            if logger:
                logger.warning(
                    "[ORDER] 매수 주문 응답 이상 | rt_cd=%s | %s", rt_cd, msg
                )
        return resp

    except Exception as e:
        if logger:
            logger.error("[ORDER] 매수 주문 실패: %s", e)
        return None


def place_sell_order(
    client: KISApiClient,
    config: dict,
    stock_code: str,
    price: int,
    quantity: int = 1,
    logger=None,
) -> Optional[dict]:
    """
    지정가 매도 주문을 제출합니다.

    Args:
        client:     KISApiClient
        config:     load_config() 반환값
        stock_code: 종목코드
        price:      주문가격 (원) — current_price + trade_offset
        quantity:   주문수량 (기본 1주)
        logger:     logging.Logger (선택)

    Returns:
        dict: 응답 JSON (실패 시 None)
    """
    path = "/uapi/domestic-stock/v1/trading/order-cash"
    tr_id = "VTTC0801U"  # 모의투자 현금 매도

    body = {
        "CANO": config["account_no"],
        "ACNT_PRDT_CD": config["account_code"],
        "PDNO": stock_code,
        "ORD_DVSN": "00",              # 00 = 지정가
        "ORD_QTY": str(quantity),
        "ORD_UNPR": str(price),
    }

    if logger:
        logger.info(
            "[ORDER] 매도 주문 요청 | %s | %s원 × %d주",
            stock_code, f"{price:,}", quantity,
        )

    try:
        resp = client.post(path, tr_id, body)
        rt_cd = resp.get("rt_cd", "?")
        msg = resp.get("msg1", "")

        if rt_cd == "0":
            order_no = resp.get("output", {}).get("ODNO", "N/A")
            if logger:
                logger.info(
                    "[ORDER] 매도 주문 접수 완료 | 주문번호: %s | %s",
                    order_no, msg,
                )
        else:
            if logger:
                logger.warning(
                    "[ORDER] 매도 주문 응답 이상 | rt_cd=%s | %s", rt_cd, msg
                )
        return resp

    except Exception as e:
        if logger:
            logger.error("[ORDER] 매도 주문 실패: %s", e)
        return None
