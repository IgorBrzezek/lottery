# ======================================================
# Lottery
#
# Multi-round lottery number drawing without replacement.
# Supports Python's random module or trandom.py (true
# multi-source entropy) as the RNG backend.
# ======================================================

import random
import argparse
import sys
import os

VERSION = 0.5 
AUTHOR = "igor.brzezek@gmail.com"
GITHUB = "https://github.com/IgorBrzezek/lottery"

MAX_ATTEMPTS = 1000


def has_adjacent(nums):
    s = sorted(nums)
    for i in range(len(s) - 1):
        if s[i + 1] - s[i] == 1:
            return True
    return False

def count_neighbor_runs(nums, m):
    s = sorted(nums)
    count = 0
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] - s[j] == 1:
            j += 1
        run_len = j - i + 1
        count += run_len // m
        i = j + 1
    return count


def parse_nei(s):
    parts = [int(x.strip()) for x in s.split(",")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("--nei requires N,M")
    return tuple(parts)


def has_close(nums, minlen):
    s = sorted(nums)
    for i in range(len(s) - 1):
        if s[i + 1] - s[i] < minlen:
            return True
    return False

def can_pick(nums, n, min_gap):
    if min_gap <= 1:
        return len(nums) >= n
    s = sorted(nums)
    count = 1
    last = s[0]
    for i in range(1, len(s)):
        if s[i] - last >= min_gap:
            count += 1
            last = s[i]
            if count >= n:
                return True
    return False

try:
    import colorama
    colorama.init()
except ImportError:
    pass

WHITE = '\033[97m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RESET = '\033[0m'



# -------------------------------------------------------
#  RNG backends
# -------------------------------------------------------

RNG_MODES = ['python', 'auto']

_trng_instance = None
_use_trng = False

def _get_trng():
    global _trng_instance
    if _trng_instance is None:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from trandom import TrueRandom
        _trng_instance = TrueRandom(verbose=False)
    return _trng_instance

def _collect_trng_extra(samples=250):
    trng = _get_trng()
    if args.mouse:
        print("[*] Move your mouse around to collect entropy", flush=True)
    if args.keyboard:
        print("[*] Press keys on the keyboard to collect entropy", flush=True)
    if args.mouse or args.keyboard:
        trng.verbose = True
    if args.mouse:
        if not os.name == 'nt':
            print("Warning: --mouse on Linux/macOS requires: pip install pynput", file=sys.stderr)
        trng.collect_mouse_entropy(duration=None, samples=samples)
    if args.keyboard:
        trng.collect_keyboard_entropy(duration=None, samples=samples)
    if args.sensors:
        trng.collect_sensor_entropy()
    if args.mouse or args.keyboard:
        trng.verbose = False

def _trng_kwargs():
    return {
        'use_mouse': args.mouse,
        'use_keyboard': args.keyboard,
        'use_sensors': args.sensors,
    }

def _trandom_sample(population, k):
    trng = _get_trng()
    kwargs = _trng_kwargs()
    n = len(population)
    indices = list(range(n))
    for i in range(k):
        j = trng.random_int(i, n - 1, **kwargs)
        indices[i], indices[j] = indices[j], indices[i]
    return [population[i] for i in indices[:k]]

# -------------------------------------------------------
#  Threading helpers
# -------------------------------------------------------

from concurrent.futures import ThreadPoolExecutor

def _draw_sample_core(rng, pool, n, minlen, noneighbor, nei, max_attempts):
    if minlen is not None and not can_pick(pool, n, minlen):
        return rng.sample(pool, n)
    nei_attempts = 0
    while True:
        draw = rng.sample(pool, n)
        if (not noneighbor or not has_adjacent(draw)) and (minlen is None or not has_close(draw, minlen)):
            if nei is None or count_neighbor_runs(draw, nei[1]) == nei[0]:
                break
            nei_attempts += 1
            if nei_attempts >= max_attempts:
                break
    return draw

def _draw_refill_core(rng, avail, need, existing_draw, minlen, noneighbor, nei, max_attempts):
    extra = []
    if minlen is not None:
        filtered = [x for x in avail if all(abs(x - d) >= minlen for d in existing_draw)]
        if not can_pick(filtered, need, minlen):
            extra = rng.sample(avail, min(need, len(avail)))
    if not extra:
        while True:
            extra = rng.sample(avail, min(need, len(avail)))
            if (not noneighbor or not has_adjacent(existing_draw + extra)) and (minlen is None or not has_close(existing_draw + extra, minlen)):
                break
    return extra

def _thread_worker(a, b, n, minlen, noneighbor, nei, is_fullpool, num_items, seed):
    rng = random.Random(seed)
    full_list = list(range(a, b + 1))
    seen = set()
    results = []
    for _ in range(num_items):
        if is_fullpool:
            draw = _draw_sample_core(rng, full_list, n, minlen, noneighbor, nei, MAX_ATTEMPTS)
            repeats = [d in seen for d in draw]
            seen.update(draw)
            results.append((draw, repeats))
        else:
            remaining = list(full_list)
            ser_seen = set()
            while remaining:
                if len(remaining) >= n:
                    draw = _draw_sample_core(rng, remaining, n, minlen, noneighbor, nei, MAX_ATTEMPTS)
                    for d in draw:
                        remaining.remove(d)
                else:
                    draw = list(remaining)
                    remaining.clear()
                    need = n - len(draw)
                    if need > 0:
                        avail = [x for x in full_list if x not in draw]
                        extra = _draw_refill_core(rng, avail, need, draw, minlen, noneighbor, nei, MAX_ATTEMPTS)
                        draw.extend(extra)
                repeats = [d in seen or d in ser_seen for d in draw]
                ser_seen.update(draw)
                seen.update(draw)
                results.append((draw, repeats))
    return results

def _draw_progress(current, total):
    if total <= 0:
        return
    pct = current / total * 100
    w = 30
    filled = int(w * current / total)
    bar = '#' * filled + '-' * (w - filled)
    print(f'\r  [{bar}] {pct:5.1f}%', file=sys.stderr, end='')
    if current >= total:
        print(file=sys.stderr)

# -------------------------------------------------------
#  File display (for -in)
# -------------------------------------------------------

def display_infile(filename):
    try:
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
    except IOError as e:
        print(f'Error: cannot read {filename}: {e}', file=sys.stderr)
        sys.exit(1)

    if not lines:
        return

    if not args.color and not args.colorneighbor:
        for line in lines:
            print(line)
        return

    parsed = []
    all_nums = []
    max_rnd = 0
    for line in lines:
        parts = line.split(',')
        rnd = int(parts[0])
        nums = [int(x) for x in parts[1:]]
        parsed.append((rnd, nums))
        all_nums.extend(nums)
        max_rnd = max(max_rnd, rnd)

    width = len(str(max(all_nums))) if all_nums else 1
    rnd_width = len(str(max_rnd)) if max_rnd else 1
    seen = set()

    for rnd, nums in parsed:
        neighbor_nums = set()
        if args.colorneighbor:
            s = sorted(nums)
            for i in range(len(s) - 1):
                if s[i + 1] - s[i] == 1:
                    neighbor_nums.add(s[i])
                    neighbor_nums.add(s[i + 1])

        items = []
        for num in nums:
            if args.colorneighbor and num in neighbor_nums:
                items.append(f'{GREEN}{num:>{width}}{RESET}')
            elif args.color:
                color = RED if num in seen else WHITE
                items.append(f'{color}{num:>{width}}{RESET}')
            else:
                items.append(f'{num:>{width}}')
            seen.add(num)

        print(f'{rnd:{rnd_width}d}: {" ".join(items)}')

# -------------------------------------------------------
#  CLI
# -------------------------------------------------------

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-a', '--from', type=int, metavar='INT', dest='a')
parser.add_argument('-b', '--to', type=int, metavar='INT', dest='b')
parser.add_argument('-n', '--count', type=int, metavar='INT', dest='n')
parser.add_argument('-nn', '--noneighbor', action='store_true', dest='noneighbor')
parser.add_argument('--minlen', type=int, metavar='INT', dest='minlen')
parser.add_argument('--nei', type=parse_nei, metavar='N,M', dest='nei',
                    help='require exactly N runs of M consecutive numbers (e.g., --nei 1,2)')
parser.add_argument('--series', type=int, metavar='N', dest='series',
                    help='repeat the entire drawing process N times, each starting from a fresh pool')
parser.add_argument('--fullpool', action='store_true', dest='fullpool',
                    help='each draw uses the full pool [a..b] without removing numbers; --series N determines the number of draws')
parser.add_argument('-t', '--threads', type=int, metavar='N', dest='threads',
                    help='run draws in N parallel threads (requires --series)')
parser.add_argument('--debug', action='store_true', dest='debug')
parser.add_argument('-h', action='store_true', dest='short_help')
parser.add_argument('--help', action='store_true', dest='long_help')
parser.add_argument('--rndauto', action='store_true', dest='rndauto',
                    help='use trandom.py true random generator (7 always-active entropy sources)')
parser.add_argument('--rnd', type=str, choices=RNG_MODES, default='python', dest='rnd_mode',
                    help="random generator: python|auto (default: python)")
parser.add_argument('--mouse', action='store_true', dest='mouse',
                    help='add mouse-movement entropy (interactive, requires --rndauto)')
parser.add_argument('--keyboard', action='store_true', dest='keyboard',
                    help='add keyboard-press entropy (interactive, mutually exclusive with --mouse)')
parser.add_argument('--sensors', action='store_true', dest='sensors',
                    help='add hardware sensor entropy (CPU temp, fans)')
parser.add_argument('--samples', type=int, default=250, dest='samples',
                    help='number of mouse/keyboard samples to collect (default 250)')
parser.add_argument('--color', action='store_true', dest='color',
                    help='enable colored output (ANSI); without this flag, output is plain ASCII')
parser.add_argument('--colorneighbor', action='store_true', dest='colorneighbor',
                    help='highlight adjacent numbers in green')
parser.add_argument('--seriesentropy', action='store_true', dest='seriesentropy',
                    help='re-collect sensor entropy at each new series when using --series (requires --rndauto)')
parser.add_argument('--numbering', type=str, choices=['cont', 'ext'], default='cont', dest='numbering',
                    help='round numbering: cont (continuous, default) or ext (continuous/series round)')
parser.add_argument('-w', '--write', type=str, metavar='FILENAME', dest='write',
                    help='write drawn numbers to CSV file (one round per line, comma-separated; blank line between series)')
parser.add_argument('--wcont', action='store_true', dest='wcont',
                    help='write CSV continuously without blank line separators between series')
parser.add_argument('-in', '--infile', type=str, metavar='FILE', dest='infile',
                    help='read and display a CSV file previously written with -w')
parser.add_argument('--nodisplay', action='store_true', dest='nodisplay',
                    help='suppress terminal output (requires -w)')
parser.add_argument('--pb', '--progressbar', action='store_true', dest='pb',
                    help='show progress bar (requires --nodisplay)')

args = parser.parse_args()

if args.infile:
    display_infile(args.infile)
    sys.exit(0)

# resolve rnd mode: --rndauto is shorthand for --rnd auto
if args.rndauto:
    args.rnd_mode = 'auto'

# mutual exclusion
if args.mouse and args.keyboard:
    print('error: --mouse and --keyboard are mutually exclusive', file=sys.stderr)
    sys.exit(1)

if args.minlen is not None and args.nei is not None:
    print('error: --minlen and --nei are mutually exclusive', file=sys.stderr)
    sys.exit(1)

_use_trng = (args.rnd_mode != 'python')

# -------------------------------------------------------
#  Help
# -------------------------------------------------------

if args.short_help:
    print('Usage: python lottery.py -a FROM -b TO -n COUNT [--series N] [--fullpool] [-t N] [-w FILENAME] [--wcont] [--nodisplay] [--pb] [-in FILE] [--nei N,M] [--rndauto] [--rnd MODE] [--color] [--colorneighbor] [--seriesentropy] [--numbering cont|ext]')
    sys.exit(0)

if args.long_help:
    print('Lottery-style number drawing without replacement.')
    print()
    print('Draws n numbers from range [FROM, TO] in each round,')
    print('removing them from the pool.  When fewer than n numbers')
    print('remain, takes the leftovers and refills the round from')
    print('the full set, then stops.')
    print()
    print('With --series N the entire drawing process (a full pool cycle)')
    print('is repeated N times.  A separator line is printed between each')
    print('series showing the series number.')
    print('With --fullpool, each draw uses the full range [FROM, TO] without')
    print('removing numbers from the pool.  --series N sets the number of')
    print('draws (default: 1).  Without --fullpool the original behavior')
    print('(removing drawn numbers until pool exhaustion) is used.')
    print('With --threads N the work is split across N parallel threads')
    print('(each with its own RNG).  Requires --series.  Repeat tracking')
    print('is thread-local.')
    print('With --seriesentropy, sensor entropy is re-collected')
    print('at each new series (requires --rndauto).')
    print()
    print('Random generator:')
    print('  Default          Python built-in random.sample / random.randint')
    print('  --rndauto        Use trandom.py with 7 always-active entropy sources')
    print('  --rnd auto       Same as --rndauto')
    print('  --rnd python     Use Python random module (default)')
    print()
    print('Additional entropy (only with --rndauto / --rnd auto):')
    print('  --mouse          Add mouse-movement entropy (interactive)')
    print('  --keyboard       Add keyboard-press entropy (interactive)')
    print('  --sensors        Add hardware sensor entropy')
    print('  --samples N      Number of mouse/keyboard samples (default 250)')
    print('  Note: --mouse and --keyboard are mutually exclusive.')
    print()
    print('Output:')
    print('  --color   Enable ANSI colored output (new numbers white, repeats red).')
    print('            Without this flag, output is plain ASCII without color codes.')
    print('  -w, --write FILENAME')
    print('            Write drawn numbers to CSV file (one round per line,')
    print('            comma-separated; blank line between series).')
    print('  --wcont   With -w, write CSV continuously without blank line')
    print('            separators between series.')
    print('  --nodisplay   Suppress all terminal output (requires -w).')
    print('  --pb, --progressbar')
    print('            Show progress bar on stderr (requires --nodisplay).')
    print('  -in, --infile FILE')
    print('            Read and display a CSV file previously written with -w.')
    print('            With --color, numbers are colored as on screen.')
    print('            With --colorneighbor, adjacent numbers are highlighted.')
    print()
    print(f'Version: {VERSION}')
    print(f'Author: {AUTHOR}')
    print()
    print('Options:')
    print('  -a, --from INT    Start of the range')
    print('  -b, --to   INT    End of the range (inclusive)')
    print('  -n, --count INT   Numbers to draw per round')
    print('  -w, --write FILENAME  Write drawn numbers to CSV file (blank line between series)')
    print('  --wcont               With -w, skip blank line separators between series')
    print('  -in, --infile FILE    Read and display a CSV file written with -w')
    print('  --nodisplay           Suppress terminal output (requires -w)')
    print('  --pb, --progressbar   Show progress bar on stderr (requires --nodisplay)')
    print('  -nn, --noneighbor      Prevent adjacent numbers (differing by 1) in the same draw')
    print('  --minlen INT      Minimum distance between any two drawn numbers')
    print('  --nei N,M         Require exactly N runs of M consecutive numbers (e.g., --nei 1,2)')
    print('  --series N        Repeat the drawing process N times (fresh pool each time)')
    print('  --fullpool        Each draw uses the full pool [a..b] without removal; --series N sets draw count')
    print('  -t, --threads N   Run draws in N parallel threads (requires --series)')
    print('  --debug           Show remaining numbers in brackets')
    print('  --rndauto         Use trandom.py (7 always-active entropy sources)')
    print('  --rnd MODE        Generator: python|auto (default: python)')
    print('  --mouse           Add mouse-movement entropy (with --rndauto)')
    print('  --keyboard        Add keyboard-press entropy (with --rndauto)')
    print('  --sensors         Add hardware sensor entropy (with --rndauto)')
    print('  --samples N       Mouse/keyboard samples to collect (default 250)')
    print('  --color           Enable ANSI colored output')
    print('  --colorneighbor   Highlight adjacent numbers in green')
    print('  --seriesentropy   Re-collect sensor entropy at each pool reset (requires --rndauto)')
    print('  --numbering       Round numbering: cont (continuous, default) or ext (continuous/series round)')
    print('  -h                Show this help')
    print('  --help            Show detailed help')
    sys.exit(0)

if args.a is None or args.b is None or args.n is None:
    print('Error: -a, -b, and -n are required.')
    print('Usage: python 6z49_DeepSeek.py -a FROM -b TO -n COUNT')
    print('Use -h for help or --help for detailed help.')
    sys.exit(1)

if args.nodisplay and not args.write:
    print('error: --nodisplay requires -w FILENAME', file=sys.stderr)
    sys.exit(1)

if args.pb and not args.nodisplay:
    print('error: --pb/--progressbar requires --nodisplay', file=sys.stderr)
    sys.exit(1)

a, b, n = args.a, args.b, args.n

full = list(range(a, b + 1))
remaining = list(full)
seen = set()
width = len(str(b))

min_gap = 0
if args.minlen is not None:
    min_gap = args.minlen
elif args.noneighbor:
    min_gap = 2

rnd = 1

if args.series is not None and args.series < 1:
    print('error: --series must be >= 1', file=sys.stderr)
    sys.exit(1)

if n > len(full):
    print(f'Warning: n ({n}) exceeds range size ({len(full)}), not enough unique numbers to refill.')

# pre-collect additional entropy (mouse/keyboard/sensors)
if _use_trng and (args.mouse or args.keyboard or args.sensors):
    try:
        _collect_trng_extra(samples=args.samples)
    except Exception as e:
        print(f'Error: failed to initialize trandom extra entropy: {e}', file=sys.stderr)
        print('Make sure trandom.py is in the same directory.', file=sys.stderr)
        sys.exit(1)

# open CSV output file
csv_file = None
if args.write:
    try:
        csv_file = open(args.write, 'w', newline='')
    except IOError as e:
        print(f'Error: cannot write to {args.write}: {e}', file=sys.stderr)
        sys.exit(1)

if args.nodisplay:
    sys.stdout = open(os.devnull, 'w')

def _sample(pop, k):
    if _use_trng:
        return _trandom_sample(pop, k)
    return random.sample(pop, k)

max_series = args.series
fullpool_draws = max_series if max_series is not None else 1 if args.fullpool else 0
series_num = 1
numbering = args.numbering
rnd_width = 3
ser_rnd = 0
ser_width = 1

if max_series is not None:
    if numbering == 'cont':
        rnd_width = len(str(max_series))
    elif args.fullpool:
        rnd_width = len(str(max_series))
        ser_width = len(str(max_series))
    else:
        draws_per_pool = len(full) // n
        if len(full) % n != 0:
            draws_per_pool += 1
        rnd_width = len(str(max_series * draws_per_pool))
        ser_width = len(str(draws_per_pool))

# -------------------------------------------------------
#  Threaded execution path
# -------------------------------------------------------

if args.threads and args.threads > 1:
    if _use_trng:
        print('Warning: --threads uses Python random (trandom not supported in parallel)', file=sys.stderr)

    if args.fullpool:
        total = fullpool_draws
    elif max_series is not None:
        total = max_series
    else:
        print('error: --threads requires --series', file=sys.stderr)
        sys.exit(1)

    if total <= 0:
        sys.exit(0)

    base = total // args.threads
    rem = total % args.threads
    batches = []
    for i in range(args.threads):
        size = base + (1 if i < rem else 0)
        if size > 0:
            batches.append((a, b, n, args.minlen, args.noneighbor, args.nei, args.fullpool, size, os.urandom(16)))

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(_thread_worker, *batch) for batch in batches]
        all_results = []
        for i, f in enumerate(futures):
            all_results.append(f.result())
            if args.pb:
                _draw_progress(i + 1, len(futures))

    flat = []
    for batch in all_results:
        flat.extend(batch)

    rnd_w = len(str(len(flat)))
    for idx, (draw, repeats) in enumerate(flat, 1):
        neighbor_nums = set()
        if args.colorneighbor:
            s = sorted(draw)
            for i in range(len(s) - 1):
                if s[i + 1] - s[i] == 1:
                    neighbor_nums.add(s[i])
                    neighbor_nums.add(s[i + 1])
        items = []
        for num, is_repeat in zip(draw, repeats):
            if args.colorneighbor and num in neighbor_nums:
                items.append(f'{GREEN}{num:>{width}}{RESET}')
            elif args.color:
                color = RED if is_repeat else WHITE
                items.append(f'{color}{num:>{width}}{RESET}')
            else:
                marker = '*' if is_repeat else ' '
                items.append(f'{marker}{num:>{width}}')
        print(f'{idx:{rnd_w}d}: {" ".join(items)}')

    if csv_file:
        for idx, (draw, _) in enumerate(flat, 1):
            csv_file.write(f'{idx},' + ','.join(str(num) for num in draw) + '\n')
        csv_file.close()

    sys.exit(0)

# -------------------------------------------------------
#  Single-threaded path
# -------------------------------------------------------

if max_series is not None and not args.fullpool:
    msg = f'--- Generating new series (series 1/{max_series}) ---'
    if args.color:
        print(f'{YELLOW}{msg}{RESET}')
    else:
        print(msg)
    print()

while True:
    if args.fullpool:
        if rnd > fullpool_draws:
            break
    else:
        if max_series is not None:
            if not remaining:
                series_num += 1
                if series_num > max_series:
                    break
                print()
                msg = f'--- Generating new series (series {series_num}/{max_series}) ---'
                if args.color:
                    print(f'{YELLOW}{msg}{RESET}')
                else:
                    print(msg)
                if _use_trng and args.seriesentropy:
                    try:
                        _get_trng().collect_sensor_entropy()
                    except Exception as e:
                        print(f'Error: sensor entropy collection failed: {e}', file=sys.stderr)
                print()
                if csv_file and not args.wcont:
                    csv_file.write('\n')
                remaining = list(full)
                seen.clear()
                ser_rnd = 0
        elif not remaining:
            break

    pool = full if args.fullpool else remaining

    if len(pool) >= n:
        if args.minlen is not None and not can_pick(pool, n, args.minlen):
            draw = _sample(pool, n)
        else:
            nei_attempts = 0
            while True:
                draw = _sample(pool, n)
                if (not args.noneighbor or not has_adjacent(draw)) and (args.minlen is None or not has_close(draw, args.minlen)):
                    if args.nei is None or count_neighbor_runs(draw, args.nei[1]) == args.nei[0]:
                        break
                    nei_attempts += 1
                    if nei_attempts >= MAX_ATTEMPTS:
                        break
        if not args.fullpool:
            for d in draw:
                remaining.remove(d)
    elif args.fullpool:
        draw = list(full)
    else:
        draw = list(remaining)
        remaining.clear()
        need = n - len(draw)
        if need > 0:
            avail = [x for x in full if x not in draw]
            extra = []
            if args.minlen is not None:
                filtered = [x for x in avail if all(abs(x - d) >= args.minlen for d in draw)]
                if not can_pick(filtered, need, args.minlen):
                    extra = _sample(avail, min(need, len(avail)))
            if not extra:
                while True:
                    extra = _sample(avail, min(need, len(avail)))
                    if (not args.noneighbor or not has_adjacent(draw + extra)) and (args.minlen is None or not has_close(draw + extra, args.minlen)):
                        break
            draw.extend(extra)

    if csv_file:
        if max_series is not None:
            csv_file.write(f'{rnd:0{rnd_width}d},' + ','.join(str(num) for num in draw) + '\n')
        else:
            csv_file.write(f'{rnd},' + ','.join(str(num) for num in draw) + '\n')

    neighbor_nums = set()
    if args.colorneighbor:
        s = sorted(draw)
        for i in range(len(s) - 1):
            if s[i + 1] - s[i] == 1:
                neighbor_nums.add(s[i])
                neighbor_nums.add(s[i + 1])

    items = []
    for num in draw:
        if args.colorneighbor and num in neighbor_nums:
            items.append(f'{GREEN}{num:>{width}}{RESET}')
        elif args.color:
            color = RED if num in seen else WHITE
            items.append(f'{color}{num:>{width}}{RESET}')
        else:
            marker = '*' if num in seen else ' '
            items.append(f'{marker}{num:>{width}}')
        seen.add(num)

    ser_rnd += 1
    debug_info = f' [{",".join(map(str, remaining))}]' if args.debug else ''
    if numbering == 'ext':
        print(f'{rnd:{rnd_width}d}/{ser_rnd:{ser_width}d}: {" ".join(items)}{debug_info}')
    else:
        print(f'{rnd:{rnd_width}d}: {" ".join(items)}{debug_info}')
    rnd += 1
    if args.pb:
        if args.fullpool:
            _draw_progress(rnd - 1, fullpool_draws)
        elif max_series is not None:
            _dp = len(full) // n
            if len(full) % n != 0:
                _dp += 1
            _draw_progress(rnd - 1, max_series * _dp)

if csv_file:
    csv_file.close()
