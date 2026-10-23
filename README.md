# OS Synchronization Assignment

**Name:** <your name>  **USN:** <your registration number>

Readers-Writers and Dining Philosophers (4 philosophers), each solved twice:
once with semaphores and once with a monitor. Every program records what its
threads really did and writes an HTML replay of that run.

## What's in here

| Folder | Program | Idea |
|---|---|---|
| `readers_writers/semaphore` | `rw_semaphore.py` | `mutex` + `rw_mutex` + `read_count`; readers have priority (writers can starve) |
| `readers_writers/monitor` | `rw_monitor.py` | class with one lock and two condition variables; writers have priority (readers can starve) |
| `dining_philosophers/semaphore` | `dp_semaphore.py` | one semaphore per fork + a `seats` semaphore of 3 so a circular wait can't form |
| `dining_philosophers/monitor` | `dp_monitor.py` | per-philosopher condition variable; forks are taken only if both neighbours aren't eating |
| `common/` | `sync_trace.py`, `html_report.py` | event recorder and HTML generator shared by all four |

## Requirements

Python 3.8+ (tested on 3.12). Standard library only, nothing to install or compile.

## Run

```bash
python readers_writers/semaphore/rw_semaphore.py
python readers_writers/monitor/rw_monitor.py
python dining_philosophers/semaphore/dp_semaphore.py
python dining_philosophers/monitor/dp_monitor.py
```

Options (all optional): `--readers 4 --writers 2` (RW only), `--rounds 3`,
`--delay 0.3` (max random delay in seconds), `--seed N`, `--out path.html`.
The end of each run prints a self-check (final value vs expected, or meals eaten)
and the number of mutual-exclusion violations, which should be 0.

## How the HTML is generated

1. Threads run the real algorithm.
2. At each state change (wait, enter/leave critical section, pick up/put down a fork)
   the thread calls `RWTrace` / `DPTrace`, which stores a snapshot of the full state.
3. After `join()`, `finish()` writes `generated_html/<name>.json` and `<name>.html`
   (the trace is embedded in the page).
4. Open the `.html` file in any browser. Use Play/Pause/Step/Reset, the speed box,
   the slider, or click a line in the event log.

Running a program again gives a different trace; the OS scheduler and random delays change it.

## Expected output

```
final value = 8 (expected 8), violations = 0
HTML written to .../generated_html/readers_writers_semaphore.html
```

Screenshots go in `screenshots/`.

## Known limitations

- Python's GIL means threads aren't truly parallel, but blocking and interleaving
  (and so the synchronization behaviour) is still real.
- Neither dining-philosophers version has a formal starvation guarantee (see the comments in the code).
- Seeding only fixes the random delays, not the thread scheduling.

## AI tools used

See [ai_prompts/prompts.md](ai_prompts/prompts.md). References: [references/references.md](references/references.md).
