"""adiFit — Streamlit 데모 앱.

탭1 핏 어드바이저(소비자·헤드라인) / 탭2 머천다이저 대시보드(내부·근거) /
탭3 검증(신뢰도 지표). 하나의 리뷰 분석 엔진, 두 개의 얼굴.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from adifit import config
from adifit.advisor import advise, groundedness
from adifit.evaluator import eval_extraction, load_gold
from adifit.llm import get_client
from adifit.pipeline import build_analysis
from adifit.schema import (
    ASPECT_KO,
    COMFORT_TAG_KO,
    CUSTOMER_TAG_KO,
    DESIGN_COLOR_TAG_KO,
    SIZE_SIGNAL_KO,
    USE_CASE_KO,
    VOC_ISSUE_TAG_KO,
    ComfortTag,
    CustomerTag,
    DesignColorTag,
    WIDTH_SIGNAL_KO,
    SizeSignal,
    UseCase,
    VocIssueTag,
    WidthSignal,
)

st.set_page_config(page_title="adiFit — 리뷰 기반 핏·VOC 인텔리전스", page_icon="👟", layout="wide")

# ---------- 스타일 (아디다스 톤: 블랙/화이트) ----------
st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem;}
      .adi-header {background:#000; color:#fff; padding:14px 20px; border-radius:8px; margin-bottom:6px;}
      .adi-header h1 {margin:0; font-size:1.5rem; letter-spacing:1px;}
      .adi-header p {margin:2px 0 0; color:#bbb; font-size:0.85rem;}
      .verdict {background:#f4f4f4; border-left:6px solid #000; padding:12px 16px; border-radius:4px; font-size:1.05rem; font-weight:600;}
      .action {background:#fff7e6; border-left:5px solid #f5a623; padding:10px 14px; margin:6px 0; border-radius:4px;}
      .badge {display:inline-block; padding:3px 10px; border-radius:12px; color:#fff; font-size:0.85rem; font-weight:700;}
      .cite {background:#fafafa; border:1px solid #eee; border-radius:6px; padding:8px 12px; margin:6px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# 검증된 팔레트 (dataviz validator: light surface, all PASS)
SENT_COLORS = {"positive": "#2E7D32", "neutral": "#BDBDBD", "negative": "#C62828"}  # 발산 녹/회/적 (양극 CVD ΔE 15.8)
SIZE_COLORS = {"runs_small": "#D95F02", "true_to_size": "#1B9E77", "runs_large": "#7570B3", "not_mentioned": "#CFCFCF"}  # 발산, CVD PASS
PRODUCT_COLORS = ["#0072B2", "#E69F00", "#009E73"]  # Okabe-Ito 범주형 (CVD ΔE 51.6)
CAT_COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00"]  # 다계열 범주형 (Okabe-Ito 6, CVD PASS)
CONF_COLORS = {"high": "#2E7D32", "medium": "#E69F00", "low": "#C62828"}
SIZE_ORDER = ["runs_small", "true_to_size", "runs_large"]


# ---------- 리소스 로딩 ----------
@st.cache_resource(show_spinner="분석 엔진 로딩 중… (리뷰 추출·색인)")
def load_client_and_analysis():
    client = get_client()
    analysis = build_analysis(client)
    return client, analysis


def _dom_label(dist: dict, enum_cls, ko_map) -> str:
    m = {k: v for k, v in dist.items() if k != enum_cls.not_mentioned.value and v > 0}
    if not m:
        return "-"
    return ko_map[enum_cls(max(m, key=m.get))]


def md_table(rows: list[dict]) -> str:
    """list[dict] → 마크다운 표. pyarrow(st.dataframe) 세그폴트 회피용 순수 텍스트 렌더."""
    if not rows:
        return "_데이터 없음_"
    cols = list(rows[0].keys())
    head = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = "\n".join(
        "| " + " | ".join(str(r.get(c, "")).replace("|", "/") for c in cols) + " |" for r in rows
    )
    return f"{head}\n{sep}\n{body}"


def size_dist_chart(insight):
    order = ["runs_small", "true_to_size", "runs_large", "not_mentioned"]
    labels = [SIZE_SIGNAL_KO[SizeSignal(o)] for o in order]
    vals = [insight.size_distribution.get(o, 0) for o in order]
    colors = [SIZE_COLORS[o] for o in order]
    fig = go.Figure(
        go.Bar(
            x=vals, y=labels, orientation="h", marker_color=colors,
            text=vals, textposition="auto", cliponaxis=False,
            hovertemplate="%{y}: %{x}건<extra></extra>",
        )
    )
    fig.update_layout(height=210, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="리뷰 수",
                      plot_bgcolor="white", showlegend=False)
    fig.update_yaxes(autorange="reversed")
    return fig


def aspect_chart(insight):
    aspects = insight.aspect_breakdown
    names = [ASPECT_KO[b.aspect] for b in aspects]
    fig = go.Figure()
    for sent, key in [("긍정", "positive"), ("중립", "neutral"), ("부정", "negative")]:
        fig.add_bar(
            name=sent,
            y=names,
            x=[getattr(b, key) for b in aspects],
            orientation="h",
            marker_color=SENT_COLORS[key],
            marker_line_width=1.5,
            marker_line_color="white",  # 2px 표면 간격
            hovertemplate="%{y} · " + sent + ": %{x}건<extra></extra>",
        )
    fig.update_layout(
        barmode="stack", height=max(240, 44 * len(names)),
        margin=dict(l=10, r=10, t=10, b=10), xaxis_title="언급 수", plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return fig


def size_share_comparison_chart(analysis):
    """상품별 사이즈 신호 100% 비중 비교 — '어떤 신발이 작게 나오나'를 한눈에."""
    fig = go.Figure()
    names = [pname for _, pname in analysis.products]
    for sig in SIZE_ORDER:
        shares = []
        for pid, _ in analysis.products:
            ins = analysis.insights[pid]
            mentioned = sum(ins.size_distribution.get(s, 0) for s in SIZE_ORDER)
            shares.append(round(100 * ins.size_distribution.get(sig, 0) / mentioned) if mentioned else 0)
        fig.add_bar(
            name=SIZE_SIGNAL_KO[SizeSignal(sig)], y=names, x=shares, orientation="h",
            marker_color=SIZE_COLORS[sig], marker_line_width=1.5, marker_line_color="white",
            text=[f"{v}%" if v >= 8 else "" for v in shares], textposition="inside", insidetextanchor="middle",
            hovertemplate="%{y} · " + SIZE_SIGNAL_KO[SizeSignal(sig)] + ": %{x}%<extra></extra>",
        )
    fig.update_layout(
        barmode="stack", height=max(220, 70 * len(names)),
        margin=dict(l=10, r=10, t=10, b=10), xaxis_title="사이즈 언급 대비 비중 (%)", plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(range=[0, 100])
    return fig


def rating_comparison_chart(analysis):
    names = [pname for _, pname in analysis.products]
    vals = [analysis.insights[pid].avg_rating for pid, _ in analysis.products]
    fig = go.Figure(
        go.Bar(
            x=names, y=vals, marker_color=PRODUCT_COLORS[: len(names)],
            text=[f"{v:.2f}" for v in vals], textposition="outside", cliponaxis=False,
            hovertemplate="%{x}: 평점 %{y}<extra></extra>",
        )
    )
    fig.update_layout(height=280, margin=dict(l=10, r=10, t=20, b=10), yaxis_title="평균 평점",
                      plot_bgcolor="white", showlegend=False)
    fig.update_yaxes(range=[0, 5])
    return fig


def segment_scatter_chart(segment_analysis):
    df = pd.DataFrame(segment_analysis.points)
    if df.empty:
        return go.Figure()
    fig = px.scatter(
        df,
        x="x",
        y="y",
        color="segment",
        symbol="product",
        hover_data={
            "review_id": True,
            "product": True,
            "rating": True,
            "use_cases": True,
            "comfort": True,
            "issues": True,
            "x": False,
            "y": False,
        },
        labels={"segment": "세그먼트", "product": "상품"},
        color_discrete_sequence=CAT_COLORS,
        height=430,
    )
    fig.update_traces(marker=dict(size=12, line=dict(width=1, color="white")))
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Embedding PC1",
        yaxis_title="Embedding PC2",
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return fig


def voc_trend_chart(segment_analysis):
    df = pd.DataFrame(segment_analysis.trend_rows)
    fig = go.Figure()
    if df.empty:
        return fig
    issue_cols = {
        "fit_risk": "핏/사이즈",
        "durability": "내구성",
        "delivery_packaging": "배송/포장",
        "price_resistance": "가격 저항",
        "comfort_complaint": "착용감 불만",
    }
    monthly = df.groupby("month", as_index=False)[list(issue_cols)].sum()
    for i, (col, label) in enumerate(issue_cols.items()):
        color = CAT_COLORS[i % len(CAT_COLORS)]
        fig.add_scatter(
            x=monthly["month"],
            y=monthly[col],
            mode="lines+markers",
            name=label,
            line=dict(color=color, width=2),
            marker=dict(color=color, size=8),
            hovertemplate="%{x} · " + label + ": %{y}건<extra></extra>",
        )
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="VOC 이슈 태그 수",
        xaxis_title="월",
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_yaxes(dtick=1)
    return fig


def use_case_trend_chart(segment_analysis):
    df = pd.DataFrame(segment_analysis.trend_rows)
    fig = go.Figure()
    if df.empty:
        return fig
    use_cols = {
        "running": "러닝",
        "daily": "일상",
        "commute": "출퇴근",
        "race": "대회",
    }
    monthly = df.groupby("month", as_index=False)[list(use_cols)].sum()
    for i, (col, label) in enumerate(use_cols.items()):
        fig.add_bar(
            x=monthly["month"],
            y=monthly[col],
            name=label,
            marker_color=CAT_COLORS[i % len(CAT_COLORS)],
            marker_line_width=1.5,
            marker_line_color="white",
            hovertemplate="%{x} · " + label + ": %{y}건<extra></extra>",
        )
    fig.update_layout(
        barmode="stack",
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="사용 맥락 태그 수",
        xaxis_title="월",
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_yaxes(dtick=1)
    return fig


def _pairs_text(pairs: list[tuple[str, int]]) -> str:
    return " · ".join(f"{name} {count}" for name, count in pairs) if pairs else "-"


def product_context_rows(analysis):
    rows = []
    for pid, pname in analysis.products:
        reviews = [r for r in analysis.analyzed if r.product_id == pid]
        use_cases = {}
        comfort = {}
        design = {}
        issues = {}
        for r in reviews:
            for x in r.extraction.use_cases:
                use_cases[USE_CASE_KO[x]] = use_cases.get(USE_CASE_KO[x], 0) + 1
            for x in r.extraction.comfort_tags:
                comfort[COMFORT_TAG_KO[x]] = comfort.get(COMFORT_TAG_KO[x], 0) + 1
            for x in r.extraction.design_color_tags:
                design[DESIGN_COLOR_TAG_KO[x]] = design.get(DESIGN_COLOR_TAG_KO[x], 0) + 1
            for x in r.extraction.voc_issue_tags:
                issues[VOC_ISSUE_TAG_KO[x]] = issues.get(VOC_ISSUE_TAG_KO[x], 0) + 1

        def top(d):
            return " · ".join(f"{k} {v}" for k, v in sorted(d.items(), key=lambda item: -item[1])[:3]) or "-"

        rows.append(
            {
                "상품": pname,
                "주요 용도": top(use_cases),
                "착용감/성능": top(comfort),
                "디자인/색상": top(design),
                "주요 VOC": top(issues),
            }
        )
    return rows


def build_report_md(insight, reviews) -> str:
    issues = insight.top_issues or ["(없음)"]
    lines = [
        f"# adiFit VOC 리포트 — {insight.product_name}",
        "",
        f"- 리뷰 수: {insight.n_reviews}건 · 평균 평점: {insight.avg_rating}",
        f"- 사이즈 결론: {insight.size_verdict}",
        f"- 발볼 결론: {insight.width_verdict}",
        "",
        "## 상위 이슈",
        *[f"- {t}" for t in issues],
        "",
        "## 실행 제안 (VOC → 액션)",
        *[f"- {a}" for a in insight.action_recommendations],
        "",
        "## 속성별 감성 (언급 수)",
    ]
    for b in insight.aspect_breakdown:
        lines.append(
            f"- {ASPECT_KO[b.aspect]}: 긍정 {b.positive} · 중립 {b.neutral} · 부정 {b.negative} (순점수 {b.net_score:+.2f})"
        )
    return "\n".join(lines)


# ---------- 헤더 ----------
st.markdown(
    '<div class="adi-header"><h1>adiFit 👟</h1>'
    '<p>리뷰 기반 핏·사용맥락·VOC 인텔리전스 — 하나의 분석 엔진, 두 개의 얼굴</p></div>',
    unsafe_allow_html=True,
)

if not config.GEMINI_API_KEY:
    st.error("GEMINI_API_KEY가 설정되지 않았습니다. `.env`에 무료 키를 넣어주세요 (https://aistudio.google.com/apikey).")
    st.stop()

client, analysis = load_client_and_analysis()

# ---------- 사이드바 ----------
with st.sidebar:
    st.markdown("### 상품 선택")
    pid_to_name = dict(analysis.products)
    product_id = st.selectbox(
        "상품", options=[p[0] for p in analysis.products],
        format_func=lambda x: pid_to_name[x], label_visibility="collapsed",
    )
    st.caption(f"백엔드: `{config.LLM_MODEL}` · 임베딩 `{config.EMBED_MODEL}`")
    st.caption(f"리뷰 {len(analysis.analyzed)}건 · 상품 {len(analysis.products)}종 · 세그먼트 {len(analysis.segments.summaries)}개")
    st.divider()
    st.caption("데이터: 아디다스 데모 큐레이션 리뷰(직접 정의). 파이프라인은 언어·소스 무관.")

insight = analysis.insights[product_id]

tab_advisor, tab_dash, tab_compare, tab_segments, tab_eval = st.tabs(
    [
        "🧑‍💻 핏 어드바이저 (소비자)",
        "📊 머천다이저 대시보드 (내부)",
        "🆚 상품 비교",
        "🧬 세그먼트 & 트렌드",
        "✅ 검증 (신뢰도)",
    ]
)

# ========== 탭1: 핏 어드바이저 ==========
with tab_advisor:
    st.subheader(f"{pid_to_name[product_id]} — 핏 어드바이저")
    st.caption("데모 리뷰 근거로만 사이즈를 추천합니다. 근거 밖 추측은 하지 않습니다.")
    c1, c2 = st.columns(2)
    with c1:
        usual = st.text_input("평소 신는 사이즈 (선택)", placeholder="예: 265, 또는 나이키 270")
    with c2:
        width = st.radio("발볼", ["모름", "좁음", "보통", "넓음"], horizontal=True)
    query = st.text_input("질문", placeholder="예: 이거 정사이즈로 사면 될까요?")
    go_btn = st.button("사이즈 추천 받기", type="primary")

    if go_btn and query.strip():
        ctx_parts = []
        if usual.strip():
            ctx_parts.append(f"평소 사이즈 {usual.strip()}")
        if width != "모름":
            ctx_parts.append(f"발볼 {width}")
        user_ctx = ", ".join(ctx_parts) or None
        with st.spinner("리뷰 근거를 검색하고 분석하는 중…"):
            advice, results = advise(client, analysis.retriever, query, product_id, user_ctx=user_ctx)
            g = groundedness(advice, results)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f'<div class="verdict">👟 추천: {advice.recommended_size}</div>', unsafe_allow_html=True)
        with col2:
            c = CONF_COLORS[advice.confidence.value]
            st.markdown(
                f'확신도 <span class="badge" style="background:{c}">{advice.confidence.value.upper()}</span> · '
                f'근거성 {g["grounded_ratio"]*100:.0f}%',
                unsafe_allow_html=True,
            )
        st.write(advice.rationale)
        if advice.caveats:
            st.info(f"⚠️ {advice.caveats}")

        with st.expander(f"🔍 근거가 된 리뷰 {len(advice.citations)}건 (인용)", expanded=True):
            id_to_review = {r.review_id: r for r, _ in results}
            for cit in advice.citations:
                rv = id_to_review.get(cit.review_id)
                meta = ""
                if rv:
                    e = rv.extraction
                    meta = f" · 평점 {rv.rating} · 사이즈신호 {SIZE_SIGNAL_KO[e.size_signal]} · 발볼 {WIDTH_SIGNAL_KO[e.width_signal]}"
                st.markdown(
                    f'<div class="cite"><b>[{cit.review_id}]</b>{meta}<br>“{cit.quote}”</div>',
                    unsafe_allow_html=True,
                )
    elif go_btn:
        st.warning("질문을 입력해주세요.")

# ========== 탭2: 대시보드 ==========
with tab_dash:
    st.subheader(f"{pid_to_name[product_id]} — VOC 대시보드")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("리뷰 수", f"{insight.n_reviews}건")
    k2.metric("평균 평점", f"{insight.avg_rating}")
    k3.metric("사이즈 결론", _dom_label(insight.size_distribution, SizeSignal, SIZE_SIGNAL_KO))
    k4.metric("발볼 결론", _dom_label(insight.width_distribution, WidthSignal, WIDTH_SIGNAL_KO))

    st.markdown(f'<div class="verdict">📏 {insight.size_verdict}<br>🦶 {insight.width_verdict}</div>', unsafe_allow_html=True)

    st.download_button(
        "📥 VOC 리포트 다운로드 (.md)",
        data=build_report_md(insight, [x for x in analysis.analyzed if x.product_id == product_id]),
        file_name=f"adiFit_report_{product_id}.md",
        mime="text/markdown",
    )

    st.markdown("#### 실행 제안 (VOC → 액션)")
    for a in insight.action_recommendations:
        st.markdown(f'<div class="action">→ {a}</div>', unsafe_allow_html=True)

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown("#### 속성별 감성")
        st.plotly_chart(aspect_chart(insight), use_container_width=True)
    with cc2:
        st.markdown("#### 사이즈 신호 분포")
        st.plotly_chart(size_dist_chart(insight), use_container_width=True)
        if insight.top_issues:
            st.markdown("#### 상위 이슈")
            for t in insight.top_issues:
                st.markdown(f"- {t}")

    with st.expander("📝 이 상품 리뷰 원문 + 추출 결과"):
        for r in [x for x in analysis.analyzed if x.product_id == product_id]:
            e = r.extraction
            asp = ", ".join(f"{ASPECT_KO[a.aspect]}({a.sentiment.value[:3]})" for a in e.aspects)
            usage = ", ".join(USE_CASE_KO[x] for x in e.use_cases) or "-"
            comfort = ", ".join(COMFORT_TAG_KO[x] for x in e.comfort_tags) or "-"
            design = ", ".join(DESIGN_COLOR_TAG_KO[x] for x in e.design_color_tags) or "-"
            st.markdown(
                f"**[{r.review_id}]** 평점 {r.rating} · 사이즈 **{SIZE_SIGNAL_KO[e.size_signal]}** · 발볼 {WIDTH_SIGNAL_KO[e.width_signal]}  \n"
                f"“{r.text}”  \n"
                f"_{asp}_  \n"
                f"사용맥락: `{usage}` · 착용감: `{comfort}` · 디자인/색상: `{design}`"
            )

# ========== 탭3: 상품 비교 ==========
with tab_compare:
    st.subheader("상품 비교 — 어떤 신발이 정사이즈인가?")
    st.caption("모든 상품을 한눈에. 사이즈 신호 비중과 평점을 나란히 비교합니다.")

    rows = []
    for pid, pname in analysis.products:
        ins = analysis.insights[pid]
        rows.append(
            {
                "상품": pname,
                "리뷰": ins.n_reviews,
                "평점": ins.avg_rating,
                "사이즈 결론": _dom_label(ins.size_distribution, SizeSignal, SIZE_SIGNAL_KO),
                "발볼": _dom_label(ins.width_distribution, WidthSignal, WIDTH_SIGNAL_KO),
                "대표 이슈": ins.top_issues[0] if ins.top_issues else "-",
            }
        )
    st.markdown(md_table(rows))

    cc1, cc2 = st.columns([3, 2])
    with cc1:
        st.markdown("#### 사이즈 신호 비중 (상품별)")
        st.caption("주황(작게 나옴) 막대가 길수록 사이즈 업이 필요한 상품.")
        st.plotly_chart(size_share_comparison_chart(analysis), use_container_width=True)
    with cc2:
        st.markdown("#### 평균 평점")
        st.plotly_chart(rating_comparison_chart(analysis), use_container_width=True)

# ========== 탭4: 세그먼트 & 트렌드 ==========
with tab_segments:
    st.subheader("리뷰 세그먼트 & VOC 트렌드")
    st.caption("리뷰 임베딩 클러스터링 + LLM 구조화 태그로 고객 사용 맥락을 분리합니다. 현재 수치는 데모 샘플 기준입니다.")

    c1, c2, c3 = st.columns(3)
    c1.metric("세그먼트", f"{len(analysis.segments.summaries)}개")
    c2.metric("태그 추출 리뷰", f"{sum(1 for r in analysis.analyzed if r.extraction.use_cases or r.extraction.comfort_tags or r.extraction.design_color_tags)}건")
    c3.metric("월별 관측점", f"{len(analysis.segments.trend_rows)}개")

    st.markdown("#### Embedding Clusters")
    st.plotly_chart(segment_scatter_chart(analysis.segments), use_container_width=True)

    st.markdown("#### 상품별 사용 맥락 요약")
    st.markdown(md_table(product_context_rows(analysis)))

    st.markdown("#### 세그먼트 요약")
    for seg in analysis.segments.summaries:
        with st.expander(f"{seg.label} · {seg.n_reviews}건 · 평균 평점 {seg.avg_rating}", expanded=True):
            m1, m2, m3 = st.columns(3)
            m1.markdown(f"**상품**  \n{', '.join(seg.product_names)}")
            m2.markdown(f"**사용 맥락**  \n{_pairs_text(seg.top_use_cases)}")
            m3.markdown(f"**사이즈 믹스**  \n{_pairs_text(seg.size_mix)}")

            t1, t2, t3 = st.columns(3)
            t1.markdown(f"**착용감**  \n{_pairs_text(seg.top_comfort_tags)}")
            t2.markdown(f"**디자인/색상**  \n{_pairs_text(seg.top_design_color_tags)}")
            t3.markdown(f"**고객/VOC**  \n{_pairs_text(seg.top_customer_tags + seg.top_issue_tags)}")

            st.markdown(f'<div class="action">→ {seg.action}</div>', unsafe_allow_html=True)
            st.markdown("대표 리뷰")
            for r in seg.representative_reviews:
                st.markdown(f"- **[{r.review_id}] {r.product_name}** · 평점 {r.rating}: “{r.text}”")

    st.markdown("#### VOC Time-series")
    st.caption("실서비스에서는 수천~수만 건 리뷰에서 이슈 spike와 고객 세그먼트 drift를 추적하는 형태로 확장합니다.")
    tc1, tc2 = st.columns(2)
    with tc1:
        st.markdown("##### 월별 VOC 이슈")
        st.plotly_chart(voc_trend_chart(analysis.segments), use_container_width=True)
    with tc2:
        st.markdown("##### 월별 사용 맥락")
        st.plotly_chart(use_case_trend_chart(analysis.segments), use_container_width=True)

# ========== 탭5: 검증 ==========
with tab_eval:
    st.subheader("검증 — 측정된 신뢰도")
    st.caption("'그럴듯함'이 아니라 수치로 증명. 직접 라벨링한 골드셋 기준.")
    gold = load_gold()
    ev = eval_extraction(analysis.analyzed, gold)
    m1, m2 = st.columns(2)
    m1.metric("사이즈 신호 추출 정확도", f"{ev['accuracy']*100:.1f}%", help=f"골드셋 {ev['n']}건 기준")
    n_wrong = sum(1 for r in ev["rows"] if not r["correct"])
    m2.metric("불일치", f"{n_wrong}건 / {ev['n']}건")
    st.markdown("##### 라벨 비교 (불일치는 🔴)")
    st.markdown(
        md_table(
            [
                {"review_id": r["review_id"], "gold": r["gold"], "예측": r["pred"], "일치": "✅" if r["correct"] else "🔴"}
                for r in ev["rows"]
            ]
        )
    )
    st.info(
        "어드바이저 **근거성(groundedness)** 은 답변마다 실시간 계산됩니다 — 인용된 review_id가 "
        "실제 검색 근거에 존재하는 비율. 핏 어드바이저 탭에서 질문하면 각 답변 옆에 표시됩니다. "
        "사전 테스트 3케이스 평균 citation coverage **100%**."
    )
