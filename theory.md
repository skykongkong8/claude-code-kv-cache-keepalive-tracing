# Theoretical background & evidence — prompt-cache keep-alive

This document records the theory the `cache-keepalive` plugin rests on, the evidence for each claim, and
the one empirical fact from *this* environment that reframes the whole evaluation.

## 1. What the cache actually is (KV cache reuse)

LLM inference has two phases. **Prefill** runs the prompt prefix through every transformer layer and computes,
for each token, the Key/Value attention tensors — this is the expensive part and scales with prefix length.
**Decode** then generates output tokens, each attending over the already-computed KV tensors.

Anthropic's *prompt caching* stores the prefill KV tensors server-side, keyed by an exact prefix match up to a
`cache_control` breakpoint. On a hit, the server **loads** the tensors instead of **recomputing** them:

| Operation | What the server does | Published multiplier (× base input) |
| :-- | :-- | :-- |
| Base input | normal prefill | 1.0× |
| Cache **write** (5-min TTL) | prefill **+** store tensors | 1.25× |
| Cache **write** (1-hour TTL) | prefill **+** store tensors (longer) | 2.0× |
| Cache **read** | **load** stored tensors, skip prefill | **0.1×** |

A read is ~12.5× cheaper than a 5-min write and ~20× cheaper than a 1-hour write, for the same tokens.
*Evidence:* Anthropic prompt-caching docs — https://docs.claude.com/en/docs/build-with-claude/prompt-caching
(pricing & the 5m/1h TTL options).

## 2. The single invariant the plugin exploits

> **A successful cache read refreshes the cached prefix's TTL.**

If a prefix would expire in 30 s but you send any request that *reads* it, the TTL clock resets to full.
So a cheap "do-nothing" read just before expiry extends cache life by another TTL window, at read price.
*Evidence:* Anthropic docs state cache entries are refreshed on use ("Cache lifetime … refreshed each time the
cached content is used"); the prior-art tools below all rely on exactly this.

## 3. The break-even math

From the Cline community write-up (cspotcode), the clearest derivation:

> "If first message populates the cache at 1.25× cost, ping it 6 times at 0.1× cost, then send your second
> chat message … 1.25 + (6 + 1) × 0.1 = **1.95× cost for 2× requests**."

So on a 6-minute idle gap that would otherwise force two full 5-min writes (2.5×), six keep-alive pings cut it
to 1.95× — a ~22 % saving on that gap, growing as the gap lengthens.
*Evidence:* https://github.com/cline/cline/discussions/414

## 4. Prior art (same trick, other tools)

- **Aider** ships `--cache-keepalive-pings` as a built-in — https://aider.chat/docs/usage/caching.html
- **Cache-Refresh-SillyTavern** reports ~89 % cost reduction on long chats —
  https://github.com/OneinfinityN7/Cache-Refresh-SillyTavern
- **ClaudeMind** extends effective TTL 5 min → 60 min with ~12 pings; break-even = 2 follow-up questions.

The plugin under test ports this to Claude Code via a `Stop` hook that sleeps ~240 s then emits
`{"decision":"block","reason":"…"}`, forcing a cheap extra turn that reads the cached prefix.
*Evidence:* repo — https://github.com/yujiachen-y/claude-code-cache-keepalive ; mechanism dissected in
[`claude-code-kv-cache-keepalive-분석.md`](./claude-code-kv-cache-keepalive-분석.md).

## 5. Why the plugin exists: the March-2026 TTL regression

Anthropic silently lowered Claude Code's **default** prompt-cache TTL from 1 hour to 5 minutes in March 2026.
Users with normal >5-min thinking pauses began paying for full cache *rewrites* every turn; one user traced
~$949 (Sonnet-4.6) and ~$1,582 (Opus-4.6) of excess billing to it.
*Evidence:* https://github.com/anthropics/claude-code/issues/46829

## 6. ★ The decisive empirical fact in THIS environment

Before running anything, we parsed the local Claude Code transcripts
(`~/.claude/projects/-home-skykongkong-workstation-AICanWinLottery/*.jsonl`, Claude Code **v2.1.179–2.1.181**,
2026-06-22). Each assistant `message.usage.cache_creation` splits writes by TTL tier:

```
total cache_creation tokens : 8,462,428
  of which 5m-ephemeral     : 0          ← zero
  of which 1h-ephemeral     : 8,462,428  ← 100%
total cache_read tokens     : 73,155,222
```

**Every cache write in this environment uses the 1-hour TTL; none use the 5-minute TTL.** That is the exact
opposite of the precondition the plugin assumes. Consequences:

1. The cache survives idle gaps up to ~1 hour with **no** pinging. At the plugin's design timescale
   (240 s interval to beat a 300 s TTL), there is **nothing to save** here — the cache never went cold.
2. With defaults `interval=240, max_loops=7`, the plugin covers only ~28 min, so it could not even protect a
   genuine >1-hour gap without reconfiguration.
3. On this **subscription** plan (quota = request count, not token cost), each keep-alive turn is a pure
   debit against the 5-hour request quota with no offsetting token saving. → expected **net-negative**.

This is why the live experiment is framed as: *measure the real environment (1h TTL, subscription) AND the
5-min-TTL / API-billing counterfactual the report assumed, and let the token graphs show both.*

## 7. Caveats inherited from the mechanism

- "Reads refresh TTL" is documented behavior, **not** a contractual guarantee — Anthropic already changed TTL
  defaults once without notice; refresh semantics could change too.
- A keep-alive turn is a **real** turn: it appears in the transcript and consumes output tokens; a poorly
  chosen keep-alive message that triggers tools or long output stops being cheap.
- On subscription/request-metered plans the technique is counterproductive regardless of token math.
