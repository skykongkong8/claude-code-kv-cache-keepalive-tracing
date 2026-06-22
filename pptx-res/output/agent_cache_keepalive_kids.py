#!/usr/bin/env python3
"""Kids version (12-year-old level) of the cache-keepalive verdict deck.

Same diagrams, charts, numbers and verdict as agent_cache_keepalive.py.
Only the explanation changes: everything is told with the "book on the desk"
analogy in simple Korean. One idea per slide.
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

b = PresentationBuilder(theme=KO_THEME, default_section_marker="책상 위의 책 이야기")

# Slide 1 — Cover
b.add(
    "cover_slide",
    title="책을 톡톡 건드리는 친구가 정말 필요할까?",
    subtitle="AI의 '캐시'를 쉬운 비유로 풀어 보는 이야기",
    client="Claude Code · 쉬운 버전",
    date="2026-06-22",
    confidentiality="이야기로 배우기",
)

# Slide 2 — The answer up front, in plain words
b.add(
    "dark_navy_summary",
    body=(
        "결론: 지금 환경에선 이 친구(플러그인)를 꺼두는 게 좋아요. "
        "책은 알아서 1시간 동안 책상에 펼쳐져 있으니까요. "
        "7분 자리를 비워도 책은 그대로예요. 그래서 톡톡 건드릴 필요가 없어요."
    ),
    eyebrow="쉬운 버전",
    corner_text="AX Labs",
)

# Slide 3 — Analogy 1: what the cache is (a book left open on the desk)
b.add(
    "three_trends_icons",
    title="AI는 매번 처음부터 다시 읽어야 해요 — 그래서 '책'을 펼쳐 둬요",
    subtitle="AI한테 말을 걸 때마다 일어나는 일",
    trends=[
        {
            "label": "매번 다시 읽기",
            "icon": "📖",
            "bullets": [
                "AI는 한 마디 할 때마다",
                "지금까지 한 이야기를 처음부터 다시 읽어요",
                "그래서 시간이 오래 걸려요",
            ],
        },
        {
            "label": "책상에 펼쳐 두기",
            "icon": "🔖",
            "bullets": [
                "그래서 책(대화)을 책상에 펼쳐 둬요",
                "이게 바로 '캐시'예요",
                "펼쳐 두면 다음에 빨리 볼 수 있어요",
            ],
        },
        {
            "label": "다시 보면 빨라요",
            "icon": "⚡",
            "bullets": [
                "이미 펼쳐진 책을 보는 건 쉽고 빨라요",
                "처음부터 펼치는 것보다 훨씬 싸요",
                "그게 캐시를 쓰는 이유예요",
            ],
        },
    ],
)

# Slide 4 — Analogy 2: warm book vs cold book
b.add(
    "two_column_compare",
    title="책이 '따뜻하다' vs '식었다(콜드)' — 무슨 뜻일까요?",
    left_label="따뜻한 책 (그대로 펼쳐져 있음)",
    right_label="식은 책 (덮여서 다시 펼쳐야 함)",
    left_items=[
        "책이 책상에 그대로 펼쳐져 있어요",
        "보던 페이지를 바로 다시 볼 수 있어요",
        "빠르고, 거의 공짜예요",
    ],
    right_items=[
        "누가 책을 덮어 버렸어요",
        "처음부터 다시 펼쳐야 해요",
        "오래 걸리고, 비싸요",
    ],
    left_color="blue",
    right_color="amber",
    show_arrow=True,
)

# Slide 5 — Analogy 3: write (open the book) vs read (look at open book)
b.add(
    "stat_hero",
    title="책을 '새로 펼치기'는 비싸고, '펼쳐진 책 보기'는 싸요",
    stat="10배",
    stat_label="펼쳐진 책을 보는 건, 책을 새로 펼치는 것보다 훨씬 싸요",
    context="책을 새로 펼치기(cache write)는 힘들고 비싸요. 이미 펼쳐진 책 보기(cache read)는 쉽고 싸요. 차이가 10배도 넘어요.",
)

# Slide 6 — Analogy 4: TTL = how long the desk stays untouched
b.add(
    "stat_hero",
    title="책상은 1시간 동안 안 치워요 — 이게 'TTL'이에요",
    stat="1시간",
    stat_label="자리를 비워도 책이 그대로 펼쳐져 있는 시간 (TTL)",
    context="여기선 책상을 1시간 동안 안 치워요. 그래서 7분쯤 자리를 비워도 책은 그대로 펼쳐져 있어요. 1시간이 지나야 누가 책을 덮어 버려요.",
)

# Slide 7 — Analogy 5: the plugin = the friend who taps the book
b.add(
    "three_trends_icons",
    title="플러그인은 '혹시 책 치울까 봐' 책을 톡톡 건드리는 친구예요",
    subtitle="이 친구가 하는 일과, 그 대가",
    trends=[
        {
            "label": "톡톡 건드리기",
            "icon": "👆",
            "bullets": [
                "7분마다 책을 톡톡 건드려요",
                "'책 치우지 마세요!' 하는 거예요",
                "책을 따뜻하게(펼쳐진 채) 두려는 거죠",
            ],
        },
        {
            "label": "그런데…",
            "icon": "🤔",
            "bullets": [
                "여긴 1시간 동안 책을 안 치워요",
                "7분 가지고는 책이 안 덮여요",
                "그래서 건드릴 필요가 없어요",
            ],
        },
        {
            "label": "티켓 낭비",
            "icon": "🎟️",
            "bullets": [
                "건드릴 때마다 '요청 티켓' 한 장을 써요",
                "아낀 건 없는데 티켓만 닳아요",
                "그래서 손해예요",
            ],
        },
    ],
)

# Slide 8 — Subscription = ticket bundle
b.add(
    "stat_hero",
    title="우리 요금제는 '티켓'으로 닳아요 — 글자 수가 아니라요",
    stat="5시간",
    stat_label="이만큼의 시간 동안 쓸 수 있는 '요청 티켓 묶음'이 있어요",
    context="구독 요금제는 글자(토큰)를 얼마나 썼는지가 아니라, 몇 번 부탁(요청)했는지로 닳아요. 책을 톡톡 건드리는 것도 티켓 한 장을 그냥 써 버리는 거예요.",
)

# Slide 9 — What we tested
b.add(
    "overview_areas",
    title="우리는 다섯 가지 경우를 직접 해 봤어요",
    subtitle="친구(플러그인)를 켰을 때와 껐을 때를 비교했어요",
    areas=[
        {"name": "가-끄기", "bullets": ["숙제 A", "친구 꺼둠", "7분 쉼"]},
        {"name": "가-켜기", "bullets": ["숙제 A", "친구 켜둠", "7분 쉼"]},
        {"name": "나-끄기", "bullets": ["숙제 B", "친구 꺼둠", "7분 쉼"]},
        {"name": "나-켜기", "bullets": ["숙제 B", "친구 켜둠", "7분 쉼"]},
        {"name": "오래-쉬기", "bullets": ["한계 실험", "친구 꺼둠", "70분 쉼"]},
    ],
    call_out="다섯 번 모두 실제로 해 봤어요",
)

# Slide 10 — How we counted (kid-friendly data provenance)
b.add(
    "three_trends_icons",
    title="숫자는 어떻게 셌을까요? — AI가 스스로 '영수증'을 줬어요",
    subtitle="우리가 손으로 일일이 센 게 아니에요",
    trends=[
        {
            "label": "AI가 영수증을 줘요",
            "icon": "🧾",
            "bullets": [
                "AI는 대답할 때마다",
                "'책 새로 펼친 양·펼쳐진 책 본 양'을",
                "영수증처럼 같이 알려줘요",
            ],
        },
        {
            "label": "공책에 적어 둬요",
            "icon": "📒",
            "bullets": [
                "그 영수증이 컴퓨터 공책(파일)에",
                "한 줄씩 차곡차곡 저장돼요",
                "우리가 고치거나 지운 적 없어요",
            ],
        },
        {
            "label": "모아서 세요",
            "icon": "🔢",
            "bullets": [
                "작은 프로그램이 그 공책을 읽어",
                "다섯 경우의 숫자를 모아 줘요",
                "그래서 믿을 수 있어요",
            ],
        },
    ],
)

# Slide 11 — Decisive chart: cache state at the gap boundary (same data)
b.add(
    "grouped_column_chart",
    title="7분 쉬면 책은 그대로! 70분 쉬어야 책이 덮여요",
    description="쉬고 돌아왔을 때, 펼쳐진 책을 봤는지(read) 새로 펼쳤는지(write)",
    data_label="책 보기 양",
    data_unit="천 번",
    takeaway_header="여기서 알 수 있는 것",
    categories=["오래-쉬기(70분)", "가-끄기", "가-켜기", "나-끄기", "나-켜기"],
    series=[
        {"name": "펼쳐진 책 보기 (싸요)", "values": [0, 36.9, 35.7, 43.8, 45.3]},
        {"name": "책 새로 펼치기 (비싸요)", "values": [25.1, 0.0, 0.1, 1.3, 0.1]},
    ],
    takeaways=[
        "70분 쉰 경우만 책을 새로 펼쳤어요 (비쌈)",
        "7분 쉰 네 경우는 책이 그대로 펼쳐져 있었어요",
        "그러니까 7분으론 책이 안 덮여요",
    ],
    source="gap-boundary.csv",
)

# Slide 12 — All writes were 1-hour, no 5-minute (same data, kid words)
b.add(
    "stat_hero",
    title="150번 넘게 봤는데 '5분짜리 책상'은 한 번도 없었어요",
    stat="100%",
    stat_label="책을 새로 펼친 경우는 전부 '1시간짜리 책상'이었어요",
    context="플러그인 친구는 '5분 책상'을 걱정해요. 그런데 여긴 5분 책상이 아예 없었어요. 다 1시간 책상이라 걱정할 일이 없었어요.",
    source_text="ttl-write-breakdown.csv",
)

# Slide 13 — Cache hit ratio (same data)
b.add(
    "column_comparison",
    title="7분 쉰 경우는 거의 다 잘했고, 70분 쉰 경우만 점수가 뚝 떨어졌어요",
    description="펼쳐진 책을 얼마나 잘 다시 봤는지 점수 (높을수록 좋아요)",
    data_label="잘한 점수",
    data_unit="점",
    takeaway_header="여기서 알 수 있는 것",
    categories=["가-끄기", "나-켜기", "가-켜기", "나-끄기", "오래-쉬기"],
    values=[94.6, 90.6, 90.4, 89.1, 56.0],
    focus_index=4,
    takeaways=[
        "친구 켠 경우(90점)와 끈 경우(95점)가 거의 같아요",
        "그러니 친구가 점수를 올려 준 게 아니에요",
        "70분 쉰 경우만 56점으로 뚝 떨어졌어요",
    ],
    source="kpis.csv (CHR)",
)

# Slide 14 — Counterfactual: when the friend would help (same data)
b.add(
    "grouped_column_chart",
    title="만약 책상이 '5분'이었다면? 그땐 친구가 도움이 됐을 거예요",
    description="책상이 5분만에 치워진다면, 한 번 쉴 때 드는 비용",
    data_label="드는 비용",
    data_unit="천 번",
    takeaway_header="만약에 이야기",
    categories=["책 새로 펼치기(친구 없음)", "톡톡 건드리기(친구 있음)"],
    series=[
        {"name": "드는 비용", "values": [45.0, 3.6]},
    ],
    takeaways=[
        "책을 새로 펼치면 비용이 약 45,000",
        "톡톡 건드리면 약 3,600",
        "그러면 약 41,000을 아껴요",
        "하지만 지금 책상은 1시간이라 해당 안 돼요",
    ],
    source="counterfactual-5min-ttl.csv",
)

# Slide 15 — Verdict, friendly
b.add(
    "pros_cons",
    title="그래서 친구를 켜는 게 좋을까, 끄는 게 좋을까?",
    pros_label="끄면 좋은 점",
    cons_label="켜면 생기는 일",
    pros=[
        "티켓을 아껴요 (괜한 톡톡이 없어요)",
        "책은 1시간 동안 알아서 펼쳐져 있어요",
        "7분 쉬어도 아무 문제 없어요",
    ],
    cons=[
        "톡톡 건드릴 때마다 티켓 한 장씩 써요",
        "그런데 아끼는 건 하나도 없어요",
        "그냥 손해만 봐요",
    ],
)

# Slide 16 — Final takeaway
b.add(
    "dark_navy_summary",
    body=(
        "한 줄 정리: 친구(플러그인)를 꺼두세요. "
        "책은 1시간 동안 알아서 펼쳐져 있으니까, "
        "7분쯤 자리를 비워도 괜찮아요. 톡톡 건드리면 티켓만 아까워요."
    ),
    eyebrow="마무리",
    corner_text="AX Labs",
)

out_path = os.path.join(OUT_DIR, "cache-keepalive-verdict-kids.pptx")
b.save(out_path)
print("saved:", out_path)
