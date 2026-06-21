"""
market_data.py
국내주식 현재가 및 등락률/거래량 조회를 담당합니다.
strategy.py가 필요로 하는 change_rate 필드를 추가로 반환합니다.
"""

from api_client import KISApiClient


def get_current_price(client: KISApiClient, stock_code: str, logger=None) -> dict:
    """
    주어진 종목의 현재가 및 주요 시세 정보를 반환합니다.

    Args:
        client:     KISApiClient 인스턴스
        stock_code: 종목코드 (예: "005930")
        logger:     logging.Logger (선택)

    Returns:
        dict: {
            "stock_code":    str,
            "stock_name":    str,
            "current_price": int,   # 현재가 (원)
            "change_rate":   float, # 전일 대비 등락률 (%)
            "volume":        int,   # 누적 거래량
            "high_price":    int,   # 당일 고가
            "low_price":     int,   # 당일 저가
        }

    Raises:
        ValueError: API 응답에 현재가 필드가 없을 때
    """
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = "FHKST01010100"
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": stock_code,
    }

    data = client.get(path, tr_id, params)
    output = data.get("output", {})

    price_str = output.get("stck_prpr")
    if not price_str:
        raise ValueError(
            f"현재가(stck_prpr) 필드를 찾을 수 없습니다. 응답: {data}"
        )

    result = {
        "stock_code":    stock_code,
        "stock_name":    output.get("hts_kor_isnm", stock_code),
        "current_price": int(price_str),
        "change_rate":   float(output.get("prdy_ctrt", 0)),   # 전일 대비 등락률
        "volume":        int(output.get("acml_vol", 0)),       # 누적 거래량
        "high_price":    int(output.get("stck_hgpr", 0)),      # 당일 고가
        "low_price":     int(output.get("stck_lwpr", 0)),      # 당일 저가
    }

    if logger:
        logger.info(
            "[MARKET] %s(%s) 현재가: %s원 | 등락률: %+.2f%% | 거래량: %s",
            result["stock_name"], stock_code,
            f"{result['current_price']:,}",
            result["change_rate"],
            f"{result['volume']:,}",
        )

    return result
