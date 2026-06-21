"""
trader.py
A학점 전략 포함 매매 루프.
- 복수 종목 (삼성전자 005930 + SK하이닉스 000660)
- RSI + 등락률 복합 전략 (strategy.py)
- 기존 ±2000원 지정가 주문 유지 (학교 프롬프트 요구사항)
- 09:10 ~ 15:30 매매 시간대 제어
"""

import time
from collections import defaultdict
from datetime import datetime

from account import get_holdings, get_target_holding_qty
from api_client import KISApiClient
from logger import log_trade
from market_data import get_current_price
from orders import place_buy_order, place_sell_order
from strategy import decide

# 관찰 종목 리스트 (A학점: 복수 종목)
WATCHLIST = [
    {"code": "005930", "name": "삼성전자"},
    {"code": "000660", "name": "SK하이닉스"},
]


def _is_trading_window(config: dict) -> bool:
    """현재 시각이 09:10~15:30 매매 시간대인지 확인."""
    now = datetime.now().strftime("%H:%M")
    return config["trade_start"] <= now <= config["trade_end"]


def run_trading_loop(client: KISApiClient, config: dict, logger) -> None:
    """
    자동매매 메인 루프.

    사이클 흐름 (종목별):
      1. 현재가 + 등락률 조회
      2. RSI + 등락률 복합 전략으로 매매 신호 판단
      3. BUY 신호: 현재가 - trade_offset 지정가 매수
      4. 보유 시: 현재가 + trade_offset 지정가 매도
      5. 주문 후 잔고 재확인 → 체결 추정
      6. trade_log.csv 기록
    """
    offset = config["trade_offset"]
    interval = config["poll_interval_sec"]

    # 종목별 가격 히스토리 (RSI 계산용)
    price_history: dict = defaultdict(list)

    logger.info("=" * 60)
    logger.info("[TRADER] 자동매매 시작 | 종목: %s",
                ", ".join(s["name"] for s in WATCHLIST))
    logger.info("[TRADER] 전략: 등락률 -1%% 이하 + RSI 복합 판단")
    logger.info("[TRADER] 매매 시간대: %s ~ %s",
                config["trade_start"], config["trade_end"])
    logger.info("=" * 60)

    cycle = 0

    while True:
        cycle += 1
        now_str = datetime.now().strftime("%H:%M:%S")

        # ── 매매 시간대 확인 ────────────────────────────────────────
        if not _is_trading_window(config):
            current_time = datetime.now().strftime("%H:%M")
            if current_time > config["trade_end"]:
                logger.info("[TRADER] 15:30 이후 → 자동매매 종료")
                log_trade(action="SESSION_END", note=f"종료 시각: {now_str}")
                break
            elif current_time < config["trade_start"]:
                logger.info("[TRADER] 장 시작 전 (%s) → 자동 종료. %s 이후에 다시 실행하세요.",
                            now_str, config["trade_start"])
                log_trade(action="SESSION_END", note=f"장 시작 전 종료 ({now_str})")
                break
            else:
                logger.info("[TRADER] 매매 시간 외 대기 중 (%s)...", now_str)
                log_trade(action="SKIP", note=f"매매 시간 외 ({now_str})")
                time.sleep(interval)
                continue

        logger.info("-" * 50)
        logger.info("[TRADER] 사이클 #%d (%s)", cycle, now_str)

        # ── 종목별 순회 ─────────────────────────────────────────────
        for stock in WATCHLIST:
            code = stock["code"]
            name = stock["name"]

            # 1. 현재가 + 등락률 조회
            try:
                price_info = get_current_price(client, code, logger)
            except Exception as e:
                logger.error("[TRADER] %s 현재가 조회 실패: %s", name, e)
                continue

            current_price = price_info["current_price"]

            # 가격 히스토리 누적 (RSI용)
            price_history[code].append(current_price)
            if len(price_history[code]) > 50:
                price_history[code].pop(0)

            # 2. 전략 판단
            decision, reason = decide(price_info, price_history[code])
            logger.info(
                "[STRATEGY] %s → %s | %s", name, decision, reason
            )

            # 3. 주문 전 잔고 확인
            try:
                before = get_holdings(client, config, logger)
            except Exception as e:
                logger.error("[TRADER] 잔고 조회 실패: %s", e)
                continue

            before_qty = get_target_holding_qty(before["holdings"], code)
            log_trade(
                action="BALANCE_CHECK",
                stock_code=code,
                price=current_price,
                available_cash=before["available_cash"],
                holding_qty=before_qty,
                note=f"주문 전 | 전략={decision} | {reason}",
            )

            # 4. 매수 주문 — BUY 신호 + 잔액 충분할 때만
            buy_price = current_price - offset
            if decision == "BUY" and before["available_cash"] >= buy_price:
                buy_resp = place_buy_order(
                    client, config, code, buy_price,
                    quantity=1, logger=logger
                )
                order_no = ""
                if buy_resp and buy_resp.get("rt_cd") == "0":
                    order_no = buy_resp.get("output", {}).get("ODNO", "")
                log_trade(
                    action="BUY_ORDER",
                    stock_code=code,
                    price=buy_price,
                    quantity=1,
                    order_no=order_no,
                    available_cash=before["available_cash"],
                    holding_qty=before_qty,
                    note=f"현재가 {current_price:,}원 | {reason}",
                )
            elif decision == "BUY" and before["available_cash"] < buy_price:
                logger.info("[TRADER] %s 잔액 부족 → 매수 생략", name)
                log_trade(action="BUY_SKIP", stock_code=code,
                          price=buy_price, note="잔액 부족")
            else:
                logger.info("[TRADER] %s HOLD → 매수 없음", name)
                log_trade(action="HOLD", stock_code=code,
                          price=current_price, note=reason)

            # 5. 매도 주문 — 보유 수량 있을 때만
            sell_price = current_price + offset
            if before_qty > 0:
                sell_resp = place_sell_order(
                    client, config, code, sell_price,
                    quantity=1, logger=logger
                )
                order_no = ""
                if sell_resp and sell_resp.get("rt_cd") == "0":
                    order_no = sell_resp.get("output", {}).get("ODNO", "")
                log_trade(
                    action="SELL_ORDER",
                    stock_code=code,
                    price=sell_price,
                    quantity=1,
                    order_no=order_no,
                    available_cash=before["available_cash"],
                    holding_qty=before_qty,
                    note=f"현재가 {current_price:,}원 기준",
                )
            else:
                logger.info("[TRADER] %s 보유 없음 → 매도 생략", name)
                log_trade(action="SELL_SKIP", stock_code=code, note="보유수량 0")

            # 6. 주문 후 잔고 재확인
            time.sleep(3)
            try:
                after = get_holdings(client, config, logger)
                after_qty = get_target_holding_qty(after["holdings"], code)

                if after_qty > before_qty:
                    note = f"매수 체결 추정 ({before_qty}→{after_qty}주)"
                    logger.info("[TRADER] %s %s", name, note)
                elif after_qty < before_qty:
                    note = f"매도 체결 추정 ({before_qty}→{after_qty}주)"
                    logger.info("[TRADER] %s %s", name, note)
                else:
                    note = "체결 미확인 (지정가 미체결 가능)"
                    logger.info("[TRADER] %s %s", name, note)

                log_trade(
                    action="BALANCE_CHECK",
                    stock_code=code,
                    price=current_price,
                    available_cash=after["available_cash"],
                    holding_qty=after_qty,
                    note=f"주문 후 확인 | {note}",
                )
            except Exception as e:
                logger.warning("[TRADER] %s 주문 후 잔고 확인 실패: %s", name, e)

        # ── 다음 사이클 대기 ────────────────────────────────────────
        logger.info("[TRADER] %d초 대기 후 다음 사이클...", interval)
        time.sleep(interval)
