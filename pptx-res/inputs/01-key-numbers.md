# Key numbers — quick reference for the deck

Use these exact figures on slides. All measured from session transcript JSONL.

## Headline
- **Cache TTL in this environment:** 1 hour (not 5 minutes).
- **Verdict:** plugin is net-negative on a subscription plan. Recommendation: leave it off.

## TTL write breakdown (all 5 arms, ~150 turns)
- `ephemeral_5m_input_tokens`: **0** (0%)
- `ephemeral_1h_input_tokens`: **466,136** (100%)

## Gap-boundary (first real turn after the idle gap) — the decisive evidence
| arm      | gap    | turn | cache_write | cache_read | state |
|----------|--------|------|------------:|-----------:|-------|
| ttl-long | 70 min | t4   | 25,134      | 0          | COLD  |
| wlA-off  | 7 min  | t31  | 27          | 36,858     | warm  |
| wlA-on   | 7 min  | t28  | 127         | 35,716     | warm  |
| wlB-off  | 7 min  | t27  | 1,266       | 43,791     | warm  |
| wlB-on   | 7 min  | t29  | 149         | 45,264     | warm  |

## Per-arm KPIs
| arm      | turns (real/keepalive) | write   | read      | CHR   | CWT     | ECM   |
|----------|------------------------|--------:|----------:|------:|--------:|------:|
| wlA-off  | 45 / 0                 | 81,247  | 1,412,539 | 0.946 | 452,365 | 0.275 |
| wlA-on   | 35 / 1                 | 106,143 | 1,002,420 | 0.904 | 543,828 | 0.406 |
| wlB-off  | 30 / 0                 | 114,045 | 931,248   | 0.891 | 589,757 | 0.449 |
| wlB-on   | 33 / 1                 | 118,392 | 1,137,317 | 0.906 | 620,470 | 0.407 |
| ttl-long | 5 / 0                  | 46,309  | 58,914    | 0.560 | 119,041 | 0.947 |

- CHR = cache_read / (cache_read + cache_write). CWT = cost-weighted tokens (API counterfactual:
  1.0·input + 1.25·write_5m + 2.0·write_1h + 0.1·read + 5.0·output). ECM = CWT / base_uncached.

## Keepalive turns (proof the mechanism fired and is cheap)
| arm    | turn | cache_write | cache_read | output |
|--------|------|------------:|-----------:|-------:|
| wlA-on | t27  | 25          | 35,691     | 22     |
| wlB-on | t28  | 909         | 44,355     | 54     |

## 5-minute-TTL counterfactual (weighted tokens, ~36k prefix, per gap)
- cold rewrite (no plugin): 36k × 1.25 ≈ **45,000**
- keepalive read (plugin):  36k × 0.10 ≈ **3,600** (+~30 output)
- **plugin saving per gap:** ≈ **41,400** weighted tokens — but costs +1 request.

## Definitions for footnotes
- **Subscription billing:** quota = request count in a rolling 5-hour window → each keepalive ping
  is a wasted request.
- **API billing:** quota = token cost → where the plugin *would* pay off if TTL were 5 min.
- **Plugin defaults:** interval 240s × max_loops 7 ≈ 28 min of coverage — cannot span a >1h gap.
