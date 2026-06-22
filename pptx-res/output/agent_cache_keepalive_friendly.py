#!/usr/bin/env python3
"""Friendly / detailed-theory Korean version of the cache-keepalive verdict deck.

Same diagrams, charts, numbers and verdict as agent_cache_keepalive.py.
Only the explanation style changes: concepts are unpacked for a general
technical reader who is not familiar with agent token economics.
"""
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
    subtitle="개념부터 차근차근 — 구독 과금 환경에서 cache-keepalive 플러그인 실측 A/B 검증",
    client="Claude Code v2.1.18x · Claude Pro · Opus 4.8",
    date="2026-06-22 · 라이브 중첩 세션 5종",
    confidentiality="INTERNAL",
)

# Slide 2 — Executive summary (the answer, up front)
b.add(
    "dark_navy_summary",
    body=(
        "결론: 이 환경에서 플러그인은 비용을 줄이지 못하고 구독 쿼터만 소모한다 — "
        "캐시 유효시간(TTL)이 1시간이라 7분 정도 쉬는 것으로는 캐시가 스스로 살아있고, "
        "킵얼라이브 핑은 절약 없이 5시간 요청 쿼터만 깎는다. 끄는 것을 권고한다."
    ),
    eyebrow="cache-keepalive 검증",
)

# Slide 3 — Agenda so the reader knows the path
b.add(
    "agenda",
    title="이 보고서를 읽는 순서",
    items=[
        "배경 개념: 프롬프트 캐시란 무엇인가",
        "배경 개념: 구독 과금 vs API 과금",
        "이 실험이 알아내려던 것 (A/B 설계)",
        "실측 결과: 캐시 상태·히트율·TTL 분해",
        "판정과 권고",
    ],
    active_index=0,
)

# ── 개념 설명 블록 (Version 1 추가분) ───────────────────────────────

# Slide 4 — Concept 1: what is a prompt cache (process_flow makes the loop concrete)
b.add(
    "process_flow_horizontal",
    title="개념 ①: 프롬프트 캐시 — LLM이 매 턴 대화 전체를 다시 읽는 비용을 줄이는 장치",
    steps=[
        {
            "name": "프리픽스 재전송",
            "description": "매 턴 LLM은 지금까지의 대화 전체(프리픽스)를 다시 입력으로 읽어야 함",
        },
        {
            "name": "cache write (비쌈)",
            "description": "처음 읽을 때 캐시에 저장 — 입력 토큰의 1.25x(5분)~2.0x(1시간) 가중 비용",
        },
        {
            "name": "cache read (쌈)",
            "description": "이미 저장된 프리픽스를 재사용 — 입력 토큰의 0.1x, 즉 10분의 1",
        },
        {
            "name": "TTL 만료 → 콜드",
            "description": "유효시간(TTL)이 지나면 캐시가 사라짐 → 다시 비싼 write 발생",
        },
    ],
    footnote="가중 비용 배수는 Anthropic 프롬프트 캐싱 가격 모델 기준 (write 1.25x/2.0x, read 0.1x)",
)

# Slide 5 — Concept 1 deepened: warm vs cold, with the two-column compare
b.add(
    "two_column_compare",
    title="캐시가 '따뜻하다' vs '콜드'다 — 같은 대화를 이어가도 비용이 10배 이상 갈린다",
    left_label="따뜻한 캐시 (cache read)",
    right_label="콜드 캐시 (cache write 재발생)",
    left_items=[
        "TTL이 아직 안 지나 프리픽스가 살아있음",
        "재사용 비용 = 입력 토큰 x 0.1 (싼 read)",
        "유휴(쉬는 구간)가 TTL보다 짧으면 자동으로 유지됨",
    ],
    right_items=[
        "TTL이 지나 프리픽스가 사라짐",
        "처음부터 다시 저장 = x1.25~x2.0 (비싼 write)",
        "유휴가 TTL보다 길 때만 발생",
    ],
    left_color="blue",
    right_color="amber",
    show_arrow=True,
)

# Slide 6 — Concept 2: subscription vs API billing
b.add(
    "two_column_compare",
    title="개념 ②: 구독 과금 vs API 과금 — '무엇으로 비용이 닳는가'가 다르다",
    left_label="구독 과금 (Claude Pro)",
    right_label="API 과금 (API 키)",
    left_items=[
        "5시간 롤링 윈도우의 '요청 수'로 청구",
        "토큰을 많이 써도 한 요청은 한 요청",
        "캐시로 토큰을 아껴도 요청 쿼터는 그대로 닳음",
    ],
    right_items=[
        "실제 사용한 '토큰 비용'으로 청구",
        "토큰을 아끼면 곧바로 돈이 절약됨",
        "캐시 read(0.1x)가 직접적인 비용 절감",
    ],
    left_color="navy",
    right_color="gray",
    show_arrow=False,
    footnote="이 차이가 플러그인의 가치를 가른다 — 구독에선 토큰을 아껴도 요청 쿼터가 별도로 닳는다",
)

# Slide 7 — Concept 2 punchline: why this decides plugin value
b.add(
    "stat_hero",
    title="그래서 핵심 질문은 하나: 이 환경에서 캐시는 절약을 만드는가?",
    stat="0.1x vs 1.25x",
    stat_label="cache read 대 cache write의 가중 비용 배수 — 플러그인은 비싼 write를 싼 read로 바꿔 절약하려 함",
    context="단, 구독 과금에선 절약된 토큰이 '돈'이 아니라 '요청 쿼터'와 무관하다. 핑 한 번은 요청 한 장을 그대로 소모한다.",
)

# Slide 8 — Concept 3: what the experiment set out to learn
b.add(
    "executive_summary_takeaways",
    title="개념 ③: 이 실험이 알아내려던 세 가지",
    sections=[
        {
            "takeaway": "이 환경의 실제 캐시 유효시간(TTL)은 몇 분인가",
            "bullets": [
                "플러그인은 '5분 TTL'을 전제로 핑을 보냄",
                "전사 로그에서 ephemeral_5m vs ephemeral_1h write를 분해해 확인",
            ],
        },
        {
            "takeaway": "7분 쉬면 캐시는 따뜻하게 살아남는가, 콜드가 되는가",
            "bullets": [
                "실제 벽시계 유휴 직후 첫 턴의 캐시 read/write를 측정",
                "유휴 경계(gap-boundary)에서 캐시 생존 여부를 직접 관찰",
            ],
        },
        {
            "takeaway": "플러그인이 캐시 히트율(CHR)을 실제로 끌어올리는가",
            "bullets": [
                "CHR = 캐시 read / (read + write), 1에 가까울수록 캐시 효율 좋음",
                "ON 암과 OFF 암의 CHR을 나란히 비교",
            ],
        },
    ],
    final_conclusion="요약하면: TTL이 정말 5분인지, 7분 유휴로 콜드가 되는지, 플러그인이 효과가 있는지를 실측으로 확인한다.",
)

# Slide 9 — Method: faithful A/B across real idle gaps (same data as base deck)
b.add(
    "overview_areas",
    title="동일 베이스라인, 실제 벽시계 유휴로 구성한 5개 라이브 암",
    subtitle="워크로드 2종 × 플러그인 ON/OFF + 70분 TTL 탐침 암 1종 (각 암 n=1)",
    areas=[
        {"name": "wlA-off", "bullets": ["워크로드 A · TS API JSDoc", "플러그인 OFF", "7분 유휴"]},
        {"name": "wlA-on", "bullets": ["워크로드 A · TS API JSDoc", "플러그인 ON", "7분 유휴"]},
        {"name": "wlB-off", "bullets": ["워크로드 B · Python 오류경로", "플러그인 OFF", "7분 유휴"]},
        {"name": "wlB-on", "bullets": ["워크로드 B · Python 오류경로", "플러그인 ON", "7분 유휴"]},
        {"name": "ttl-long", "bullets": ["TTL 한계 탐침", "플러그인 OFF", "70분 단일 유휴"]},
    ],
    call_out="각 암 = 일회용 워크트리 · n=1",
    footnote="HEAD 분기 워크트리에서 편집 폐기, 전사 JSONL로 턴별 토큰 파싱 (Claude 비결정성 유의)",
)

# Slide 10 — How the token data was collected (data provenance)
b.add(
    "process_flow_horizontal",
    title="이 숫자들은 어떻게 모았나 — 토큰 사용량은 Anthropic 서버가 응답마다 직접 돌려준다",
    steps=[
        {
            "name": "서버가 usage 반환",
            "description": "매 응답에 cache_read·cache_write·ephemeral_5m/1h·output 토큰 수가 포함됨 (추정이 아닌 실측치)",
        },
        {
            "name": "전사 JSONL 기록",
            "description": "Claude Code가 세션 대화를 ~/.claude/projects/.../<세션>.jsonl에 메시지 단위로 저장",
        },
        {
            "name": "파서로 턴별 추출",
            "description": "harness/parse-usage.py가 어시스턴트 턴마다 usage를 읽고 real/keepalive로 분류",
        },
        {
            "name": "암별 집계·교차검증",
            "description": "CHR·CWT로 합산하고 jq로 원본 전사 합계와 대조해 일치 확인",
        },
    ],
    footnote="핵심 수치(ephemeral_5m=0, ephemeral_1h=100%)는 서버가 직접 내려준 값이라 'TTL=1시간' 근거가 반박 불가",
)

# Slide 11 — Decisive chart: cache state at the gap boundary (gap-boundary.csv)
b.add(
    "grouped_column_chart",
    title="7분 유휴는 캐시를 따뜻하게 유지, 70분 유휴만 콜드로 전환",
    description="유휴(쉬는 구간) 직후 첫 실턴에서 읽힌 캐시 read 토큰과 새로 쓴 write 토큰",
    data_label="캐시 토큰",
    data_unit="천 토큰",
    takeaway_header="핵심 시사점",
    categories=["ttl-long(70분)", "wlA-off", "wlA-on", "wlB-off", "wlB-on"],
    series=[
        {"name": "캐시 read (재사용·쌈)", "values": [0, 36.9, 35.7, 43.8, 45.3]},
        {"name": "캐시 write (재작성·비쌈)", "values": [25.1, 0.0, 0.1, 1.3, 0.1]},
    ],
    takeaways=[
        "ttl-long만 read 0 · write 25,134 — 캐시가 사라져 완전 재작성",
        "7분 4개 암은 read가 우세 → 캐시가 그대로 살아있었음",
        "즉 실제 TTL은 7분보다 길고 70분보다 짧음 (문서상 1시간과 일치)",
    ],
    source="gap-boundary.csv",
)

# Slide 12 — Every cache write used the 1-hour TTL (ttl-write-breakdown.csv)
b.add(
    "stat_hero",
    title="약 150턴 동안 '5분 캐시'에 쓴 토큰은 단 한 개도 없었다",
    stat="100%",
    stat_label="ephemeral_1h(1시간 TTL)를 사용한 write 토큰 비중 — 총 466,136개 전부",
    context="ephemeral_5m(5분 TTL) write = 0개. 플러그인이 격파하려는 '5분 TTL'은 이 환경에 아예 존재하지 않는다.",
    source_text="ttl-write-breakdown.csv",
)

# Slide 13 — Cache Hit Ratio: the plugin does not move it (kpis.csv CHR)
b.add(
    "column_comparison",
    title="따뜻한 암은 캐시 히트율 89~95%, 콜드 70분 암만 56%로 붕괴",
    description="캐시 히트율(CHR) = 캐시 read / (read + write) · 1에 가까울수록 캐시가 잘 재사용됨",
    data_label="캐시 히트율",
    data_unit="%",
    takeaway_header="핵심 시사점",
    categories=["wlA-off", "wlB-on", "wlA-on", "wlB-off", "ttl-long"],
    values=[94.6, 90.6, 90.4, 89.1, 56.0],
    focus_index=4,
    takeaways=[
        "플러그인 ON(90.4%)과 OFF(94.6%)가 사실상 동일",
        "ON·OFF 차이는 캐시 효과가 아니라 워크로드 노이즈",
        "즉 플러그인은 캐시 히트율을 끌어올리지 못함",
        "콜드 암(ttl-long)만 유일하게 56%로 급락",
    ],
    source="kpis.csv (CHR)",
)

# Slide 14 — Keepalive mechanism works but is pointless here (keepalive-turns.csv)
b.add(
    "two_column_compare",
    title="플러그인은 작동은 한다 — 다만 값싼 read 한 번을 보낼 뿐, 콜드가 없어 무의미",
    left_label="wlA-on · t27 킵얼라이브 턴",
    right_label="wlB-on · t28 킵얼라이브 턴",
    left_items=[
        "캐시 read 35,691 토큰 (이미 따뜻한 캐시를 읽음)",
        "캐시 write 25 토큰 (거의 0)",
        "출력 22 토큰 — 0.1x 값싼 read 한 번",
    ],
    right_items=[
        "캐시 read 44,355 토큰 (이미 따뜻한 캐시를 읽음)",
        "캐시 write 909 토큰 (거의 0)",
        "출력 54 토큰 — 0.1x 값싼 read 한 번",
    ],
    left_color="blue",
    right_color="blue",
    show_arrow=False,
    footnote="핑은 정상 작동하지만 이미 따뜻한 캐시를 한 번 더 데우는 것이라 절약이 0이다",
)

# Slide 15 — Counterfactual: when the plugin would win (counterfactual-5min-ttl.csv)
b.add(
    "grouped_column_chart",
    title="만약 5분 TTL·API 과금이었다면 유휴당 약 41,000 가중 토큰을 아꼈을 것",
    description="약 36k 프리픽스 기준 — 유휴 한 번당 발생하는 가중 토큰 (반사실 시나리오)",
    data_label="가중 토큰",
    data_unit="천 토큰",
    takeaway_header="반사실 시나리오",
    categories=["콜드 재작성(플러그인 없음)", "킵얼라이브 read(플러그인)"],
    series=[
        {"name": "가중 토큰", "values": [45.0, 3.6]},
    ],
    takeaways=[
        "콜드 재작성 = 36k x 1.25 ≈ 45,000 가중 토큰",
        "킵얼라이브 read = 36k x 0.10 ≈ 3,600 가중 토큰",
        "유휴당 절약 약 41,400 — 단, 요청은 +1회 추가",
        "Aider·Cline류 환경에선 유효하나, 여기선 레버가 연결돼 있지 않음",
    ],
    source="counterfactual-5min-ttl.csv",
)

# Slide 16 — Verdict matrix
b.add(
    "comparison_table",
    title="토큰 비용(API)은 거의 안 움직이고, 요청 비용(구독)은 오르기만 한다",
    subtitle="환경·유휴 조건별 플러그인 판정 (Harvey-ball: 채울수록 유리)",
    options=["플러그인 없음", "플러그인 사용"],
    criteria=[
        {"name": "이 환경(1h TTL)·7분 유휴", "scores": [4, 1]},
        {"name": "가상 5분 TTL·7분 유휴", "scores": [1, 4]},
        {"name": "이 환경·1시간 초과 유휴", "scores": [2, 2]},
    ],
    recommended_index=0,
)

# Slide 17 — Recommendation
b.add(
    "executive_summary_takeaways",
    title="여기선 플러그인을 끈 채로 — 과금·TTL이 바뀔 때만 재검토",
    sections=[
        {
            "takeaway": "실행: 이 구독 설치에서 cache-keepalive 비활성 유지",
            "bullets": [
                "현재 1시간 TTL에서는 순수 오버헤드 (절약 0)",
                "7분 유휴는 그 자체로 캐시를 따뜻하게 유지함",
            ],
        },
        {
            "takeaway": "재검토 트리거: API-키 과금 전환 + 전사에 ephemeral_5m write 관측",
            "bullets": [
                "두 조건이 동시에 성립할 때만 플러그인이 유효",
                "TTL은 계약이 아닌 환경 변수 (1h→5m로 바뀐 전례 2026/3)",
            ],
        },
        {
            "takeaway": "조치: 조건 충족 시 harness/run-all.py 재실행으로 재측정",
            "bullets": [
                "반사실 분석(슬라이드 14)이 실제 API 비용 절감을 예측",
            ],
        },
    ],
    final_conclusion="현 환경 권고: 플러그인 OFF 유지. 과금 방식 또는 TTL이 변할 때에만 재검토.",
)

# Slide 18 — Appendix: method robustness & limitations
b.add(
    "pros_cons",
    title="방법론 견고성과 한계",
    pros_label="견고한 근거",
    cons_label="한계 및 주의",
    pros=[
        "유휴 경계 캐시 상태는 턴 수에 무관하게 robust",
        "캐시 히트율(CHR)도 턴 수 영향 없이 robust",
        "70분 단일 유휴 암이 TTL을 7~70분으로 고정",
    ],
    cons=[
        "암당 n=1 (반복 측정 없음)",
        "Claude 비결정성으로 암 간 총량 교란 (45턴 vs 35턴)",
        "TTL을 분 단위로 정확히 특정하지는 못함",
    ],
)

out_path = os.path.join(OUT_DIR, "cache-keepalive-verdict-friendly.pptx")
b.save(out_path)
print("saved:", out_path)
