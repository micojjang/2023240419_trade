"""
account.py
모의투자 계좌 잔고 및 보유종목 조회를 담당합니다.
"""

from typing import Optional
from api_client import KISApiClient


def get_holdings(client: KISApiClient, config: dict, logger=None) -> dict:
    """
    계좌 보유종목 및 주문가능금액을 조회합니다.

    Args:
        client: KISApiClient 인스턴스
        config: load_config() 반환값
        logger: logging.Logger (선택)

    Returns:
        dict: {
            "available_cash": int,         # 주문가능금액 (원)
            "holdings": [                  # 보유종목 리스트
                {
                    "stock_code": str,
                    "stock_name": str,
                    "quantity": int,       # 보유수량
                    "avg_price": int,      # 평균단가
                    "current_price": int,  # 현재가
                    "eval_profit_loss": int, # 평가손익
                }
            ]
        }
    """
    path = "/uapi/domestic-stock/v1/trading/inquire-balance"
    tr_id = "VTTC8434R"  # 모의투자 주식잔고조회

    params = {
        "CANO": config["account_no"],           # 계좌번호 앞 8자리
        "ACNT_PRDT_CD": config["account_code"], # 계좌상품코드
        "AFHR_FLPR_YN": "N",                    # 시간외단일가여부
        "OFL_YN": "",
        "INQR_DVSN": "02",                      # 조회구분 02=잔고합산
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",                      # 처리구분 01=현재가
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }

    data = client.get(path, tr_id, params)

    # 주문가능금액
    output2 = data.get("output2", [{}])
    available_cash_str = output2[0].get("dnca_tot_amt", "0") if output2 else "0"
    available_cash = int(available_cash_str)

    # 보유종목 리스트
    holdings = []
    for item in data.get("output1", []):
        qty = int(item.get("hldg_qty", 0))
        if qty <= 0:
            continue
        holdings.append({
            "stock_code": item.get("pdno", ""),
            "stock_name": item.get("prdt_name", ""),
            "quantity": qty,
            "avg_price": int(item.get("pchs_avg_pric", 0)),
            "current_price": int(item.get("prpr", 0)),
            "eval_profit_loss": int(item.get("evlu_pfls_amt", 0)),
        })

    result = {
        "available_cash": available_cash,
        "holdings": holdings,
    }

    if logger:
        logger.info(
            "[ACCOUNT] 주문가능금액: %s원 | 보유종목: %d개",
            f"{available_cash:,}", len(holdings),
        )
        for h in holdings:
            logger.info(
                "[ACCOUNT]   └ %s(%s) %d주 | 평균단가 %s원 | 평가손익 %s원",
                h["stock_name"], h["stock_code"], h["quantity"],
                f"{h['avg_price']:,}", f"{h['eval_profit_loss']:,}",
            )

    return result


def get_target_holding_qty(holdings: list, stock_code: str) -> int:
    """
    보유종목 리스트에서 특정 종목의 보유수량을 반환합니다.

    Args:
        holdings:   get_holdings()["holdings"] 값
        stock_code: 조회할 종목코드

    Returns:
        int: 보유수량 (없으면 0)
    """
    for h in holdings:
        if h["stock_code"] == stock_code:
            return h["quantity"]
    return 0
