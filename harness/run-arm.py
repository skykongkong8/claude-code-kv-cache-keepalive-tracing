#!/usr/bin/env python3
"""
run-arm.py — run one experiment arm: a real interactive `claude` session driven
via pexpect, with deliberate idle gaps between turns, then collect the transcript
and keep-alive log into the raw output dir.

Example:
  run-arm.py --label wlA-off --cwd /tmp/ccka-wlA-off --gap 420 \
      --raw .../raw --turn "PROMPT 1" --turn "PROMPT 2"
  run-arm.py --label wlA-on  --cwd /tmp/ccka-wlA-on  --plugin --interval 240 --gap 420 \
      --raw .../raw --turn "PROMPT 1" --turn "PROMPT 2"

Notes:
- Nested sessions run with DISABLE_OMC=1 to isolate the user's global OMC hooks
  from the cache-keepalive Stop hook under test.
- Turn completion is detected from the transcript JSONL (a NEW assistant message
  with stop_reason in {end_turn, stop_sequence} beyond the pre-send baseline).
- ON-arm gaps let the keepalive Stop hook fire; we send Esc before the next real
  turn to break any in-progress sleep.
"""
import argparse, json, os, shutil, sys, time, glob, threading, pexpect

HOME = os.path.expanduser("~")
PLUGIN = "/tmp/cc-cache-keepalive/plugins/cache-keepalive"
DONE = ("end_turn", "stop_sequence")


def proj_dir(cwd):
    return os.path.join(HOME, ".claude", "projects", cwd.replace("/", "-"))


def transcript_for(cwd, t0):
    pdir = proj_dir(cwd)
    js = [p for p in glob.glob(os.path.join(pdir, "*.jsonl"))
          if os.path.getmtime(p) >= t0 - 2]
    return max(js, key=os.path.getmtime) if js else None


def count_done(path):
    """Number of assistant messages that ended a turn, in file order."""
    n = 0
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            m = o.get("message")
            if isinstance(m, dict) and m.get("role") == "assistant" \
                    and m.get("stop_reason") in DONE:
                n += 1
    except FileNotFoundError:
        return 0
    return n


class Session:
    def __init__(self, cwd, plugin, interval):
        os.makedirs(cwd, exist_ok=True)
        self.cwd = cwd
        # scrub inherited Claude Code env so the nested session is a fresh
        # TOP-LEVEL session that persists a transcript (CLAUDECODE/
        # CLAUDE_CODE_CHILD_SESSION would otherwise put it in child mode).
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("CLAUDE_CODE") and k not in
               ("CLAUDECODE", "CLAUDE_EFFORT", "AI_AGENT")}
        env["DISABLE_OMC"] = "1"
        env["CCKA_STATE_DIR"] = os.path.join(cwd, ".ccka")
        env["CCKA_LOG"] = os.path.join(cwd, ".ccka", "keepalive.log")
        if interval:
            env["CCKA_INTERVAL"] = str(interval)
        args = ["--model", "opus", "--allowedTools",
                "Bash Edit MultiEdit Write Read Grep Glob LS WebFetch WebSearch "
                "TodoWrite NotebookEdit Task"]
        if plugin:
            args += ["--plugin-dir", PLUGIN]
        print(f"[{cwd}] spawn: claude {' '.join(args)}", flush=True)
        self.child = pexpect.spawn("claude", args, cwd=cwd, env=env,
                                   encoding="utf-8", timeout=30, dimensions=(50, 200))
        self.buf = []
        self._stop = False
        self._log = open(os.path.join(cwd, "stdout.log"), "w")
        threading.Thread(target=self._drain, daemon=True).start()

    def _drain(self):
        while not self._stop:
            try:
                chunk = self.child.read_nonblocking(4096, timeout=1)
                if chunk:
                    self.buf.append(chunk)
                    self._log.write(chunk); self._log.flush()
            except pexpect.TIMEOUT:
                continue
            except (pexpect.EOF, OSError, ValueError):
                break

    def tail(self, n=2000):
        return "".join(self.buf)[-n:]

    def wait_ready(self, timeout=80):
        """Wait until the REPL input box is ready to accept a prompt."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            low = self.tail(4000).lower().replace(" ", "")
            if "foragents" in low or 'try"' in low or "esctointerrupt" in low:
                return True
            time.sleep(1)
        return False

    def send_prompt(self, text, ready_timeout=80):
        self.wait_ready(ready_timeout)
        time.sleep(1.5)
        for _ in range(4):                      # type, verify placeholder gone, retry
            self.child.send(text)
            time.sleep(2.5)
            recent = self.tail(1500).lower().replace(" ", "")
            if 'try"create' not in recent:
                break
        self.child.send("\r")

    def esc(self):
        self.child.send("\x1b"); time.sleep(1)

    def close(self):
        self._stop = True
        try:
            self.child.send("\x1b"); time.sleep(0.3)
            self.child.sendcontrol("c"); time.sleep(0.3)
            self.child.sendcontrol("c"); time.sleep(0.3)
            self.child.terminate(force=True)
        except Exception:
            pass
        try:
            self._log.close()
        except Exception:
            pass


def wait_new_done(cwd, t0, baseline, timeout):
    """Wait until a NEW completed assistant turn appears beyond baseline."""
    deadline = time.time() + timeout
    path = None
    while time.time() < deadline:
        path = path or transcript_for(cwd, t0)
        if path and count_done(path) > baseline:
            return path
        time.sleep(3)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--turn", action="append", required=True)
    ap.add_argument("--plugin", action="store_true")
    ap.add_argument("--interval", type=int, default=240)
    ap.add_argument("--gap", type=int, default=420)
    ap.add_argument("--settle", type=int, default=15)
    ap.add_argument("--turn-timeout", type=int, default=600)
    ap.add_argument("--post-wait", type=int, default=0,
                    help="extra wait after last turn (ON arms: capture keepalive pings)")
    a = ap.parse_args()

    os.makedirs(a.cwd, exist_ok=True)   # cwd is a pre-created git worktree
    t0 = time.time()
    s = Session(a.cwd, a.plugin, a.interval if a.plugin else None)
    s.wait_ready(80)

    path = None
    for i, turn in enumerate(a.turn):
        path = transcript_for(a.cwd, t0)
        baseline = count_done(path) if path else 0
        print(f"[{a.label}] turn {i+1}/{len(a.turn)} (baseline_done={baseline}) "
              f"@ +{time.time()-t0:.0f}s: {turn[:70]!r}", flush=True)
        if a.plugin and i > 0:
            s.esc()             # break any sleeping keepalive before a real turn
        s.send_prompt(turn)
        path = wait_new_done(a.cwd, t0, baseline, a.turn_timeout)
        done_now = count_done(path) if path else 0
        print(f"[{a.label}] turn {i+1} done @ +{time.time()-t0:.0f}s "
              f"(done_count={done_now}, transcript={path})", flush=True)
        if i < len(a.turn) - 1:
            print(f"[{a.label}] idle gap {a.gap}s "
                  f"({'keepalive may fire' if a.plugin else 'plain wait'}) ...", flush=True)
            time.sleep(a.gap)
    if a.post_wait:
        print(f"[{a.label}] post-wait {a.post_wait}s ...", flush=True)
        time.sleep(a.post_wait)

    s.close()

    # collect artifacts
    outdir = os.path.join(a.raw, a.label)
    os.makedirs(outdir, exist_ok=True)
    if path and os.path.exists(path):
        shutil.copy(path, os.path.join(outdir, os.path.basename(path)))
    klog = os.path.join(a.cwd, ".ccka", "keepalive.log")
    if os.path.exists(klog):
        shutil.copy(klog, os.path.join(outdir, "keepalive.log"))
    shutil.copy(os.path.join(a.cwd, "stdout.log"),
                os.path.join(outdir, "stdout.log"))
    print(f"[{a.label}] collected -> {outdir} "
          f"(elapsed {time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
