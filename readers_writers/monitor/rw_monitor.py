"""
Readers-Writers problem, solved with a monitor.

Python has no 'monitor' keyword, so the monitor is a class: one lock, and every
public method takes that lock (the 'with self._lock' blocks). Two condition
variables sit on that same lock.

Shared resource : SharedData.value
Critical section: reading/writing it, which happens after start_* returns

Unlike the semaphore version this one gives WRITERS preference: a new reader
waits if any writer is waiting. That stops writer starvation, but a stream of
writers can now starve readers.

Run:  python rw_monitor.py [--readers 4 --writers 2 --rounds 3 --delay 0.3]
"""
import random
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from sync_trace import RWTrace, parse_args


class ReadersWritersMonitor:
    def __init__(self):
        self._lock = threading.Lock()
        self._ok_to_read = threading.Condition(self._lock)
        self._ok_to_write = threading.Condition(self._lock)
        self._active_readers = 0
        self._writing = False
        self._waiting_writers = 0

    def start_read(self):
        with self._lock:
            # 'while', not 'if': after waking up we must re-check the condition
            while self._writing or self._waiting_writers > 0:
                self._ok_to_read.wait()
            self._active_readers += 1

    def end_read(self):
        with self._lock:
            self._active_readers -= 1
            if self._active_readers == 0:
                self._ok_to_write.notify()

    def start_write(self):
        with self._lock:
            self._waiting_writers += 1
            while self._writing or self._active_readers > 0:
                self._ok_to_write.wait()
            self._waiting_writers -= 1
            self._writing = True

    def end_write(self):
        with self._lock:
            self._writing = False
            if self._waiting_writers > 0:
                self._ok_to_write.notify()
            else:
                self._ok_to_read.notify_all()


class SharedData:
    def __init__(self):
        self.value = 0


def reader(rid, data, trace, monitor, rounds, delay):
    name = f"R{rid}"
    for _ in range(rounds):
        time.sleep(random.uniform(0, delay))
        trace.record(f"{name} wants to read", ("readers", name, "Waiting"))
        monitor.start_read()
        trace.enter_read(name, data.value)                    # ---- critical section ----
        time.sleep(random.uniform(0, delay))
        trace.exit_read(name)
        monitor.end_read()


def writer(wid, data, trace, monitor, rounds, delay):
    name = f"W{wid}"
    for _ in range(rounds):
        time.sleep(random.uniform(0, delay))
        trace.record(f"{name} wants to write", ("writers", name, "Waiting"))
        monitor.start_write()
        trace.enter_write(name)                               # ---- critical section ----
        tmp = data.value
        time.sleep(random.uniform(0, delay))
        data.value = tmp + 1
        trace.exit_write(name, data.value)
        monitor.end_write()


def main():
    args = parse_args("Readers-Writers with a monitor", "readers_writers_monitor.html", True)
    if args.seed is not None:
        random.seed(args.seed)

    params = {"solution": "monitor", "readers": args.readers, "writers": args.writers,
              "rounds": args.rounds, "delay": args.delay}
    trace = RWTrace("Readers-Writers (Monitor)", args.readers, args.writers, params)
    data = SharedData()
    monitor = ReadersWritersMonitor()

    threads = [threading.Thread(target=reader, args=(r, data, trace, monitor, args.rounds, args.delay))
               for r in range(1, args.readers + 1)]
    threads += [threading.Thread(target=writer, args=(w, data, trace, monitor, args.rounds, args.delay))
                for w in range(1, args.writers + 1)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    expected = args.writers * args.rounds
    print(f"final value = {data.value} (expected {expected}), violations = {trace.violations}")
    print("HTML written to", trace.finish(args.out))


if __name__ == "__main__":
    main()
