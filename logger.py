"""
logger.py
콘솔과 trade_log.csv 파일에 동시에 기록하는 로거를 설정합니다.
"""

import csv
import logging
import os
from datetime import datetime


def setup_logger(name: str = "trader") -> logging.Logger:
    """
    콘솔(INFO)과 파일(DEBUG) 양쪽에 로그를 출력하는 Logger를 반환합니다.

    Args:
        name: 로거 이름

    Returns:
        logging.Logger
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # 이미 설정된 경우 재설정 방지

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 콘솔 핸들러
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # 파일 핸들러 (debug 포함 전부 기록)
    log_dir = os.path.dirname(__file__)
    fh = logging.FileHandler(
        os.path.join(log_dir, "trader.log"),
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


# ── CSV 거래 로그 ────────────────────────────────────────────────────────────

_CSV_PATH = os.path.join(os.path.dirname(__file__), "trade_log.csv")
_CSV_HEADERS = [
    "timestamp", "action", "stock_code", "price", "quantity",
    "order_no", "available_cash", "holding_qty", "note",
]


def _ensure_csv_header() -> None:
    """CSV 파일이 없으면 헤더를 생성합니다."""
    if not os.path.exists(_CSV_PATH):
        with open(_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_HEADERS)
            writer.writeheader()


def log_trade(
    action: str,
    stock_code: str = "",
    price: int = 0,
    quantity: int = 0,
    order_no: str = "",
    available_cash: int = 0,
    holding_qty: int = 0,
    note: str = "",
) -> None:
    """
    거래 이벤트를 trade_log.csv에 한 줄 추가합니다.

    Args:
        action:         "BUY_ORDER" | "SELL_ORDER" | "BALANCE_CHECK" | "SKIP" 등
        stock_code:     종목코드
        price:          주문/조회 가격
        quantity:       수량
        order_no:       주문번호
        available_cash: 주문가능금액
        holding_qty:    보유수량
        note:           기타 메모
    """
    _ensure_csv_header()
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "stock_code": stock_code,
        "price": price,
        "quantity": quantity,
        "order_no": order_no,
        "available_cash": available_cash,
        "holding_qty": holding_qty,
        "note": note,
    }
    with open(_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_HEADERS)
        writer.writerow(row)
