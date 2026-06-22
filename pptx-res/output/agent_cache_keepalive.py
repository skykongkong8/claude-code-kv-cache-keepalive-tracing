#!/usr/bin/env python3
"""Build the cache-keepalive verdict deck (Korean) from pptx-res inputs."""
import os
import sys
from dataclasses import replace

PLUGIN_ROOT = "/home/skykongkong/.claude/plugins/cache/axlabs/axlabs-mckinsey-pptx/0.2.0"
sys.path.insert(0, PLUGIN_ROOT)

from mckinsey_pptx import PresentationBuilder, DEFAULT_THEME
from mckinsey_pptx.theme import Typography

KO_THEME = replace(
    DEFAULT_THEME,
    typography=replace(DEFAULT_THEME.typography, family="Apple SD Gothic Neo"),
    copyright_text="ⓒ 2026 AX Labs",
)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

b = PresentationBuilder(theme=KO_THEME, default_section_marker="캐시 킵얼라이브 검증")

# Slide 1 — Cover
b.add(
    "cover_slide",
    title="Claude Code KV-캐시를 살려둘 가치가 있는가?",
    subtitle="구독 과금 환경에서 cache-keepalive 플러그인 실측 A/B 검증",
    client="Claude Code v2.1.18x · Claude Pro · Opus 4.8",
    date="2026-06-22 · 라이브 중첩 세션 5종",
    confidentiality="INTERNAL",
)

# Slide 2 — Executive summary (the answer, up front)
b.add(
    "dark_navy_summary",
    body=(
        "결론: 이 환경에서 플러그인은 절약이 없고 쿼터만 소모한다 — "
        "캐시 TTL이 1시간이라 7분 유휴는 자체로 캐시가 유지되며, "
        "모든 킵얼라이브 핑은 5시간 쿼터를 깎는 불필요 요청이다. 끄는 것을 권고한다."
    ),
    eyebrow="cache-keepalive 검증",
)

# Slide 3 — Three takeaways
b.add(
    "executive_summary_takeaways",
    title="세 가지 핵심 결론",
    sections=[
        {
            "takeaway": "이 환경의 캐시 TTL은 5분이 아니라 1시간",
            "bullets": [
                "write 토큰 466,136개 100%가 ephemeral_1h 사용",
                "ephemeral_5m 사용량은 0개",
                "플러그인 전제(300초 TTL 격파)가 성립하지 않음",
            ],
        },
        {
            "takeaway": "7분 유휴 후에도 플러그인 없이 캐시는 따뜻함",
            "bullets": [
                "7분 4개 암 모두 유휴 직후 캐시-read 우세 (35k~45k read)",
                "write는 거의 0, 콜드 재작성 없음",
                "ON 암이 얻은 이득을 OFF 암도 공짜로 누림",
            ],
        },
        {
            "takeaway": "킵얼라이브 핑 하나하나가 낭비된 구독 요청",
            "bullets": [
                "구독 과금은 토큰이 아니라 요청 수로 청구",
                "기본값은 유휴당 최대 7회 핑 발사 가능",
                "토큰 이득 0 → 최대 7개 요청 낭비",
            ],
        },
    ],
    final_conclusion="이 구독 설치 환경에서는 플러그인을 끈 채로 둘 것을 권고한다.",
)

# Slide 4 — Context: what the plugin claims to do
b.add(
    "process_flow_horizontal",
    title="플러그인은 비싼 캐시 write를 값싼 캐시 read로 바꾼다",
    steps=[
        {"name": "유휴 시작", "description": "대화 유휴 구간 진입, 캐시 TTL 카운트다운 시작"},
        {"name": "킵얼라이브", "description": "Stop 훅이 약 240초 후 값싼 더미 턴 주입"},
        {"name": "캐시 유지", "description": "read로 TTL 갱신 → 캐시 따뜻하게 유지"},
        {"name": "이득 조건", "description": "유휴가 TTL 초과할 때만 절약 발생 (write 2.0x vs read 0.1x)"},
    ],
)

# Slide 5 — Method: faithful A/B across real idle gaps
b.add(
    "overview_areas",
    title="동일 베이스라인, 실제 벽시계 유휴로 구성한 5개 라이브 암",
    subtitle="워크로드 2종 × 플러그인 ON/OFF + 70분 TTL 탐침 암 1종",
    areas=[
        {"name": "wlA-off", "bullets": ["워크로드 A · TS API JSDoc", "플러그인 OFF", "7분 유휴"]},
        {"name": "wlA-on", "bullets": ["워크로드 A · TS API JSDoc", "플러그인 ON", "7분 유휴"]},
        {"name": "wlB-off", "bullets": ["워크로드 B · Python 오류경로", "플러그인 OFF", "7분 유휴"]},
        {"name": "wlB-on", "bullets": ["워크로드 B · Python 오류경로", "플러그인 ON", "7분 유휴"]},
        {"name": "ttl-long", "bullets": ["TTL 한계 탐침", "플러그인 OFF", "70분 단일 유휴"]},
    ],
    call_out="각 암 = 일회용 워크트리 · n=1",
    footnote="HEAD 분기 워크트리에서 편집 폐기, 전사 JSONL로 턴별 토큰 파싱 (비결정성 유의)",
)

# Slide 6 — Decisive chart: cache state at the gap boundary (gap-boundary.csv)
b.add(
    "grouped_column_chart",
    title="7분 유휴는 따뜻하게 유지, 70분 유휴만 콜드로 전환",
    description="유휴 직후 첫 실턴의 캐시 read vs write 토큰",
    data_label="캐시 토큰",
    data_unit="천 토큰",
    takeaway_header="핵심 시사점",
    categories=["ttl-long(70분)", "wlA-off", "wlA-on", "wlB-off", "wlB-on"],
    series=[
        {"name": "캐시 read", "values": [0, 36.9, 35.7, 43.8, 45.3]},
        {"name": "캐시 write", "values": [25.1, 0.0, 0.1, 1.3, 0.1]},
    ],
    takeaways=[
        "ttl-long만 read 0 / write 25,134 — 완전 콜드 재작성",
        "7분 4개 암은 read 우세, 캐시 생존",
        "TTL은 7~70분 사이로 묶임 (문서상 1시간과 일치)",
    ],
    source="gap-boundary.csv",
)

# Slide 7 — Every cache write used the 1-hour TTL (ttl-write-breakdown.csv)
b.add(
    "stat_hero",
    title="약 150턴 동안 5분 캐시 write는 단 한 건도 없었다",
    stat="100%",
    stat_label="ephemeral_1h를 사용한 write 토큰 비중 (총 466,136개)",
    context="ephemeral_5m write = 0개. 플러그인이 노리는 5분 TTL은 이 환경에 존재하지 않는다.",
    source_text="ttl-write-breakdown.csv",
)

# Slide 8 — Cache Hit Ratio: the plugin does not move it (kpis.csv CHR)
b.add(
    "column_comparison",
    title="따뜻한 암은 89~95%, 콜드 70분 암만 56%로 붕괴",
    description="캐시 히트율(CHR) = read / (read + write)",
    data_label="캐시 히트율",
    data_unit="%",
    takeaway_header="핵심 시사점",
    categories=["wlA-off", "wlB-on", "wlA-on", "wlB-off", "ttl-long"],
    values=[94.6, 90.6, 90.4, 89.1, 56.0],
    focus_index=4,
    takeaways=[
        "wlA-on(90.4%) ≈ wlA-off(94.6%)",
        "ON·OFF 차이는 캐시 효과가 아닌 워크로드 노이즈",
        "플러그인은 CHR을 끌어올리지 못함",
        "콜드 암만 유일하게 56%로 급락",
    ],
    source="kpis.csv (CHR)",
)

# Slide 9 — Keepalive mechanism works but is pointless here (keepalive-turns.csv)
b.add(
    "two_column_compare",
    title="ON 암은 각각 값싼 킵얼라이브 read 1회만 발사",
    left_label="wlA-on · t27 킵얼라이브 턴",
    right_label="wlB-on · t28 킵얼라이브 턴",
    left_items=[
        "캐시 read 35,691 토큰",
        "캐시 write 25 토큰",
        "출력 22 토큰 (0.1x 값싼 read)",
    ],
    right_items=[
        "캐시 read 44,355 토큰",
        "캐시 write 909 토큰",
        "출력 54 토큰 (0.1x 값싼 read)",
    ],
    left_color="blue",
    right_color="blue",
    show_arrow=False,
)

# Slide 10 — Counterfactual: when the plugin would win (counterfactual-5min-ttl.csv)
b.add(
    "grouped_column_chart",
    title="5분 TTL·API 과금이라면 유휴당 약 41,000 가중 토큰 절약",
    description="약 36k 프리픽스 기준 유휴당 가중 토큰",
    data_label="가중 토큰",
    data_unit="천 토큰",
    takeaway_header="반사실 시나리오",
    categories=["콜드 재작성(플러그인 없음)", "킵얼라이브 read(플러그인)"],
    series=[
        {"name": "가중 토큰", "values": [45.0, 3.6]},
    ],
    takeaways=[
        "콜드 재작성 36k x 1.25 ≈ 45,000",
        "킵얼라이브 read 36k x 0.10 ≈ 3,600",
        "유휴당 절약 약 41,400 — 단, +1 요청",
        "Aider·Cline 환경의 결과, 여기선 레버가 연결되지 않음",
    ],
    source="counterfactual-5min-ttl.csv",
)

# Slide 11 — Verdict matrix
b.add(
    "comparison_table",
    title="토큰 비용(API)은 거의 안 움직이고, 요청 비용(구독)은 오르기만 한다",
    subtitle="환경·유휴 조건별 플러그인 판정",
    options=["플러그인 없음", "플러그인 사용"],
    criteria=[
        {"name": "이 환경(1h TTL)·7분 유휴", "scores": [4, 1]},
        {"name": "가상 5분 TTL·7분 유휴", "scores": [1, 4]},
        {"name": "이 환경·1시간 초과 유휴", "scores": [2, 2]},
    ],
    recommended_index=0,
)

# Slide 12 — Recommendation
b.add(
    "executive_summary_takeaways",
    title="여기선 플러그인을 끈 채로 — 과금·TTL이 바뀔 때만 재검토",
    sections=[
        {
            "takeaway": "실행: 이 구독 설치에서 cache-keepalive 비활성 유지",
            "bullets": [
                "현재 1시간 TTL에서는 순수 오버헤드",
                "유휴는 자체로 캐시를 따뜻하게 유지",
            ],
        },
        {
            "takeaway": "재검토 트리거: API-키 과금 전환 + 전사에 ephemeral_5m write 관측",
            "bullets": [
                "두 조건이 동시에 성립할 때만 유효",
                "TTL은 계약이 아닌 환경 변수 (1h→5m, 2026/3 변경 전례)",
            ],
        },
        {
            "takeaway": "조치: 조건 충족 시 harness/run-all.py 재실행",
            "bullets": [
                "§6 반사실 분석이 실제 API 비용 절감을 예측",
            ],
        },
    ],
    final_conclusion="현 환경 권고: 플러그인 OFF 유지. 과금 또는 TTL 변경 시에만 재검토.",
)

# Appendix — Method robustness & limitations
b.add(
    "pros_cons",
    title="방법론 견고성과 한계",
    pros_label="견고한 근거",
    cons_label="한계 및 주의",
    pros=[
        "유휴 경계 캐시 상태는 턴 수에 무관하게 robust",
        "CHR도 턴 수 영향 없이 robust",
        "70분 단일 유휴 암이 TTL을 7~70분으로 고정",
    ],
    cons=[
        "암당 n=1",
        "Claude 비결정성으로 암 간 총량 교란 (45 vs 35턴)",
        "TTL을 분 단위로 정확히 특정하지 못함",
    ],
)

out_path = os.path.join(OUT_DIR, "cache-keepalive-verdict.pptx")
b.save(out_path)
print("saved:", out_path)
