"""
Dining Philosophers (4 philosophers) with semaphores.

Philosopher Pi sits between fork Fi (left) and F(i+1 mod 4) (right).
Shared resources: the 4 forks, one semaphore each (init 1).

Deadlock prevention: an extra counting semaphore 'seats' (init 3 = N-1) lets at
most 3 philosophers try to pick up forks at once. If all 4 each held one fork,
nobody could ever get a second one - with only 3 competing, at least one of
them can always get both. (The circular-wait condition can't complete.)

Starvation: deadlock is gone, but nothing guarantees fairness. A philosopher
could in theory be unlucky and keep losing the race for a fork. Python's
Semaphore wakes waiters roughly in FIFO order, which helps in practice.

Run:  python dp_semaphore.py [--rounds 3 --delay 0.3]
"""
import random
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from sync_trace import DPTrace, parse_args

N = 4


def philosopher(i, trace, forks, seats, meals, rounds, delay):
    name = f"P{i}"
    left, right = i, (i + 1) % N
    for _ in range(rounds):
        time.sleep(random.uniform(0, delay))                  # thinking
        trace.set_state(name, "Hungry", f"{name} is hungry")

        seats.acquire()                                       # at most N-1 at the table
        trace.set_state(name, "Acquiring Forks", f"{name} sits down and reaches for forks")

        forks[left].acquire()
        trace.take_fork(name, f"F{left}")
        time.sleep(random.uniform(0, delay / 3))              # small pause makes contention visible
        forks[right].acquire()
        trace.take_fork(name, f"F{right}")

        trace.set_state(name, "Eating", f"{name} is eating")  # ---- critical section ----
        time.sleep(random.uniform(0, delay))
        meals[i] += 1                                         # only this thread touches meals[i]

        trace.set_state(name, "Releasing Forks", f"{name} finished eating")
        trace.drop_fork(name, f"F{left}")                     # log first, then release
        forks[left].release()
        trace.drop_fork(name, f"F{right}")
        forks[right].release()
        seats.release()
        trace.set_state(name, "Thinking", f"{name} goes back to thinking")


def main():
    args = parse_args("Dining Philosophers (4) with semaphores", "dining_philosophers_semaphore.html", False)
    if args.seed is not None:
        random.seed(args.seed)

    params = {"solution": "semaphore", "philosophers": N, "rounds": args.rounds, "delay": args.delay}
    trace = DPTrace("Dining Philosophers - 4 philosophers (Semaphores)", N, params)
    forks = [threading.Semaphore(1) for _ in range(N)]
    seats = threading.Semaphore(N - 1)
    meals = [0] * N

    threads = [threading.Thread(target=philosopher, args=(i, trace, forks, seats, meals, args.rounds, args.delay))
               for i in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"meals eaten = {meals}, violations = {trace.violations}")
    print("HTML written to", trace.finish(args.out))


if __name__ == "__main__":
    main()
