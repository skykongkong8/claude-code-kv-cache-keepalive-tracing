# Experiment design — does `cache-keepalive` actually save tokens here?

## Goal
Empirically compare token usage **with vs without** the
[`cache-keepalive`](https://github.com/yujiachen-y/claude-code-cache-keepalive) plugin, for the **same input
prompts**, and produce intuitive graphs of (a) per-turn token-usage *rate* and (b) *total* tokens spent.
Report both the **subscription reality** (request/turn count — what this plan actually bills) and the
**API-billing counterfactual** (token cost that *would* be saved).

## Decisions (locked with the user)
- **Fidelity:** faithful — real `interval_seconds=240`, real interactive sessions, real idle gaps.
- **Scope:** *two-tier* — four short-gap arms (~7 min gap) **+** one long (>65 min) OFF-gap to pin the real
  TTL **+** a token-math counterfactual for the assumed 5-min-TTL case.
- **Repo edits:** discarded — each arm runs in a throwaway `git worktree` off `HEAD` (`f711958`); nothing merged.
- **Nested-session permissions:** user explicitly authorized `--dangerously-skip-permissions` for the nested
  sessions (throwaway worktrees, no network-destructive actions). Allow-rule added in
  `.claude/settings.local.json` scoped to `harness/*.py` + `git worktree`.

## Reframing finding (see `theory.md` §6)
This environment (Claude Code v2.1.18x) writes the cache with a **1-hour TTL** (100 % of 8.46 M write tokens),
**not** the 5-min TTL the plugin assumes. So the short-gap arms test the *real* situation (cache stays warm
regardless → plugin only adds turns), and the long arm probes the actual cooling point.

## Driver
No `tmux` in this environment → the driver is **pexpect**-based (`harness/run-arm.py`, primitives validated by
`harness/smoke.py`). It spawns a real interactive `claude`, sends turns, detects turn completion by polling the
session transcript JSONL for an assistant message with `stop_reason ∈ {end_turn, stop_sequence}`, injects idle
gaps, then collects the transcript + keep-alive log.

- **ON arm:** `claude --plugin-dir /tmp/cc-cache-keepalive/plugins/cache-keepalive --model opus
  --dangerously-skip-permissions`, defaults `interval=240, max_loops=7`. Per-arm `CCKA_STATE_DIR`/`CCKA_LOG`
  under the worktree so the keep-alive log is isolated.
- **OFF arm:** identical launch without `--plugin-dir`; the idle gap is a plain wait.

## Workloads (same prompts across ON/OFF)
- **WL-A — JSDoc the API service layer (TypeScript).** Turn 1: document every exported function in
  `apps/api/src/service.ts` + `apps/api/src/agentClient.ts`. Turn 2 (after gap): "also document the error
  codes / thrown errors." Verify (post-hoc, in worktree): `pnpm typecheck`.
- **WL-B — Python agent error-path tests.** Turn 1: add `pytest` cases (not `live_nim`) for the error/fallback
  paths in `apps/agent/src/lotto_agent/graph_explain.py` + `llm.py`. Turn 2 (after gap): "add one more test
  for the empty-response case." Verify: `pytest apps/agent/tests -m "not live_nim"`.

Both read across many files → large cached prefix; the decisive measurement is the **first real turn after the
gap**: `cache_creation_input_tokens` spike (cold) vs `cache_read` dominant (warm).

## Matrix
| Arm | Workload | Plugin | Gap | Purpose |
| :-- | :-- | :-- | :-- | :-- |
| `wlA-off` | A | OFF | ~7 min | baseline, warm-cache @1h TTL |
| `wlA-on`  | A | ON  | ~7 min | does keep-alive change anything @1h TTL? (expect: only extra turns) |
| `wlB-off` | B | OFF | ~7 min | baseline |
| `wlB-on`  | B | ON  | ~7 min | "" |
| `ttl-long`| A (light) | OFF | >65 min | pin real TTL: does the cache finally go cold past 1 h? |

## Metrics & KPIs (`harness/parse-usage.py`)
Per assistant turn: `input, cache_write (+5m/1h split), cache_read, output`, classified `real` vs `keepalive`
(triggering user text contains the keep-alive phrase). Per-arm aggregates:
- **CHR** = read / (read + write) — cache warmth.
- **CWT** = 1.0·input + 1.25·write₅ₘ + 2.0·write₁ₕ + 0.1·read + R_out·output — API-billing counterfactual cost.
- **ECM** = CWT / (all input billed at base) — effective multiplier (lower = better).
- **turns_total / turns_real / turns_keepalive** — the *subscription* cost (extra keep-alive turns = quota burn).

## Charts (`harness/make-charts.py`, `uv run --with matplotlib`)
1. Per-turn stacked bars (write vs read) over the session timeline, ON vs OFF — *token-usage rate*.
2. Grouped bar of total tokens by category, ON vs OFF — *total spent*.
3. Cumulative CWT line over wall-clock.
4. "Verdict" twin bar: token-CWT saved (API counterfactual) vs extra turns consumed (subscription reality).
5. CHR bar, ON vs OFF.
Fallback if matplotlib unavailable: emit Vega-Lite JSON + ASCII charts.

## Verification that the experiment is sound
- Parser totals reconcile with `jq` on the raw transcript (done for a sample: 57 turns, write 410,922,
  read 3,613,630 — exact match).
- ON arms: `keepalive.log` shows ≥1 "blocking Stop" per gap and the transcript contains the injected turn.
- OFF long arm: first real turn after >65 min shows non-trivial `cache_creation`.
- ON/OFF pairs start from identical worktrees (same baseline ref), same model, same prompts.

## Risks
- Quota burn / 5-hour limit → arms run sequentially, raw artifacts checkpointed per arm so partial results survive.
- TTL-refresh not contractual → if an ON arm still shows a post-gap write spike, that is itself reported.
- matplotlib may be absent → fallback defined.
