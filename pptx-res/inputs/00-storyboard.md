# Presentation brief — "Does the cache-keepalive plugin save tokens here?"

**Deck purpose:** Decision deck. Answer one question with evidence: should we run the
`cache-keepalive` Claude Code plugin on this subscription-billed environment?
**Audience:** Engineering / platform decision-makers (technical, time-poold).
**Tone:** McKinsey consulting — answer-first, one idea per slide, action title on every slide.
**Length:** ~12 slides. **Language:** English.
**Recommended deck:** cover → executive summary → context → method → 3–4 evidence slides →
counterfactual → verdict matrix → recommendation → appendix.

> Source data lives in `inputs/data/*.csv`; pre-rendered charts in `inputs/images/*.png`.
> Each slide below names the McKinsey template to use and the exact data/image to bind.

---

## Slide 1 — Cover
- **Template:** cover slide
- **Title:** Keeping the Claude Code KV-cache alive — is it worth it here?
- **Subtitle:** An empirical A/B of the `cache-keepalive` plugin on a subscription-billed install
- **Footnote:** Claude Code v2.1.18x · Claude Pro · Opus 4.8 · 2026-06-22 · 5 live nested sessions

## Slide 2 — Executive summary (the answer, up front)
- **Template:** `dark_navy_summary` (dark navy statement slide)
- **Body:** On this environment the plugin **saves nothing and costs quota**. Claude Code here
  writes the prompt cache with a **1-hour TTL**, so a normal idle pause (tested at 7 minutes)
  leaves the cache **fully warm on its own**. Every keepalive ping is therefore a **redundant
  request** billed against the subscription's 5-hour quota. Recommendation: **leave it off.**

## Slide 3 — Three takeaways
- **Template:** `executive_summary_takeaways`
- **sections:**
  1. takeaway: "Cache TTL here is 1 hour, not 5 minutes" —
     bullets: 100% of 466,136 write tokens used `ephemeral_1h`; 0 used `ephemeral_5m`.
     The plugin's core premise ("beat the 300s TTL") does not apply.
  2. takeaway: "At a 7-min gap the cache stays warm without the plugin" —
     bullets: First turn after the gap was cache-read-dominated in all four 7-min arms
     (35k–45k read, near-zero write). ON arms gained nothing OFF arms didn't have for free.
  3. takeaway: "Each keepalive ping is a wasted subscription request" —
     bullets: Subscription bills request count, not tokens; defaults can fire up to 7 pings
     per idle pause → up to 7 wasted requests for zero token benefit.

## Slide 4 — Context: what the plugin claims to do
- **Template:** process flow (3 steps)
- **Title:** The plugin trades an expensive cache *write* for a cheap cache *read*
- **Flow:** Idle gap starts → `Stop` hook sleeps ~240s, injects a cheap keepalive turn →
  cache TTL refreshes on read, staying warm. Pricing: write = 1.25x (5m) / 2.0x (1h),
  read = 0.1x. Payoff only exists if the gap would otherwise exceed the TTL.

## Slide 5 — Method: a faithful A/B across real idle gaps
- **Template:** comparison table / 2x2 matrix
- **Title:** Five live nested sessions, identical baselines, real wall-clock gaps
- **Matrix rows:** Workload A (JSDoc the TS API layer) · Workload B (Python error-path tests)
- **Matrix cols:** plugin OFF · plugin ON
- **Plus:** a 5th arm `ttl-long` — plugin OFF, single 70-minute gap, to find where the cache dies.
- **Footnote:** Each arm = throwaway git worktree off HEAD, edits discarded; per-turn token
  usage parsed from the session transcript JSONL. n=1 per arm (non-determinism noted).

## Slide 6 — THE decisive chart: cache state at the gap boundary
- **Template:** clustered bar chart (image)
- **Image:** `inputs/images/chart-gap-boundary.png`
- **Data:** `inputs/data/gap-boundary.csv`
- **Title:** 7-minute gaps stay warm; only the 70-minute gap goes cold
- **Callout:** ttl-long t4 = read 0 / write 25,134 (a full cold rewrite) — the lone red bar.
  All four 7-min arms = tall blue read bars (cache survived). TTL is bracketed to 7–70 min,
  consistent with the documented 1 hour.

## Slide 7 — Every cache write used the 1-hour TTL
- **Template:** KPI / single-stat bar (image + stat)
- **Image:** `inputs/images/chart-totals.png` (supporting)
- **Data:** `inputs/data/ttl-write-breakdown.csv`
- **Big stat:** 100% — share of write tokens (466,136) that used `ephemeral_1h`. `ephemeral_5m` = 0.
- **Title:** Not a single 5-minute cache write across ~150 turns

## Slide 8 — Cache Hit Ratio: the plugin does not move it
- **Template:** bar chart (image)
- **Image:** `inputs/images/chart-chr.png`
- **Data:** `inputs/data/kpis.csv` (CHR column)
- **Title:** Warm arms cluster at 0.89–0.95; only the cold 70-min arm collapses to 0.56
- **Callout:** wlA-on (0.904) ≈ wlA-off (0.946); the difference is workload noise, not a cache
  effect. The plugin does not lift CHR.

## Slide 9 — The keepalive mechanism works — it is just pointless here
- **Template:** small table + annotation
- **Data:** `inputs/data/keepalive-turns.csv`
- **Title:** Each ON arm fired exactly 1 cheap keepalive read — refreshing a cache that wasn't expiring
- **Callout:** wlA-on t27: read 35,691 / out 22. wlB-on t28: read 44,355 / out 54. The trick is
  real (cheap read at 0.1x), but in a 1h-TTL world it refreshes something that didn't need it.

## Slide 10 — When the plugin *would* win (5-minute-TTL counterfactual)
- **Template:** waterfall / before-after bar
- **Data:** `inputs/data/counterfactual-5min-ttl.csv`
- **Title:** On a 5-min-TTL, API-billed install the plugin would save ~41,000 weighted tokens per gap
- **Callout:** cold rewrite 36k x 1.25 ≈ 45,000 vs keepalive read 36k x 0.10 ≈ 3,600. That is the
  Aider/Cline/SillyTavern result — the lever simply isn't connected here.

## Slide 11 — Verdict: good on API billing, bad on subscription
- **Template:** 2x2 decision matrix (BCG-style) or two-axis verdict bar
- **Image:** `inputs/images/chart-verdict.png`
- **Title:** Token cost (API) barely moves; request cost (subscription) only rises
- **Matrix:**
  - This env (1h TTL), 7-min gap → **Without plugin wins** (plugin = pure overhead)
  - Hypothetical 5-min TTL, 7-min gap → With plugin wins (the case it's built for)
  - This env, >1h gap → Neither at default settings (defaults cover only ~28 min)

## Slide 12 — Recommendation
- **Template:** `dark_navy_summary` or action-plan slide
- **Title:** Leave the plugin off here — revisit only if billing or TTL changes
- **Bullets:**
  - Do: keep `cache-keepalive` disabled on this subscription install.
  - Trigger to revisit: switch to API-key billing AND observe `ephemeral_5m` writes in transcripts.
  - Then: re-run `harness/run-all.py`; the §6 counterfactual predicts a real API-dollar saving.
  - Note: TTL is environmental, not contractual — Anthropic changed it before (1h→5m, 3/2026).

## Appendix slide (optional) — Method robustness & limitations
- **Template:** bullet list / footnote slide
- **Points:** n=1 per arm; cross-arm raw totals confounded by Claude non-determinism (45 vs 35
  turns), so the load-bearing metrics are per-turn gap-boundary state and CHR — both robust to
  turn count. One long-gap arm pins TTL to "7–70 min," not the exact minute.
- **Supporting images:** `chart-per-turn-rate.png`, `chart-cumulative-cwt.png`.
