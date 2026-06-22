"""
strategy.py
A학점 차별화 전략: 모멘텀(Trend Following) + RSI 복합 판단.
장중 상승 추세가 확인되면 매수하는 추세 추종 전략.
trader.py에서 호출됩니다.
"""

from typing import Tuple


def compute_rsi(prices: list, period: int = 14) -> float:
    """
    RSI(Relative Strength Index) 계산.

    Args:
        prices: 최근 가격 리스트 (오래된 것 → 최신 순)
        period: 기본 14

    Returns:
        float: RSI 값 (0~100)
            RSI < 30 → 과매도(oversold) → 매수 신호
            RSI > 70 → 과매수(overbought) → 매도 신호
    """
    if len(prices) < period + 1:
        return 50.0  # 데이터 부족 시 중립값

    gains, losses = [], []
    for i in range(len(prices) - period, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def moving_average(prices: list, window: int) -> float | None:
    """단순 이동평균 계산."""
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window


def decide(price_info: dict, price_history: list = None) -> Tuple[str, str]:
    """
    매매 신호 판단 — 모멘텀(Trend Following) 전략.

    전략:
      - 전일 대비 등락률 +0.3% 이상 → 상승 추세 확인 → 매수 후보
      - 가격 히스토리 15개 이상이면 RSI 추가 확인
        RSI < 30이면 매수 보류 (과매도 구간, 추세 신뢰도 낮음)
      - 그 외 → HOLD

    Args:
        price_info: market_data.get_current_price() 반환값
        price_history: 해당 종목의 가격 기록 리스트 (선택)

    Returns:
        Tuple[str, str]: (결정, 사유)
            결정: 'BUY' | 'SELL' | 'HOLD'
    """
    change_rate = price_info.get("change_rate", 0.0)
    decision = "HOLD"
    reason = "조건 미충족"

    if change_rate >= 0.3:
        decision = "BUY"
        reason = f"등락률 {change_rate:+.2f}% (모멘텀 임계값 +0.3% 이상)"

        if price_history and len(price_history) >= 15:
            rsi = compute_rsi(price_history)
            if rsi < 30:
                decision = "HOLD"
                reason = (
                    f"등락률 조건 충족이나 RSI={rsi:.1f} (30 미만, 추세 신뢰도 낮음)"
                )
            else:
                reason += f" + RSI={rsi:.1f} (추세 확인 → 매수)"

    return decision, reason
