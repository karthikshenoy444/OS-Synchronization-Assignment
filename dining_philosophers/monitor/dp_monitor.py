"""
Dining Philosophers (4 philosophers) with a monitor.

The monitor is a class with one lock and one condition variable per philosopher.
A philosopher only gets forks if BOTH neighbours are not eating, and the check
plus picking up the forks happen atomically inside the monitor, so a philosopher
never holds just one fork -> no hold-and-wait -> no deadlock.

Starvation: this classic version can starve a philosopher. If P0's two
neighbours keep taking turns eating, P0 may never see both of them idle at
once. A fix would be an age/ticket counter; not added here to keep it readable.

Run:  python dp_monitor.py [--rounds 3 --delay 0.3]
"""
import random
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from sync_trace import DPTrace, parse_args

N = 4
THINKING, HUNGRY, EATING = "thinking", "hungry", "eating"


class DiningMonitor:
    def __init__(self, trace):
        self._lock = threading.Lock()
        self._can_eat = [threading.Condition(self._lock) for _ in range(N)]
        self._state = [THINKING] * N
        self._trace = trace

    def _try_to_eat(self, i):
        """Must be called with the monitor lock held."""
        left_neighbour, right_neighbour = (i - 1) % N, (i + 1) % N
        if (self._state[i] == HUNGRY and self._state[left_neighbour] != EATING
                and self._state[right_neighbour] != EATING):
            name = f"P{i}"
            self._state[i] = EATING
            self._trace.take_fork(name, f"F{i}")
            self._trace.take_fork(name, f"F{(i + 1) % N}")
            self._trace.set_state(name, "Eating", f"{name} is eating")
            self._can_eat[i].notify()

    def pick_up_forks(self, i):
        with self._lock:
            self._state[i] = HUNGRY
            self._trace.set_state(f"P{i}", "Acquiring Forks", f"P{i} asks the monitor for forks")
            self._try_to_eat(i)
            while self._state[i] != EATING:
                self._can_eat[i].wait()

    def put_down_forks(self, i):
        with self._lock:
            name = f"P{i}"
            self._trace.set_state(name, "Releasing Forks", f"{name} finished eating")
            self._trace.drop_fork(name, f"F{i}")
            self._trace.drop_fork(name, f"F{(i + 1) % N}")
            self._state[i] = THINKING
            self._trace.set_state(name, "Thinking", f"{name} goes back to thinking")
            # a neighbour may have been waiting for exactly these forks
            self._try_to_eat((i - 1) % N)
            self._try_to_eat((i + 1) % N)


def philosopher(i, trace, monitor, meals, rounds, delay):
    for _ in range(rounds):
        time.sleep(random.uniform(0, delay))
        trace.set_state(f"P{i}", "Hungry", f"P{i} is hungry")
        monitor.pick_up_forks(i)
        time.sleep(random.uniform(0, delay))                  # eating (outside the monitor lock)
        meals[i] += 1
        monitor.put_down_forks(i)


def main():
    args = parse_args("Dining Philosophers (4) with a monitor", "dining_philosophers_monitor.html", False)
    if args.seed is not None:
        random.seed(args.seed)

    params = {"solution": "monitor", "philosophers": N, "rounds": args.rounds, "delay": args.delay}
    trace = DPTrace("Dining Philosophers - 4 philosophers (Monitor)", N, params)
    monitor = DiningMonitor(trace)
    meals = [0] * N

    threads = [threading.Thread(target=philosopher, args=(i, trace, monitor, meals, args.rounds, args.delay))
               for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"meals eaten = {meals}, violations = {trace.violations}")
    print("HTML written to", trace.finish(args.out))


if __name__ == "__main__":
    main()
