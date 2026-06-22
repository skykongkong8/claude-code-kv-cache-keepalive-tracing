#!/usr/bin/env python3
"""
parse-usage.py — turn Claude Code transcript JSONL into per-turn usage rows + per-arm KPIs.

Usage:
    parse-usage.py RAW_DIR -o RESULTS_DIR [--keepalive-substr SUBSTR] [--rout FLOAT]

RAW_DIR layout (one subdir per experiment arm):
    RAW_DIR/<arm>/<session>.jsonl      # copied Claude Code transcript
    RAW_DIR/<arm>/cache-keepalive.log  # optional, for cross-checking ping count

Outputs:
    RESULTS_DIR/usage.csv  — one row per assistant turn (all arms)
    RESULTS_DIR/kpis.csv   — one row per arm (aggregates + CHR/CWT/ECM)

Pricing model (relative to 1.0x base input token):
    base input        1.00x
    cache write (5m)  1.25x
    cache write (1h)  2.00x
    cache read        0.10x
    output            R_out  (default 5.0 = Opus $15/$3 output:input ratio)
These are Anthropic's published multipliers; the absolute $ cancels out in ECM.
A turn is classified "keepalive" iff its triggering user message contains
--keepalive-substr (default matches the plugin's default keepalive_message).
"""
import argparse, csv, glob, json, os, sys

DEFAULT_KEEPALIVE_SUBSTR = "i need some time to think about the next move"

W_INPUT, W_WRITE_5M, W_WRITE_1H, W_READ = 1.0, 1.25, 2.0, 0.10


def text_of(content):
    """Flatten a message 'content' (str or list of blocks) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for b in content:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    out.append(b.get("text", ""))
                elif "content" in b and isinstance(b["content"], str):
                    out.append(b["content"])
            elif isinstance(b, str):
                out.append(b)
        return " ".join(out)
    return ""


def parse_transcript(path, keepalive_substr):
    """Yield per-assistant-turn dicts in file order, attributing each to the
    most recent preceding user message text (to classify real vs keepalive)."""
    last_user = ""
    last_user_is_keepalive = False
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            m = o.get("message")
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            if role == "user":
                last_user = text_of(m.get("content")).strip()
                last_user_is_keepalive = keepalive_substr.lower() in last_user.lower()
                continue
            if role != "assistant":
                continue
            u = m.get("usage")
            if not isinstance(u, dict):
                continue
            cc = u.get("cache_creation") or {}
            rows.append({
                "ts": o.get("timestamp", ""),
                "requestId": o.get("requestId", ""),
                "model": m.get("model", ""),
                "kind": "keepalive" if last_user_is_keepalive else "real",
                "user_snip": last_user[:60].replace("\n", " "),
                "input": int(u.get("input_tokens", 0) or 0),
                "cache_write": int(u.get("cache_creation_input_tokens", 0) or 0),
                "cache_write_5m": int(cc.get("ephemeral_5m_input_tokens", 0) or 0),
                "cache_write_1h": int(cc.get("ephemeral_1h_input_tokens", 0) or 0),
                "cache_read": int(u.get("cache_read_input_tokens", 0) or 0),
                "output": int(u.get("output_tokens", 0) or 0),
            })
    return rows


def cwt(r, rout):
    """Cost-weighted tokens: weight writes by their actual TTL tier."""
    return (W_INPUT * r["input"]
            + W_WRITE_5M * r["cache_write_5m"]
            + W_WRITE_1H * r["cache_write_1h"]
            + W_READ * r["cache_read"]
            + rout * r["output"])


def base_uncached(r, rout):
    """Counterfactual cost if every input token were billed at base 1.0x."""
    return (W_INPUT * (r["input"] + r["cache_write"] + r["cache_read"])
            + rout * r["output"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_dir")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--keepalive-substr", default=DEFAULT_KEEPALIVE_SUBSTR)
    ap.add_argument("--rout", type=float, default=5.0)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    arms = sorted(d for d in os.listdir(a.raw_dir)
                  if os.path.isdir(os.path.join(a.raw_dir, d)))
    if not arms:
        # allow pointing directly at a dir of jsonl files = single arm
        arms = ["."]

    all_rows, kpis = [], []
    for arm in arms:
        adir = os.path.join(a.raw_dir, arm)
        jsonls = sorted(glob.glob(os.path.join(adir, "*.jsonl")))
        rows = []
        for j in jsonls:
            rows += parse_transcript(j, a.keepalive_substr)
        for i, r in enumerate(rows):
            r["arm"] = arm
            r["turn"] = i + 1
            r["cwt"] = round(cwt(r, a.rout), 1)
            r["base_uncached"] = round(base_uncached(r, a.rout), 1)
        all_rows += rows

        real = [r for r in rows if r["kind"] == "real"]
        ka = [r for r in rows if r["kind"] == "keepalive"]
        s = lambda key, rs=rows: sum(r[key] for r in rs)
        write = s("cache_write"); read = s("cache_read")
        tot_cwt = sum(cwt(r, a.rout) for r in rows)
        tot_base = sum(base_uncached(r, a.rout) for r in rows)
        kpis.append({
            "arm": arm,
            "turns_total": len(rows),
            "turns_real": len(real),
            "turns_keepalive": len(ka),
            "input": s("input"),
            "cache_write": write,
            "cache_write_5m": s("cache_write_5m"),
            "cache_write_1h": s("cache_write_1h"),
            "cache_read": read,
            "output": s("output"),
            "CHR": round(read / (read + write), 4) if (read + write) else "",
            "CWT": round(tot_cwt, 1),
            "base_uncached": round(tot_base, 1),
            "ECM": round(tot_cwt / tot_base, 4) if tot_base else "",
        })

    if all_rows:
        cols = ["arm", "turn", "kind", "ts", "model", "input", "cache_write",
                "cache_write_5m", "cache_write_1h", "cache_read", "output",
                "cwt", "base_uncached", "requestId", "user_snip"]
        with open(os.path.join(a.out, "usage.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader(); w.writerows(all_rows)
    with open(os.path.join(a.out, "kpis.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(kpis[0].keys()) if kpis else ["arm"])
        w.writeheader(); w.writerows(kpis)

    # human-readable echo
    for k in kpis:
        print(f"[{k['arm']}] turns={k['turns_total']} "
              f"(real={k['turns_real']}, keepalive={k['turns_keepalive']})  "
              f"write={k['cache_write']:,} (5m={k['cache_write_5m']:,} "
              f"1h={k['cache_write_1h']:,})  read={k['cache_read']:,}  "
              f"CHR={k['CHR']}  CWT={k['CWT']:,}  ECM={k['ECM']}")
    print(f"\nwrote {os.path.join(a.out,'usage.csv')} and {os.path.join(a.out,'kpis.csv')}")


if __name__ == "__main__":
    main()
