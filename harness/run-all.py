#!/usr/bin/env python3
"""
run-all.py — orchestrate every experiment arm sequentially.

For each arm: create a throwaway git worktree off HEAD, run run-arm.py inside it
(real workload turns + idle gap), collect artifacts to raw/<label>/, remove the
worktree. Idempotent: an arm whose raw/<label>/*.jsonl already exists is skipped.

  python3 run-all.py [arm_label ...]      # default: all arms

Progress is appended to raw/run-all.log.
"""
import glob, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
TRACE = os.path.dirname(HERE)
REPO = os.path.dirname(TRACE)
RAW = os.path.join(TRACE, "raw")
RUN_ARM = os.path.join(HERE, "run-arm.py")
LOG = os.path.join(RAW, "run-all.log")

WL_A_1 = ("Add comprehensive JSDoc comments to every exported function in "
          "apps/api/src/service.ts and apps/api/src/agentClient.ts. Document purpose, "
          "parameters, return values, thrown errors, and the freshness and fallback "
          "branching behavior. Match the doc comment style already used in "
          "packages/data/src/sync.ts. Edit the files directly.")
WL_A_2 = "Now also add a short JSDoc note describing each thrown error code in those two files."

WL_B_1 = ("Add pytest test cases (do not mark them live_nim) covering the untested error and "
          "fallback paths in apps/agent/src/lotto_agent/graph_explain.py and "
          "apps/agent/src/lotto_agent/llm.py: timeout retry, secondary model fallback, and "
          "partial response handling. Extend apps/agent/tests/test_agent.py and mock the LLM. "
          "Edit the test file directly.")
WL_B_2 = "Add one more test for the empty LLM response case."

LONG_1 = "Read apps/api/src/service.ts and summarize its responsibilities in three bullet points."
LONG_2 = "Now read packages/data/src/provider.ts and summarize its responsibilities in three bullet points."

# label, plugin, interval, gap(s), turns, post_wait
ARMS = [
    ("wlA-off", False, 240,  420, [WL_A_1, WL_A_2], 0),
    ("wlA-on",  True,  240,  420, [WL_A_1, WL_A_2], 0),
    ("wlB-off", False, 240,  420, [WL_B_1, WL_B_2], 0),
    ("wlB-on",  True,  240,  420, [WL_B_1, WL_B_2], 0),
    ("ttl-long",False, 240, 4200, [LONG_1, LONG_2], 0),   # >65 min gap, OFF
]


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    os.makedirs(RAW, exist_ok=True)
    with open(LOG, "a") as fh:
        fh.write(line + "\n")


def done(label):
    return bool(glob.glob(os.path.join(RAW, label, "*.jsonl")))


def main():
    want = sys.argv[1:] or [a[0] for a in ARMS]
    for label, plugin, interval, gap, turns, post in ARMS:
        if label not in want:
            continue
        if done(label):
            log(f"SKIP {label} (already collected)")
            continue
        cwd = f"/tmp/ccka-{label}"
        log(f"=== ARM {label} (plugin={plugin}, gap={gap}s) ===")
        subprocess.run(["git", "worktree", "remove", "--force", cwd],
                       cwd=REPO, capture_output=True)
        os.system(f"rm -rf {cwd}")
        r = subprocess.run(["git", "worktree", "add", "--detach", cwd, "HEAD"],
                           cwd=REPO, capture_output=True, text=True)
        if r.returncode != 0:
            log(f"  worktree add FAILED: {r.stderr.strip()}"); continue
        cmd = [sys.executable, RUN_ARM, "--label", label, "--cwd", cwd,
               "--raw", RAW, "--gap", str(gap), "--turn-timeout", "600",
               "--post-wait", str(post)]
        if plugin:
            cmd += ["--plugin", "--interval", str(interval)]
        for t in turns:
            cmd += ["--turn", t]
        t0 = time.time()
        subprocess.run(cmd)
        log(f"  {label} run finished in {time.time()-t0:.0f}s")
        subprocess.run(["git", "worktree", "remove", "--force", cwd],
                       cwd=REPO, capture_output=True)
        os.system(f"rm -rf {cwd}")
        log(f"  {label} worktree removed")
    log("ALL DONE")


if __name__ == "__main__":
    main()
