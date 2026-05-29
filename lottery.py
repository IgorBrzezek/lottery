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

MAX_ATTEMPTS = 1000


def has_adjacent(nums):
    s = sorted(nums)
    for i in range(len(s) - 1):
        if s[i + 1] - s[i] == 1:
            return True
    return False

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
RED = '\033[91m'
RESET = '\033[0m'

VERSION = 0.2
AUTHOR = "igor.brzezek@gmail.com"
GITHUB = "https://github.com/IgorBrzezek/lottery"

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
#  CLI
# -------------------------------------------------------

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-a', '--from', type=int, metavar='INT', dest='a')
parser.add_argument('-b', '--to', type=int, metavar='INT', dest='b')
parser.add_argument('-n', '--count', type=int, metavar='INT', dest='n')
parser.add_argument('-nn', '--noneighbor', action='store_true', dest='noneighbor')
parser.add_argument('--minlen', type=int, metavar='INT', dest='minlen')
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
parser.add_argument('-w', '--write', type=str, metavar='FILENAME', dest='write',
                    help='write drawn numbers to CSV file (one round per line, comma-separated)')

args = parser.parse_args()

# resolve rnd mode: --rndauto is shorthand for --rnd auto
if args.rndauto:
    args.rnd_mode = 'auto'

# mutual exclusion
if args.mouse and args.keyboard:
    print('error: --mouse and --keyboard are mutually exclusive', file=sys.stderr)
    sys.exit(1)

_use_trng = (args.rnd_mode != 'python')

# -------------------------------------------------------
#  Help
# -------------------------------------------------------

if args.short_help:
    print('Usage: python lottery.py -a FROM -b TO -n COUNT [-w FILENAME] [--rndauto] [--rnd MODE] [--color]')
    sys.exit(0)

if args.long_help:
    print('Lottery-style number drawing without replacement.')
    print()
    print('Draws n numbers from range [FROM, TO] in each round,')
    print('removing them from the pool.  When fewer than n numbers')
    print('remain, takes the leftovers and refills the round from')
    print('the full set, then stops.')
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
    print('            comma-separated).  Terminal output remains unchanged.')
    print()
    print(f'Version: {VERSION}')
    print(f'Author: {AUTHOR}')
    print()
    print('Options:')
    print('  -a, --from INT    Start of the range')
    print('  -b, --to   INT    End of the range (inclusive)')
    print('  -n, --count INT   Numbers to draw per round')
    print('  -w, --write FILENAME  Write drawn numbers to CSV file')
    print('  -nn, --noneighbor      Prevent adjacent numbers (differing by 1) in the same draw')
    print('  --minlen INT      Minimum distance between any two drawn numbers')
    print('  --debug           Show remaining numbers in brackets')
    print('  --rndauto         Use trandom.py (7 always-active entropy sources)')
    print('  --rnd MODE        Generator: python|auto (default: python)')
    print('  --mouse           Add mouse-movement entropy (with --rndauto)')
    print('  --keyboard        Add keyboard-press entropy (with --rndauto)')
    print('  --sensors         Add hardware sensor entropy (with --rndauto)')
    print('  --samples N       Mouse/keyboard samples to collect (default 250)')
    print('  --color           Enable ANSI colored output')
    print('  -h                Show this help')
    print('  --help            Show detailed help')
    sys.exit(0)

if args.a is None or args.b is None or args.n is None:
    print('Error: -a, -b, and -n are required.')
    print('Usage: python 6z49_DeepSeek.py -a FROM -b TO -n COUNT')
    print('Use -h for help or --help for detailed help.')
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

def _sample(pop, k):
    if _use_trng:
        return _trandom_sample(pop, k)
    return random.sample(pop, k)

while remaining:
    if len(remaining) >= n:
        if args.minlen is not None and not can_pick(remaining, n, args.minlen):
            draw = _sample(remaining, n)
        else:
            while True:
                draw = _sample(remaining, n)
                if (not args.noneighbor or not has_adjacent(draw)) and (args.minlen is None or not has_close(draw, args.minlen)):
                    break
        for d in draw:
            remaining.remove(d)
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
        csv_file.write(','.join(str(num) for num in draw) + '\n')

    items = []
    for num in draw:
        if args.color:
            color = RED if num in seen else WHITE
            items.append(f'{color}{num:>{width}}{RESET}')
        else:
            marker = '*' if num in seen else ' '
            items.append(f'{marker}{num:>{width}}')
        seen.add(num)

    debug_info = f' [{",".join(map(str, remaining))}]' if args.debug else ''
    print(f'{rnd:3d}: {" ".join(items)}{debug_info}')
    rnd += 1

if csv_file:
    csv_file.close()
