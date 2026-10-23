"""
Readers-Writers problem, solved with semaphores (first readers-writers solution,
i.e. readers get preference).

Shared resource : SharedData.value (a single integer)
Critical section: reading or writing that integer

Semaphores
  mutex    (init 1) - protects the read_count variable
  rw_mutex (init 1) - held by a writer, or by the group of readers as a whole

The first reader in locks out writers, the last reader out lets them back in.
Downside: if readers keep arriving, a writer can starve.

Run:  python rw_semaphore.py [--readers 4 --writers 2 --rounds 3 --delay 0.3]
"""
import random
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from sync_trace import RWTrace, parse_args


class SharedData:
    def __init__(self):
        self.value = 0


def reader(rid, data, trace, mutex, rw_mutex, state, rounds, delay):
    name = f"R{rid}"
    for _ in range(rounds):
        time.sleep(random.uniform(0, delay))                  # thinking
        trace.record(f"{name} wants to read", ("readers", name, "Waiting"))

        mutex.acquire()                                       # wait(mutex)
        state["read_count"] += 1
        if state["read_count"] == 1:
            rw_mutex.acquire()                                # first reader blocks writers
        mutex.release()                                       # signal(mutex)

        trace.enter_read(name, data.value)                    # ---- critical section ----
        time.sleep(random.uniform(0, delay))
        trace.exit_read(name)                                 # log BEFORE releasing

        mutex.acquire()
        state["read_count"] -= 1
        if state["read_count"] == 0:
            rw_mutex.release()                                # last reader lets writers in
        mutex.release()


def writer(wid, data, trace, rw_mutex, rounds, delay):
    name = f"W{wid}"
    for _ in range(rounds):
        time.sleep(random.uniform(0, delay))
        trace.record(f"{name} wants to write", ("writers", name, "Waiting"))

        rw_mutex.acquire()
        trace.enter_write(name)                               # ---- critical section ----
        tmp = data.value
        time.sleep(random.uniform(0, delay))                  # gap between read and write: a race
        data.value = tmp + 1                                  # would show up as a lost update
        trace.exit_write(name, data.value)
        rw_mutex.release()


def main():
    args = parse_args("Readers-Writers with semaphores", "readers_writers_semaphore.html", True)
    if args.seed is not None:
        random.seed(args.seed)

    params = {"solution": "semaphore", "readers": args.readers, "writers": args.writers,
              "rounds": args.rounds, "delay": args.delay}
    trace = RWTrace("Readers-Writers (Semaphores)", args.readers, args.writers, params)
    data = SharedData()
    mutex, rw_mutex = threading.Semaphore(1), threading.Semaphore(1)
    state = {"read_count": 0}

    threads = [threading.Thread(target=reader, args=(r, data, trace, mutex, rw_mutex, state, args.rounds, args.delay))
               for r in range(1, args.readers + 1)]
    threads += [threading.Thread(target=writer, args=(w, data, trace, rw_mutex, args.rounds, args.delay))
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
