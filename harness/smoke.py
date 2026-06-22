#!/usr/bin/env python3
"""
smoke.py — de-risk the pexpect interactive driver before spending real quota.

Key fix vs v1: a background thread continuously DRAINS the child's PTY output
(otherwise the buffer fills and claude blocks before processing input). Nested
sessions run with DISABLE_OMC=1 so the user's global OMC hooks/statusline don't
interfere with (or mask) the cache-keepalive Stop hook.

Probe 1 (no plugin): spawn, send a trivial prompt, detect completion via the
  transcript JSONL, print timing + usage.
Probe 2 (--plugin-dir, CCKA_INTERVAL=15): confirm the keepalive Stop hook fires.

Run: python3 smoke.py [1|2]
"""
import json, os, sys, time, glob, threading, pexpect

HOME = os.path.expanduser("~")
PLUGIN = "/tmp/cc-cache-keepalive/plugins/cache-keepalive"


def proj_dir(cwd):
    return os.path.join(HOME, ".claude", "projects", cwd.replace("/", "-"))


def newest_transcript(pdir, after_ts):
    js = [p for p in glob.glob(os.path.join(pdir, "*.jsonl"))
          if os.path.getmtime(p) >= after_ts - 2]
    return max(js, key=os.path.getmtime) if js else None


def last_assistant_done(path):
    last = None
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
            if isinstance(m, dict) and m.get("role") == "assistant":
                last = (m.get("stop_reason"), m.get("usage"))
    except FileNotFoundError:
        return None
    return last[1] if last and last[0] in ("end_turn", "stop_sequence") else None


class Session:
    def __init__(self, cwd, plugin=False, interval=None):
        os.makedirs(cwd, exist_ok=True)
        self.cwd = cwd
        # scrub inherited Claude Code env so the nested session is a fresh
        # TOP-LEVEL session (otherwise CLAUDECODE/CLAUDE_CODE_CHILD_SESSION make
        # it a child session that does NOT persist a transcript).
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("CLAUDE_CODE") and k not in
               ("CLAUDECODE", "CLAUDE_EFFORT", "AI_AGENT")}
        env["DISABLE_OMC"] = "1"                 # isolate from user's global OMC
        env["CCKA_STATE_DIR"] = os.path.join(cwd, ".ccka")
        env["CCKA_LOG"] = os.path.join(cwd, ".ccka", "keepalive.log")
        if interval:
            env["CCKA_INTERVAL"] = str(interval)
        args = ["--model", "opus", "--allowedTools",
                "Bash Edit MultiEdit Write Read Grep Glob LS WebFetch WebSearch "
                "TodoWrite NotebookEdit Task"]
        if plugin:
            args += ["--plugin-dir", PLUGIN]
        print(f"spawn: claude {' '.join(args)} (cwd={cwd}, plugin={plugin})", flush=True)
        self.child = pexpect.spawn("claude", args, cwd=cwd, env=env,
                                   encoding="utf-8", timeout=30, dimensions=(50, 200))
        self.logpath = os.path.join(cwd, "stdout.log")
        self.buf = []
        self._stop = False
        self._t = threading.Thread(target=self._drain, daemon=True)
        self._t.start()

    def _drain(self):
        with open(self.logpath, "w") as log:
            while not self._stop:
                try:
                    chunk = self.child.read_nonblocking(4096, timeout=1)
                    if chunk:
                        self.buf.append(chunk)
                        log.write(chunk); log.flush()
                except pexpect.TIMEOUT:
                    continue
                except (pexpect.EOF, OSError, ValueError):
                    break

    def tail(self, n=2000):
        return "".join(self.buf)[-n:]

    def wait_ready(self, timeout=70):
        """Wait until the REPL input box is ready to accept a prompt."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            low = self.tail(4000).lower().replace(" ", "")
            if "foragents" in low or 'try"' in low or "esctointerrupt" in low:
                return True
            time.sleep(1)
        return False

    def send_prompt(self, text, ready_timeout=70):
        self.wait_ready(ready_timeout)
        time.sleep(1.5)
        for _ in range(4):                      # type, verify placeholder gone, retry
            self.child.send(text)
            time.sleep(2.5)
            recent = self.tail(1500).lower().replace(" ", "")
            if 'try"create' not in recent:      # grey placeholder replaced by our text
                break
        self.child.send("\r")

    def close(self):
        self._stop = True
        try:
            self.child.send("\x1b"); time.sleep(0.3)
            self.child.sendcontrol("c"); time.sleep(0.3)
            self.child.sendcontrol("c"); time.sleep(0.3)
            self.child.terminate(force=True)
        except Exception:
            pass


def wait_turn(pdir, t0, timeout=200):
    deadline = time.time() + timeout
    path = None
    while time.time() < deadline:
        if path is None:
            path = newest_transcript(pdir, t0)
        if path:
            u = last_assistant_done(path)
            if u:
                return path, u
        time.sleep(2)
    return path, None


def probe1():
    cwd = "/tmp/ccka-smoke1"; os.system(f"rm -rf {cwd}")
    pdir = proj_dir(cwd); t0 = time.time()
    s = Session(cwd, plugin=False)
    s.send_prompt("Reply with exactly the single word READY and nothing else.")
    path, u = wait_turn(pdir, t0)
    print(f"probe1: transcript={path}", flush=True)
    print(f"probe1: completed in {time.time()-t0:.0f}s; usage={json.dumps(u) if u else 'NONE'}", flush=True)
    if not u:
        print("---- TUI tail ----\n" + s.tail(1500), flush=True)
    s.close()
    print("probe1: OK" if u else "probe1: FAILED", flush=True)


def probe2():
    cwd = "/tmp/ccka-smoke2"; os.system(f"rm -rf {cwd}")
    pdir = proj_dir(cwd); t0 = time.time()
    s = Session(cwd, plugin=True, interval=15)
    s.send_prompt("Reply with exactly the single word OK and nothing else.")
    path, u = wait_turn(pdir, t0)
    print(f"probe2: real turn done; usage={'yes' if u else 'NO'}", flush=True)
    log = os.path.join(cwd, ".ccka", "keepalive.log")
    fired = False; deadline = time.time() + 90
    while time.time() < deadline:
        if os.path.exists(log) and "sleeping" in open(log).read():
            fired = True
            if "blocking Stop" in open(log).read():
                break
        time.sleep(3)
    print(f"probe2: keepalive log exists={os.path.exists(log)}, fired={fired}", flush=True)
    if os.path.exists(log):
        print("---- keepalive.log ----\n" + open(log).read().strip()[-800:], flush=True)
    s.close()
    print("probe2: OK" if fired else "probe2: FAILED", flush=True)


if __name__ == "__main__":
    (probe1 if (sys.argv[1:] or ["1"])[0] == "1" else probe2)()
