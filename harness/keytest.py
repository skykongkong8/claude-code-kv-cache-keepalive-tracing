#!/usr/bin/env python3
"""Determine the Down-arrow encoding that moves the bypass-mode selector.
Spawns claude, waits for the 'Yes, I accept' menu, tries one encoding, and
reports whether the selector (❯) moved to option 2."""
import os, sys, time, threading, pexpect

ENC = {"app": "\x1bOB", "normal": "\x1b[B"}[sys.argv[1] if sys.argv[1:] else "app"]
cwd = "/tmp/ccka-keytest"; os.system(f"rm -rf {cwd}"); os.makedirs(cwd)
env = dict(os.environ); env["DISABLE_OMC"] = "1"
child = pexpect.spawn("claude", ["--model", "opus", "--dangerously-skip-permissions"],
                      cwd=cwd, env=env, encoding="utf-8", timeout=30, dimensions=(50, 200))
buf = []
stop = [False]
def drain():
    while not stop[0]:
        try:
            c = child.read_nonblocking(4096, timeout=1)
            if c: buf.append(c)
        except pexpect.TIMEOUT: continue
        except Exception: break
threading.Thread(target=drain, daemon=True).start()

def compact(): return "".join(buf).lower().replace(" ", "")
# wait for the menu
t0 = time.time()
while time.time() - t0 < 25:
    if "yes,iaccept" in compact(): break
    time.sleep(1)
time.sleep(1.5)
before = compact()
b_on2 = "❯2.yes" in before
print(f"before: selector_on_option2={b_on2}")
child.send(ENC); time.sleep(2)
after = compact()
a_on2 = "❯2.yes" in after
print(f"after sending {ENC!r} ({sys.argv[1] if sys.argv[1:] else 'app'}): selector_on_option2={a_on2}")
print("RESULT: MOVED" if (a_on2 and not b_on2) else "RESULT: no-change")
stop[0] = True
try:
    child.sendcontrol("c"); time.sleep(0.3); child.terminate(force=True)
except Exception: pass
