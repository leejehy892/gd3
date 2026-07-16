"""
MRI 조영제(가돌리늄 착물) 평형상수(K) 시뮬레이터 - Streamlit 웹앱

실행 방법 (로컬 테스트):
    pip install streamlit matplotlib numpy
    streamlit run streamlit_app.py

배포 방법:
    1. 이 파일을 GitHub 저장소에 올리기 (requirements.txt도 함께)
    2. https://streamlit.io/cloud 에서 저장소 연결
    3. 자동으로 공개 URL 생성됨 (예: yourapp.streamlit.app)

화학2 개념: 화학평형, 평형상수(K), ICE표
반응: Gd3+ + L <=> GdL,  K = [GdL] / ([Gd3+][L])
"""

import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import streamlit as st

# 한글 폰트 설정 (배포 환경에 따라 폰트가 없을 수 있어 예외 처리)
try:
    mpl.rcParams["font.family"] = "Noto Sans CJK JP"
except Exception:
    pass
mpl.rcParams["axes.unicode_minus"] = False


def free_gd_concentration(K: float, C0: float) -> float:
    """
    Gd3+ + L <=> GdL 반응에서, 1:1 몰비 초기농도 C0일 때
    평형 상태의 자유 Gd3+ 농도를 계산 (ICE표 유도, 수치적으로 안정한 형태 사용)
    """
    if K <= 0 or C0 <= 0:
        return 0.0
    discriminant = 1 + 4 * K * C0
    return (2 * C0) / (1 + math.sqrt(discriminant))


# -----------------------------------------------------------
# 페이지 기본 설정
# -----------------------------------------------------------
st.set_page_config(page_title="Gd 조영제 평형상수 시뮬레이터", layout="wide")

st.title("🧲 MRI 조영제 평형상수(K) 시뮬레이터")
st.markdown(
    """
가돌리늄 착물 반응 **Gd³⁺ + L ⇌ GdL** 에서, 리간드의 종류(구조)에 따라
평형상수 **K**가 달라지고, 그 결과 평형 상태에서 풀려나오는
**자유 Gd³⁺ 농도**가 어떻게 달라지는지 확인해보세요.
"""
)

st.divider()

# -----------------------------------------------------------
# 사이드바: 사용자 입력
# -----------------------------------------------------------
st.sidebar.header("⚙️ 조건 설정")

C0 = st.sidebar.select_slider(
    "초기 농도 C0 (mol/L)",
    options=[1e-4, 1e-3, 1e-2, 1e-1, 1.0],
    value=1e-3,
    format_func=lambda x: f"{x:.0e}",
)

st.sidebar.markdown("---")
st.sidebar.markdown("**조영제별 log K 값 조절** (문헌값 기준으로 시작, 직접 바꿔보세요)")

default_agents = {
    "Gd-DTPA (Magnevist, 선형-이온성)": 22.46,
    "Gd-DTPA-BMA (Omniscan, 선형-비이온성)": 16.85,
    "Gd-HP-DO3A (ProHance, 대환형-비이온성)": 23.80,
    "Gd-DOTA (Dotarem, 대환형-이온성)": 25.30,
}

logK_values = {}
for name, default_val in default_agents.items():
    logK_values[name] = st.sidebar.slider(
        name, min_value=10.0, max_value=30.0, value=default_val, step=0.05
    )

# -----------------------------------------------------------
# 계산
# -----------------------------------------------------------
results = {}
for name, logK in logK_values.items():
    K = 10 ** logK
    x = free_gd_concentration(K, C0)
    pct = (x / C0) * 100
    results[name] = (K, logK, x, pct)

# -----------------------------------------------------------
# 결과 표
# -----------------------------------------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 계산 결과")
    table_rows = []
    for name, (K, logK, x, pct) in results.items():
        table_rows.append(
            {
                "조영제": name,
                "log K": f"{logK:.2f}",
                "자유 Gd³⁺ 농도 (mol/L)": f"{x:.3e}",
                "자유 비율 (%)": f"{pct:.3e}",
            }
        )
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.info(
        f"현재 초기 농도 C0 = {C0:.0e} mol/L 기준입니다. "
        "사이드바에서 log K를 바꾸면 표와 그래프가 실시간으로 업데이트됩니다."
    )

# -----------------------------------------------------------
# 그래프 1: log K vs 자유 Gd3+ 농도 (연속 곡선 + 각 조영제 위치)
# -----------------------------------------------------------
with col2:
    st.subheader("📈 log K에 따른 자유 Gd³⁺ 농도 변화")

    logK_range = np.linspace(10, 30, 300)
    free_conc = [free_gd_concentration(10 ** lk, C0) for lk in logK_range]

    fig1, ax1 = plt.subplots(figsize=(6, 4.5))
    ax1.plot(logK_range, free_conc, color="#2b6cb0", linewidth=2)
    ax1.set_yscale("log")
    ax1.set_xlabel("log K")
    ax1.set_ylabel("자유 Gd³⁺ 농도 (mol/L)")
    ax1.grid(True, which="both", linestyle="--", alpha=0.4)

    colors = ["#e53e3e", "#dd6b20", "#38a169", "#805ad5"]
    for (name, (K, logK, x, pct)), color in zip(results.items(), colors):
        ax1.scatter([logK], [x], color=color, zorder=5, s=60)

    st.pyplot(fig1)

st.divider()

# -----------------------------------------------------------
# 그래프 2: 막대그래프 비교
# -----------------------------------------------------------
st.subheader("📊 조영제별 자유 Gd³⁺ 비율 비교")

fig2, ax2 = plt.subplots(figsize=(10, 4.5))
names = list(results.keys())
percents = [results[n][3] for n in names]
short_names = [n.split(" (")[0] for n in names]

bars = ax2.bar(range(len(names)), percents, color=colors)
ax2.set_yscale("log")
ax2.set_xticks(range(len(names)))
ax2.set_xticklabels(short_names, fontsize=10)
ax2.set_ylabel("자유 Gd³⁺ 비율 (%)")
ax2.grid(True, axis="y", which="both", linestyle="--", alpha=0.4)

for bar, pct in zip(bars, percents):
    ax2.annotate(
        f"{pct:.1e}%",
        (bar.get_x() + bar.get_width() / 2, bar.get_height()),
        textcoords="offset points",
        xytext=(0, 5),
        ha="center",
        fontsize=9,
    )

st.pyplot(fig2)

st.caption(
    "⚠️ 그래프의 기본 log K 값은 참고용 근사치입니다. "
    "실제 탐구 보고서에는 본인이 조사한 문헌 출처의 정확한 값을 사용하세요."
)
