# cache-keepalive — empirical evaluation

Does the [`claude-code-cache-keepalive`](https://github.com/yujiachen-y/claude-code-cache-keepalive) plugin
actually save tokens? This directory holds a faithful A/B experiment (live nested `claude` sessions, real
idle gaps) plus the theory and the analysis.

## Read in this order
1. **[`claude-code-kv-cache-keepalive-분석.md`](./claude-code-kv-cache-keepalive-분석.md)** — how the plugin
   works + the original mechanism/strategy report (Korean).
2. **[`theory.md`](./theory.md)** — theoretical background with links/evidence, and the decisive local
   finding (this environment uses a **1-hour** cache TTL, not 5-min).
3. **[`00-experiment-design.md`](./00-experiment-design.md)** — methodology, matrix, metrics.
4. **[`findings.md`](./findings.md)** — results, charts, verdict.  ← the payoff

## Layout
```
harness/
  parse-usage.py   transcript JSONL -> results/usage.csv + kpis.csv (CHR/CWT/ECM)
  make-charts.py   results/*.csv -> results/*.png (+ ascii-summary.txt)
  run-arm.py       pexpect driver: one live arm (spawn, turns, idle gap, collect)
  smoke.py         pipeline self-tests (probe1 I/O, probe2 keepalive hook fires)
  keytest.py       one-off: bypass-dialog key probe (superseded; see findings)
raw/<arm>/         per-arm transcript JSONL + keepalive.log + stdout.log
results/           usage.csv, kpis.csv, *.png, ascii-summary.txt
```

## Reproduce
```bash
# one arm (OFF):
python3 harness/run-arm.py --label wlA-off --cwd /tmp/ccka-wlA-off --gap 420 \
    --raw raw --turn "PROMPT 1" --turn "PROMPT 2"
# one arm (ON):
python3 harness/run-arm.py --label wlA-on --cwd /tmp/ccka-wlA-on --plugin --interval 240 \
    --gap 420 --raw raw --turn "PROMPT 1" --turn "PROMPT 2"
# parse + chart:
python3 harness/parse-usage.py raw -o results
uv run --with matplotlib python harness/make-charts.py results
```

## Driver notes (hard-won; see findings.md §methodology)
- No `tmux` here → pexpect drives the real interactive TUI; a reader thread must continuously **drain** the
  PTY or the child blocks.
- Nested sessions must **scrub** inherited `CLAUDE_CODE*`/`CLAUDECODE` env, else they run as *child sessions*
  and never persist a transcript.
- Bypass-permission mode always shows a non-persistable warning dialog that the Kitty-protocol TUI won't let
  us navigate reliably → we use `--allowedTools <all standard tools>` for unattended autonomy instead.
- Turn completion is detected from the transcript (`stop_reason ∈ {end_turn, stop_sequence}`).
