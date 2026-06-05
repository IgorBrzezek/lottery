# Lottery — Multi-Round Number Drawing Without Replacement

**lottery.py** draws numbers from a range `[FROM, TO]` in rounds, without
replacing them until the pool runs out.  It is designed for lottery-style
scenarios where each drawn number is removed from the pool, and when the
pool no longer has enough unique numbers to fill a full round, it takes
whatever is left and then refills from the full set.

The script supports two random number backends:

1. **Python `random` module** (default) — uses `random.sample` and
   `random.randint`.
2. **trandom.py** (with `--rndauto`) — a true multi-source entropy
   generator that harvests randomness from CPU jitter, disk timing,
   memory addresses, thread scheduling, network timing, performance
   counters, and the system CSPRNG.  Optionally augmented with mouse
   movements, keyboard presses, or hardware sensors.
   
   **Importatn notice:**
   You need to download this file separately from the repo:
   https://github.com/IgorBrzezek/trandom

**Version:** 0.5
**Author:** igor.brzezek@gmail.com
**Repository:** https://github.com/IgorBrzezek/lottery

---

## How the Drawing Algorithm Works

1. A full pool of integers `[FROM, TO]` is created (inclusive of both
   endpoints).

2. Each round begins with the current `remaining` set.  Initially this
   is the full pool.

3. If `remaining` contains at least `n` numbers, the script draws `n`
   numbers **without replacement** using the selected RNG backend.

   - If `--minlen` (or `--noneighbor`) constraints are active, the draw
     is repeated until a valid set is found (or until `can_pick()`
     determines that no valid subset exists, in which case the
     constraint is bypassed and a plain draw is made).

4. The drawn numbers are removed from `remaining`.

5. When `remaining` has fewer than `n` numbers left, the script takes
   all of them, clears the pool, and then tries to refill the round by
   drawing the remaining needed numbers from the **full set**, excluding
   numbers already drawn in the current partial round.  The script then
   stops — one final round with leftovers plus refill.

6. Rounds continue until the `remaining` set is empty (one full pool cycle). With `--series N`, this full pool cycle is repeated N times, each starting from a fresh pool `[FROM, TO]`.  Between series a separator line is printed (yellow with `--color`).

7. With `--fullpool`, the pool is never depleted. Each draw picks `n` numbers from the full range `[FROM, TO]` without removing them.  `--series N` determines the number of draws (default: 1).  This is useful for independent lottery simulations where all numbers are equally likely in every draw.

8. With `--threads N`, the workload is split across N parallel threads, each with its own RNG.  Requires `--series`.  Repeat tracking is thread-local.  trandom is not supported in parallel mode (falls back to Python random).

9. Numbers that have appeared in any previous round are marked as
   repeats.  With `--color` they appear in red; without `--color` they
   are prefixed with `*`.

### Constraint Logic

- `has_adjacent(nums)` — Returns `True` if any two sorted numbers differ
  by exactly 1.
- `has_close(nums, minlen)` — Returns `True` if any two sorted numbers
  differ by less than `minlen`.
- `can_pick(nums, n, min_gap)` — Checks whether at least `n` numbers can
  be selected from `nums` such that every pair is at least `min_gap`
  apart.  If `min_gap <= 1`, every subset is valid.

- `count_neighbor_runs(nums, m)` — Counts how many non-overlapping runs
  of exactly `m` consecutive numbers appear in `nums`.  A run of length
  `L` contributes `L // m` occurrences (e.g., `[1,2,3,4]` with `m=2`
  counts as 2 pairs: `(1,2)` and `(3,4)`).

When `--minlen` is set and `can_pick()` returns `False`, the constraint
is relaxed and the script draws without checking `minlen`/`noneighbor` —
otherwise it might loop forever searching for a valid set that does not
exist.  The `--nei` constraint is still enforced in that case.

---

## Requirements

### Windows (no external dependencies)
All features work out of the box. Mouse tracking uses the Win32 API via
`ctypes` (built-in). Keyboard tracking uses `msvcrt` (built-in).

### Linux / macOS
- Mouse entropy (`--mouse`) requires: `pip install pynput`
- Keyboard entropy (`--keyboard`) uses `select` on stdin (built-in).
- Sensor entropy (`--sensors`) requires `psutil` for live readings, or
  falls back to timing jitter.

### trandom.py
`--rndauto` requires `trandom.py` to be present in the same directory.
No pip install is needed for the standard 7 entropy sources.

---

## Command-Line Options

### Required Arguments

| Option | Description |
|---|---|
| `-a FROM`, `--from FROM` | Start of the range (inclusive) |
| `-b TO`, `--to TO` | End of the range (inclusive) |
| `-n COUNT`, `--count COUNT` | Numbers to draw per round |

### Number Constraints

| Option | Description |
|---|---|---|
| `-nn`, `--noneighbor` | Prevent adjacent numbers (differing by 1) in any single draw |
| `--minlen INT` | Minimum distance between any two drawn numbers in a single draw |
| `--nei N,M` | Require exactly N runs of M consecutive numbers in each draw (e.g., `--nei 1,2` = one adjacent pair, `--nei 2,2` = two pairs, `--nei 1,3` = one triple) |
| `--series N` | Repeat the entire drawing process N times. Each series starts with a fresh pool `[FROM, TO]` and runs until the pool is exhausted (with one refill round). A separator line with the series number is printed between series (yellow with `--color`). Without this flag, a single pool cycle is performed. |
| `--fullpool` | Each draw uses the full range `[FROM, TO]` without removing numbers. `--series N` sets the number of draws (default: 1). Useful for independent lottery simulations. |
| `-t N`, `--threads N` | Split work across N parallel threads (each with its own RNG). Requires `--series`. Repeat tracking is thread-local. Not compatible with `--rndauto`. |
| `--seriesentropy` | Re-collect sensor entropy at each new series when using `--series`. Requires `--rndauto`. |
| `--debug` | Show the remaining-number pool in brackets after each round |

`--minlen` and `--noneighbor` can be used together.  If both are given,
`--minlen` takes precedence over `--noneighbor` for setting the minimum
gap, but both checks are applied.

`--nei` is **mutually exclusive** with `--minlen`.  Using both will
cause the script to exit with an error.

### Random Generator Selection

| Option | Description |
|---|---|
| (default) | Python built-in `random.sample` / `random.randint` |
| `--rndauto` | Use **trandom.py** with 7 always-active entropy sources |
| `--rnd auto` | Same as `--rndauto` |
| `--rnd python` | Explicitly use Python's random module |

### Additional Entropy (only with `--rndauto` / `--rnd auto`)

These flags augment trandom.py's 7 standard entropy sources with
additional physical entropy.

| Option | Description |
|---|---|
| `--mouse` | Collect mouse-movement entropy (interactive — move the mouse). On Windows uses Win32 API; on Linux/macOS requires `pynput`. |
| `--keyboard` | Collect keyboard-press entropy (interactive — press keys). On Windows uses `msvcrt`; on Unix uses `select` on stdin. |
| `--sensors` | Collect hardware sensor entropy (CPU temperature, fan speeds, voltages, battery). Uses `psutil` or `wmic` fallback. |
| `--samples N` | Number of mouse/keyboard samples to collect (default 250). More samples mean more entropy data mixed into the initial draws. |

`--mouse` and `--keyboard` are **mutually exclusive**.

### Output

| Option | Description |
|---|---|
| `--color` | Enable ANSI colored output: new numbers in white, repeats in red. Without this flag, output is plain ASCII — repeats are marked with `*`. |
| `--colorneighbor` | Highlight adjacent numbers in green (can be combined with `--color`; green takes priority over white/red) |
| `--numbering cont|ext` | Round numbering: `cont` (continuous, default) or `ext` (continuous/series-round, e.g. `5/  1`) |
| `--seriesentropy` | Re-collect sensor entropy at each new series when using `--series`. Requires `--rndauto`. |
| `--debug` | Append the remaining-number pool in square brackets after each round. |
| `-w FILENAME`, `--write FILENAME` | Write drawn numbers to CSV file (one round per line, comma-separated; blank line between series). Terminal output remains unchanged. |
| `--wcont` | With `-w`, write CSV continuously without blank line separators between series. |
| `--nodisplay` | Suppress all terminal output (only valid with `-w`). Useful for batch/scripted runs. |
| `--pb`, `--progressbar` | Show progress bar on stderr (requires `--nodisplay`). |
| `-in FILE`, `--infile FILE` | Read and display a CSV file previously written with `-w`. With `--color`, numbers are colored as on screen. With `--colorneighbor`, adjacent numbers are highlighted. |

### Help

| Option | Description |
|---|---|
| `-h` | Short usage line |
| `--help` | Detailed help with option descriptions |

---

## Output Format

Each round is printed on one line:

```
  N:  num1 num2 ... numN  [remaining,pool]
```

- `N` is the round number (right-aligned, 3 characters).
- Each number is right-aligned to the width of the largest number in the
  range.
- With `--color`: new numbers appear in white, numbers seen in any
  previous round appear in red.
- Without `--color`: new numbers appear as plain digits, repeats are
  prefixed with `*`.
- With `--debug`: the pool of numbers still available for future rounds
  is shown in square brackets at the end of the line.

### Example output (default, no color):

```
  1:  6  42  11  19  20  16
  2:  46  21   5  22  49  36
  ...
  9:  27 *23 *18 * 6 *48 *21
```

The `*` markers on round 9 indicate those numbers were drawn in at least
one earlier round.

### Example output (with `--color`):

In a terminal that supports ANSI escape codes, new numbers are bright
white and repeats are red.  No `*` markers are shown.

---

## Examples

```bash
# Basic lottery draw: 6 numbers from 1 to 49
python lottery.py -a 1 -b 49 -n 6

# Prevent adjacent numbers (differing by 1)
python lottery.py -a 1 -b 49 -n 6 -nn

# Require exactly one pair of adjacent numbers (e.g., 1,2 or 30,31)
python lottery.py -a 1 -b 49 -n 6 --nei 1,2

# Require exactly two pairs of adjacent numbers
python lottery.py -a 1 -b 49 -n 6 --nei 2,2

# Require exactly one triple of consecutive numbers (e.g., 5,6,7)
python lottery.py -a 1 -b 49 -n 6 --nei 1,3

# Minimum distance of 3 between any two drawn numbers
python lottery.py -a 1 -b 49 -n 6 --minlen 3

# Use trandom.py (7 always-active entropy sources)
python lottery.py -a 1 -b 49 -n 6 --rndauto

# Same, with mouse-movement entropy (interactive — move the mouse)
python lottery.py -a 1 -b 49 -n 6 --rndauto --mouse

# With keyboard-press entropy (interactive — press keys)
python lottery.py -a 1 -b 49 -n 6 --rndauto --keyboard

# Collect 500 mouse samples instead of the default 250
python lottery.py -a 1 -b 49 -n 6 --rndauto --mouse --samples 500

# Combine trandom + sensors
python lottery.py -a 1 -b 49 -n 6 --rndauto --sensors

# Combine trandom + mouse + sensors (mouse and sensors are not mutually exclusive)
python lottery.py -a 1 -b 49 -n 6 --rndauto --mouse --sensors

# Enable colored output
python lottery.py -a 1 -b 49 -n 6 --color

# Highlight adjacent numbers in green
python lottery.py -a 1 -b 49 -n 6 --colorneighbor

# Combine both: neighbors in green, repeats in red
python lottery.py -a 1 -b 49 -n 6 --color --colorneighbor

# Write results to CSV file
python lottery.py -a 1 -b 49 -n 6 -w results.csv

# Colored output with trandom and keyboard
python lottery.py -a 1 -b 49 -n 6 --rndauto --keyboard --color

# Show remaining pool after each round (debug mode)
python lottery.py -a 1 -b 49 -n 6 --debug

# Draw 10 numbers from 1 to 100 with --minlen 5
python lottery.py -a 1 -b 100 -n 10 --minlen 5

# Repeat the full drawing cycle 3 times (fresh pool each time)
python lottery.py -a 1 -b 49 -n 6 --series 3

# Independent draws from the full pool (5 draws, each from [1..49])
python lottery.py -a 1 -b 49 -n 6 --fullpool --series 5

# Single draw from the full pool (--fullpool without --series = 1 draw)
python lottery.py -a 1 -b 49 -n 6 --fullpool

# Fullpool with neighbor constraint and color
python lottery.py -a 1 -b 49 -n 6 --fullpool --series 10 --nei 1,2 --color

# Repeat 20 times with sensor entropy collected at each new series
python lottery.py -a 1 -b 49 -n 6 --series 20 --rndauto --sensors --seriesentropy

# Combine --series with --nei
python lottery.py -a 1 -b 49 -n 6 --series 5 --nei 1,2

# Edge case: n equals the range size — only one draw consumes everything
python lottery.py -a 1 -b 6 -n 6

# Edge case: n larger than the range
python lottery.py -a 1 -b 10 -n 12

# Parallel execution: 100 series across 4 threads
python lottery.py -a 1 -b 49 -n 6 --series 100 --threads 4

# Parallel execution with fullpool (6 independent draws, 3 threads)
python lottery.py -a 1 -b 49 -n 6 --fullpool --series 6 --threads 3 --color

# Parallel execution with nei constraint
python lottery.py -a 1 -b 49 -n 6 --series 50 --threads 5 --nei 1,2
```

---

## Entropy Consumption Model

When `--mouse`, `--keyboard`, or `--sensors` is used with `--rndauto`,
the collected entropy samples are stored in memory before any drawing
begins.  Each call to `gather()` (which happens internally for every
`random_int()` call) consumes **all** stored samples at once and mixes
them with the 7 always-active entropy sources via SHA3-512 + SHA-256.

This means:

- With the default 250 samples, the **first** random number drawn
  benefits from all 250 extra samples.  Subsequent draws use only the 7
  standard sources (which are themselves strong — system CSPRNG, CPU
  jitter, disk timing, etc.).

- If you want extra entropy distributed across more draws, increase
  `--samples`.  Each `gather()` call consumes the extra data in one
  batch.

- In practice the 7 standard sources provide more than enough entropy
  for lottery-style drawing; the additional sources are a demonstration
  of multi-source entropy harvesting.

---

## How the RNG Backend Works

### Python Mode (default)

Uses `random.sample(population, k)` for drawing without replacement and
`random.randint(a, b)` internally.  This is the Mersenne Twister PRNG
— deterministic, reproducible, and fast.

### trandom Mode (`--rndauto` / `--rnd auto`)

Imports the `TrueRandom` class from `trandom.py`.  Each draw uses
`trng.random_int(i, n-1)` inside a Fisher-Yates partial shuffle to
produce a random sample without replacement.  The `use_mouse`,
`use_keyboard`, and `use_sensors` flags are passed through so that the
collected extra entropy is mixed in on every `gather()` call.

When `--mouse`, `--keyboard`, or `--sensors` is requested, the script
first enters a collection phase.  Mouse and keyboard show an interactive
progress bar using `#` symbols (updates every 5 samples):

```
[*] Move your mouse around to collect entropy
[*] Collecting mouse entropy (timeout: unlimited, target: 250 samples)
    Move your mouse around now!

Mouse entropy   12.0% [####..........................]  30/250
...
Mouse entropy  100.0% [##############################]  250/250

[+] Collected 250 mouse entropy samples
   1:  ...
```

Hardware sensor collection (`--sensors`) shows a similar progress bar:

```
Sensor entropy   20.0% [######........................]  1/5
Sensor entropy   40.0% [############..................]  2/5
...
Sensor entropy  100.0% [##############################]  5/5
```

Mouse/keyboard collection stops when the target number of samples is
reached (no time limit by default).  Sensor collection always takes 5
readings (hardcoded in `trandom.py`).

---

## Edge Cases and Warnings

- **`n > range size`**: A warning is printed, and the script draws as
  many numbers as it can.  The final round takes the leftovers and
  refills from the full set.  After this single refill round the script
  stops.

- **`--minlen` too large**: If the constraint makes it impossible to
  draw a valid set (checked by `can_pick()`), the constraint is relaxed
  for that round and a plain draw is made instead.  This prevents an
  infinite loop.

- **`--mouse` without `--rndauto`**: The `--mouse`, `--keyboard`, and
  `--sensors` flags have no effect unless `--rndauto` (or `--rnd auto`)
  is also given.

- **`--mouse` and `--keyboard` together**: These are mutually exclusive
  and will cause the script to exit with an error if both are given.

- **Missing `trandom.py`**: When `--rndauto` is used and `trandom.py`
  is not found, the script will exit with an ImportError.  Place
  `trandom.py` in the same directory as `lottery.py`.

---

## Comparison of RND Modes

| Mode | Generator | Entropy Sources | Interactive? | Deterministic? |
|---|---|---|---|---|
| default (python) | Mersenne Twister | None (PRNG) | No | Yes (seeded) |
| `--rndauto` | trandom.py | 7 hardware/system sources | No | No |
| `--rndauto --mouse` | trandom.py | 7 + mouse movements | Yes (move mouse) | No |
| `--rndauto --keyboard` | trandom.py | 7 + keyboard presses | Yes (press keys) | No |
| `--rndauto --sensors` | trandom.py | 7 + hardware sensors | No | No |

---

## File Structure

| File | Description |
|---|---|
| `lottery.py` | Main lottery script (single file, no install needed) |
| `trandom.py` | True random number generator used by `--rndauto` |
| `README_lottery.md` | This documentation |

---

## Notes

- The script uses `argparse` with custom `-h` / `--help` handling.  `-h`
  prints a one-line usage summary; `--help` prints the full
  documentation.
- ANSI color support is provided via inline escape codes.  The
  `colorama` package is imported if available but is not required.
- The script is a single file with no required external dependencies on
  Windows.

## My Examples
- For one series:
python lottery.py -a 1 -b 49 -n 6  --rndauto --mouse --sensors --samples 512 --color -w result.csv --colorneighbor

Result on screen:

[*] Move your mouse around to collect entropy
[*] Collecting mouse entropy (timeout: unlimited, target: 512 samples)
    Move your mouse around now!

Mouse entropy  100.0% [##############################]  512/512
[+] Collected 512 mouse entropy samples
[*] Reading hardware sensors (CPU temp, fans, voltages, battery)
Sensor entropy  100.0% [##############################]  5/5
[+] Collected 5 sensor entropy samples
  1: 28  7 27 25 43 36
  2: 37 44 42 14 20 46
  3:  2  4 23 12 31 47
  4:  3 30 13 33 39 32
  5: 49 48 10 15 41 16
  6: 26 38 29  1 40 21
  7: 22 19 45 17 34  6
  8:  9 11  5 35 24  8
  9: 18 25 46 42 41 21

- For 100 series:
python lottery.py -a 1 -b 49 -n 6  --rndauto --mouse --sensors --samples 512 --color --series 100 -w result.csv --colorneighbor --seriesentropy --numbering ext

Result on screen:

...

--- Generating new series (series 99/100) ---
Sensor entropy  100.0% [##############################]  5/5

883/1: 24 15 27 49  9 33
884/2: 21 22 36 26 42 37
885/3: 34  8  3 11  7 30
886/4: 32 38 47 20  4 41
887/5: 17 28 43 40 23 12
888/6: 29 16 25  5 10 19
889/7: 31 39  2 44 14  1
890/8: 35 18 46  6 48 45
891/9: 13  8 10 11 28 34

--- Generating new series (series 100/100) ---
Sensor entropy  100.0% [##############################]  5/5

892/1: 34  7 28 48 39  2
893/2: 11 41  8 47 45 33
894/3: 30 42 38 15 22 20
895/4: 19 18 44 27 32 26
896/5: 14 31 40  6 29 43
897/6: 25  9 24 46 21 17
898/7:  3 35  1 16 13 23
899/8:  5 49  4 36 37 12
900/9: 10 11 42 41 35 47
