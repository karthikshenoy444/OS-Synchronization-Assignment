"""
sync_trace.py - records what the threads actually do.

Every time a thread changes state (waits, enters the critical section, picks up
a fork, ...) it calls into one of the classes here. We copy the whole system
state at that moment and store it as an "event". After the run, the events are
written to a JSON file and turned into an HTML page by html_report.py.

Nothing in here is scripted: the order of events is whatever the OS scheduler
and the synchronization primitives in the real program produced.
"""
import argparse
import copy
import json
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Trace:
    def __init__(self, title, kind, params):
        self.title = title
        self.kind = kind            # "rw" or "dp" - tells the HTML which view to draw
        self.params = params
        self.state = {}             # {group: {name: value}}
        self.events = []
        self.violations = 0         # times mutual exclusion was broken (should stay 0)
        self._lock = threading.Lock()
        self._t0 = time.perf_counter()

    def init(self, group, name, value):
        self.state.setdefault(group, {})[name] = value

    def record(self, message, *changes):
        """changes are (group, name, new_value) tuples."""
        with self._lock:
            self._record_locked(message, *changes)

    def _record_locked(self, message, *changes):
        for group, name, value in changes:
            self.state[group][name] = value
        self.events.append({
            "seq": len(self.events),
            "t_ms": round((time.perf_counter() - self._t0) * 1000),
            "msg": message,
            "state": copy.deepcopy(self.state),
        })

    def _violation(self, message):
        # called with self._lock held
        self.violations += 1
        self._record_locked("!! VIOLATION: " + message)

    def finish(self, html_path):
        from html_report import write_html
        html_path = Path(html_path)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"title": self.title, "kind": self.kind, "params": self.params,
                "violations": self.violations, "events": self.events}
        html_path.with_suffix(".json").write_text(json.dumps(data, indent=1))
        write_html(html_path, data)
        return html_path


class RWTrace(Trace):
    """Trace for Readers-Writers. Also double-checks the critical section."""

    def __init__(self, title, readers, writers, params):
        super().__init__(title, "rw", params)
        for r in range(1, readers + 1):
            self.init("readers", f"R{r}", "Thinking")
        for w in range(1, writers + 1):
            self.init("writers", f"W{w}", "Thinking")
        self.init("resource", "status", "Idle")
        self.init("resource", "readers", 0)
        self.init("resource", "writer", "-")
        self.init("resource", "value", 0)

    def enter_read(self, name, value):
        with self._lock:
            res = self.state["resource"]
            if res["writer"] != "-":
                self._violation(f"{name} reading while {res['writer']} is writing")
            n = res["readers"] + 1
            self._record_locked(f"{name} enters critical section (reads value = {value})",
                                ("readers", name, "Reading"),
                                ("resource", "readers", n),
                                ("resource", "status", "Being read"))

    def exit_read(self, name):
        with self._lock:
            n = self.state["resource"]["readers"] - 1
            self._record_locked(f"{name} leaves critical section",
                                ("readers", name, "Thinking"),
                                ("resource", "readers", n),
                                ("resource", "status", "Being read" if n else "Idle"))

    def enter_write(self, name):
        with self._lock:
            res = self.state["resource"]
            if res["writer"] != "-" or res["readers"] > 0:
                self._violation(f"{name} writing while resource is in use")
            self._record_locked(f"{name} enters critical section (writing)",
                                ("writers", name, "Writing"),
                                ("resource", "writer", name),
                                ("resource", "status", "Being written"))

    def exit_write(self, name, new_value):
        with self._lock:
            self._record_locked(f"{name} leaves critical section (value is now {new_value})",
                                ("writers", name, "Thinking"),
                                ("resource", "writer", "-"),
                                ("resource", "value", new_value),
                                ("resource", "status", "Idle"))


class DPTrace(Trace):
    """Trace for Dining Philosophers. Forks F0..F3, philosopher Pi uses Fi and F(i+1)."""

    def __init__(self, title, n, params):
        super().__init__(title, "dp", params)
        for i in range(n):
            self.init("philosophers", f"P{i}", "Thinking")
        for i in range(n):
            self.init("forks", f"F{i}", "free")

    def set_state(self, name, new_state, message=None):
        with self._lock:
            if new_state == "Eating":
                i = int(name[1:])
                n = len(self.state["forks"])
                for f in (f"F{i}", f"F{(i + 1) % n}"):
                    if self.state["forks"][f] != name:
                        self._violation(f"{name} eating without holding {f}")
            self._record_locked(message or f"{name} -> {new_state}",
                                ("philosophers", name, new_state))

    def take_fork(self, name, fork):
        with self._lock:
            if self.state["forks"][fork] != "free":
                self._violation(f"{name} took {fork} owned by {self.state['forks'][fork]}")
            self._record_locked(f"{name} picks up {fork}", ("forks", fork, name))

    def drop_fork(self, name, fork):
        with self._lock:
            self._record_locked(f"{name} puts down {fork}", ("forks", fork, "free"))


def parse_args(description, default_html, readers_writers):
    p = argparse.ArgumentParser(description=description)
    if readers_writers:
        p.add_argument("--readers", type=int, default=4, help="number of reader threads")
        p.add_argument("--writers", type=int, default=2, help="number of writer threads")
    p.add_argument("--rounds", type=int, default=3, help="how many times each thread repeats")
    p.add_argument("--delay", type=float, default=0.3, help="max random think/work time (seconds)")
    p.add_argument("--seed", type=int, default=None, help="seed for the random delays")
    p.add_argument("--out", default=str(ROOT / "generated_html" / default_html),
                   help="where to write the HTML file")
    return p.parse_args()
