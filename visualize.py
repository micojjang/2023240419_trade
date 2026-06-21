"""
visualize.py
trade_log.csv를 읽어 가격 추이 및 매매 결정 분포 차트를 생성합니다.
screenshots/price_chart.png 로 저장됩니다.

실행:
    python visualize.py
"""

import os

import matplotlib.pyplot as plt
import matplotlib
import pandas as pd

# 한글 폰트 설정 (macOS)
matplotlib.rcParams['axes.unicode_minus'] = False
try:
    matplotlib.rcParams['font.family'] = 'AppleGothic'
except Exception:
    pass

LOG_PATH  = os.path.join(os.path.dirname(__file__), "trade_log.csv")
SAVE_PATH = os.path.join(os.path.dirname(__file__), "screenshots", "price_chart.png")


def plot_trade_log() -> None:
    """trade_log.csv → 2패널 차트 생성 및 저장."""

    if not os.path.exists(LOG_PATH):
        print(f"[ERROR] {LOG_PATH} 파일이 없습니다. main.py를 먼저 실행하세요.")
        return

    df = pd.read_csv(LOG_PATH)

    # 가격 정보가 있는 행만 필터 (BALANCE_CHECK, BUY_ORDER, SELL_ORDER)
    df_price = df[df["price"] > 0].copy()

    if df_price.empty:
        print("[ERROR] 거래 기록이 없습니다.")
        return

    df_price["timestamp"] = pd.to_datetime(df_price["timestamp"])

    # 종목 이름 매핑
    name_map = {"005930": "삼성전자", "000660": "SK하이닉스"}

    fig, axes = plt.subplots(2, 1, figsize=(13, 9))
    fig.suptitle("KIS 모의투자 자동매매 결과", fontsize=16, fontweight="bold", y=0.98)

    # ── 패널 1: 종목별 현재가 추이 ────────────────────────────────
    colors = {"005930": "#2E75B6", "000660": "#C00000"}
    plotted = set()

    for _, row in df_price[df_price["action"] == "BALANCE_CHECK"].iterrows():
        code = str(row["stock_code"])
        if code in plotted:
            continue

    for code, group in df_price[df_price["action"] == "BALANCE_CHECK"].groupby("stock_code"):
        code = str(code)
        label = f"{name_map.get(code, code)}({code})"
        axes[0].plot(
            group["timestamp"], group["price"],
            marker="o", markersize=4,
            color=colors.get(code, "#7F7F7F"),
            label=label, linewidth=1.8,
        )

        # 매수 주문 표시
        buys = df_price[(df_price["action"] == "BUY_ORDER") &
                        (df_price["stock_code"].astype(str) == code)]
        if not buys.empty:
            axes[0].scatter(
                buys["timestamp"], buys["price"],
                marker="^", s=80, color="#2ECC71",
                zorder=5, label=f"{name_map.get(code, code)} 매수",
            )

        # 매도 주문 표시
        sells = df_price[(df_price["action"] == "SELL_ORDER") &
                         (df_price["stock_code"].astype(str) == code)]
        if not sells.empty:
            axes[0].scatter(
                sells["timestamp"], sells["price"],
                marker="v", s=80, color="#E74C3C",
                zorder=5, label=f"{name_map.get(code, code)} 매도",
            )

    axes[0].set_title("종목별 현재가 추이 및 주문 시점", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("가격 (원)")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)
    axes[0].tick_params(axis="x", rotation=30)

    # ── 패널 2: 매매 결정 분포 ────────────────────────────────────
    action_map = {
        "BUY_ORDER":    "매수 주문",
        "SELL_ORDER":   "매도 주문",
        "HOLD":         "HOLD",
        "BUY_SKIP":     "매수 생략",
        "SELL_SKIP":    "매도 생략",
        "BALANCE_CHECK":"잔고 확인",
    }
    color_map = {
        "BUY_ORDER":    "#2E75B6",
        "SELL_ORDER":   "#C00000",
        "HOLD":         "#7F7F7F",
        "BUY_SKIP":     "#95C8F0",
        "SELL_SKIP":    "#F0A0A0",
        "BALANCE_CHECK":"#B0B0B0",
    }

    counts = df["action"].value_counts()
    labels = [action_map.get(a, a) for a in counts.index]
    bar_colors = [color_map.get(a, "#999") for a in counts.index]

    axes[1].bar(labels, counts.values, color=bar_colors, edgecolor="white", width=0.6)
    axes[1].set_title("매매 결정 분포", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("횟수")
    axes[1].grid(True, alpha=0.3, axis="y")

    for i, v in enumerate(counts.values):
        axes[1].text(i, v + 0.1, str(v), ha="center", va="bottom", fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    plt.savefig(SAVE_PATH, dpi=150, bbox_inches="tight")
    print(f"[VISUALIZE] 차트 저장 완료: {SAVE_PATH}")
    plt.close()


if __name__ == "__main__":
    plot_trade_log()
