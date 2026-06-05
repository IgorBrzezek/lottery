import argparse
import csv
import sys
from datetime import datetime

VERSION = 0.3
AUTHOR = "igor.brzezek@gmail.com"
GITHUB = "https://github.com/IgorBrzezek/lottery_stats"

RESET = "\033[0m"
BOLD = "\033[1m"
COLORS = ["\033[31m", "\033[32m", "\033[33m", "\033[34m", "\033[35m", "\033[36m"]


def enable_ansi():
    if sys.platform != "win32":
        return
    try:
        import colorama
        colorama.init()
        return
    except ImportError:
        pass
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        h = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(h, ctypes.byref(mode))
        kernel32.SetConsoleMode(h, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    except Exception:
        pass


def parse_date(d):
    return datetime.strptime(d, "%d.%m.%Y")


def parse_format(fmt):
    if fmt is None or fmt == "lotto":
        return None
    rest = fmt[4:].strip().lstrip("(").rstrip(")")
    return [int(x.strip()) - 1 for x in rest.split(",")]


def parse_num_list(s):
    return [int(x.strip()) for x in s.split(",")]


def load_data(path, columns=None, date_min=None, date_max=None):
    counts = {}
    total_draws = 0
    total_numbers = 0

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if columns is not None:
                if any(i >= len(row) for i in columns):
                    continue
                numbers = [row[i] for i in columns]
            else:
                if len(row) < 3:
                    continue
                date_str = row[1].strip()
                if date_min and parse_date(date_str) < date_min:
                    continue
                if date_max and parse_date(date_str) > date_max:
                    continue
                numbers = row[2:]
            total_draws += 1
            for n in numbers:
                total_numbers += 1
                try:
                    val = int(n)
                except ValueError:
                    continue
                counts[val] = counts.get(val, 0) + 1

    return counts, total_draws, total_numbers


def c(text, color_index, use_color):
    if not use_color:
        return text
    return COLORS[color_index % len(COLORS)] + text + RESET


def show_single(counts, num, total_draws, total_numbers, use_color, acc):
    c_ = counts.get(num, 0)
    pct = c_ / total_numbers * 100

    print(f"\n  Statistics for number {num}:\n")

    num_str = c(f"{num}", 1, use_color)
    count_str = c(f"{c_}", 2, use_color)
    total_str = c(f"{total_numbers}", 3, use_color)
    draws_str = c(f"{total_draws}", 4, use_color)
    pct_str = c(f"{pct:.{acc}f}%", 1, use_color)
    print(f"Number {num_str} appears {count_str} times out of {total_str} numbers drawn ({draws_str} draws)")
    print(f"Percentage share: {pct_str}")

    max_c = max(counts.values())
    max_pct = max_c / total_numbers * 100
    bar_len = round(pct / max_pct * 40) if max_pct > 0 else 0
    bar = "#" * bar_len
    label = c(f"{num:2d}", num, use_color) if use_color else f"{num:2d}"
    hist_pct = c(f"{pct:{acc+4}.{acc}f}%", num, use_color) if use_color else f"{pct:{acc+4}.{acc}f}%"
    print(f"{label} | {hist_pct} {bar}")


def show_histogram(counts, total_draws, total_numbers, use_color, acc, top_n=None):
    items = sorted(counts.items(), key=lambda x: -x[1])
    if top_n:
        items = items[:top_n]
        print(f"\n  Statistics for {top_n} most frequent numbers:\n")
    else:
        items = [(i, counts.get(i, 0)) for i in range(1, 50)]
        print(f"\n  Statistics for all numbers (1-49):\n")

    max_pct = max(c / total_numbers * 100 for _, c in items)

    for num, c_ in items:
        pct = c_ / total_numbers * 100
        bar_len = round(pct / max_pct * 40) if max_pct > 0 else 0
        bar = "#" * bar_len
        label = c(f"{num:2d}", num, use_color) if use_color else f"{num:2d}"
        count_str = c(f"{c_:>4}", 1, use_color) if use_color else f"{c_:>4}"
        draws_str = c(f"{total_draws}", 4, use_color) if use_color else f"{total_draws}"
        pct_str = c(f"{pct:{acc+4}.{acc}f}%", num, use_color) if use_color else f"{pct:{acc+4}.{acc}f}%"
        print(f"{label} | {count_str}/{draws_str} | {pct_str} {bar}")


def show_neighbors(path, columns, date_min, date_max, use_color, nncolor=False, nosort=False):
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if columns is not None:
                if any(i >= len(row) for i in columns):
                    continue
                numbers = [row[i] for i in columns]
                prefix = ""
            else:
                if len(row) < 3:
                    continue
                date_str = row[1].strip()
                if date_min and parse_date(date_str) < date_min:
                    continue
                if date_max and parse_date(date_str) > date_max:
                    continue
                numbers = row[2:]
                prefix = f"{row[0]} {row[1]}:"

            int_nums = [int(n) for n in numbers]
            sorted_ints = sorted(int_nums)
            display = int_nums if nosort else sorted_ints

            neighbor_ints = set()
            for i in range(len(sorted_ints) - 1):
                if sorted_ints[i + 1] - sorted_ints[i] == 1:
                    neighbor_ints.add(sorted_ints[i])
                    neighbor_ints.add(sorted_ints[i + 1])

            parts = []
            if not neighbor_ints and nncolor:
                for n in display:
                    parts.append(YELLOW + str(n) + RESET)
            else:
                for n in display:
                    if n in neighbor_ints and use_color:
                        parts.append(GREEN + str(n) + RESET)
                    else:
                        parts.append(str(n))
            line = ", ".join(parts)
            if prefix:
                print(f"{prefix} {line}")
            else:
                print(line)


def show_neighborstats(path, columns, date_min, date_max, use_color, acc):
    pair_counts = {}

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if columns is not None:
                if any(i >= len(row) for i in columns):
                    continue
                numbers = [row[i] for i in columns]
            else:
                if len(row) < 3:
                    continue
                date_str = row[1].strip()
                if date_min and parse_date(date_str) < date_min:
                    continue
                if date_max and parse_date(date_str) > date_max:
                    continue
                numbers = row[2:]

            ints = sorted(int(n) for n in numbers)
            for i in range(len(ints) - 1):
                if ints[i + 1] - ints[i] == 1:
                    pair = (ints[i], ints[i + 1])
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1

    if not pair_counts:
        print("No consecutive pairs found")
        return

    sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[0])
    max_count = max(c for _, c in sorted_pairs)

    print(f"\n  Consecutive pair statistics:\n")
    for rank, (pair, count) in enumerate(sorted_pairs, 1):
        bar_len = round(count / max_count * 40) if max_count > 0 else 0
        bar = "#" * bar_len
        pair_str = f"{pair[0]}-{pair[1]}"
        rank_s = c(f"{rank:2d}.", 0, use_color) if use_color else f"{rank:2d}."
        val_s = c(f"{pair_str:>5}", rank, use_color) if use_color else f"{pair_str:>5}"
        count_s = c(f"{count:>4}", rank + 1, use_color) if use_color else f"{count:>4}"
        print(f"{rank_s} {val_s}  {count_s}  {bar}")


def show_mostfreq(counts, n, total_draws, total_numbers, use_color, acc):
    sorted_items = sorted(counts.items(), key=lambda x: -x[1])[:n]
    print(f"\n  Statistics for {n} most frequent numbers:\n")
    for rank, (num, c_) in enumerate(sorted_items, 1):
        pct = c_ / total_numbers * 100
        bar_len = round(pct / (sorted_items[0][1] / total_numbers * 100) * 20) if c_ > 0 else 0
        bar = "#" * bar_len
        rank_s = c(f"{rank:2d}.", 0, use_color)
        num_s = c(f"{num:2d}", rank, use_color)
        count_s = c(f"{c_}", rank + 1, use_color)
        pct_s = c(f"{pct:{acc+4}.{acc}f}%", rank + 2, use_color)
        print(f"{rank_s} #{num_s}  {count_s:>4} times  {pct_s}  {bar}")


SHORT_HELP = """usage: lottery_stats.py -in FILE [-num N] [--auto] [--mostfreq N] [--neighbors] [options]

Analyze lottery CSV data. Columns: draw_nr, date, num1..num6.

Modes (one required):
  -in FILE               Input CSV file
  -num N[,M,...]         Stats for one or more numbers (comma-separated)
  --auto                 Histogram for numbers 1-49
  --mostfreq N           Top N most frequent numbers
  --neighbors            Show rows with consecutive numbers

Options:
  -h                     This short help
  --help                 Full help (all options)
  -acc N                 Decimal places (default: 2)
  --color                ANSI colored output
  --nncolor              Highlight rows without neighbors in yellow
  --nosort               Display numbers in original order (do not sort)
  --format FORMAT        'lotto' or 'cols col1,col2,...'
  --datemin DD.MM.YYYY   Start date filter
  --datemax DD.MM.YYYY   End date filter
"""


class ShortHelpAction(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=None):
        super().__init__(option_strings=option_strings, dest=dest, default=default, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        print(SHORT_HELP)
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze lottery draw statistics from a CSV file.",
        add_help=False,
    )
    parser.add_argument("-in", dest="infile", required=True, help="Input CSV file with lottery results")
    parser.add_argument("-num", type=parse_num_list, help="Number(s) to analyze (comma-separated: N[,M,...])")
    parser.add_argument("--auto", action="store_true", help="Show percentage histogram for numbers 1-49")
    parser.add_argument("--mostfreq", type=int, metavar="N", help="Show top N most frequent numbers")
    parser.add_argument("--neighbors", action="store_true", help="Show rows with consecutive numbers (neighbors)")
    parser.add_argument("--neighborstats", action="store_true", help="Statistics for most frequent consecutive number pairs")
    parser.add_argument("--nncolor", action="store_true", help="Highlight rows without neighbors in yellow")
    parser.add_argument("--nosort", action="store_true", help="Display numbers in original order (do not sort)")
    parser.add_argument("--color", action="store_true", help="Enable ANSI colored output")
    parser.add_argument("--datemin", type=str, help="Start date (DD.MM.YYYY)")
    parser.add_argument("--datemax", type=str, help="End date (DD.MM.YYYY)")
    parser.add_argument("--format", type=str, default="lotto", help="Column format: \"lotto\" or \"cols 1,2,...\" (default: lotto)")
    parser.add_argument("-acc", "--accuracy", type=int, default=2, help="Decimal places for percentages (default: 2)")
    parser.add_argument("-h", action=ShortHelpAction, help="Show this short help")
    parser.add_argument("--help", action="help", help="Show full help with all options")
    args = parser.parse_args()

    if args.mostfreq is not None and args.mostfreq < 1:
        parser.error("--mostfreq must be a positive integer")

    if not args.num and not args.auto and not args.mostfreq and not args.neighbors and not args.neighborstats:
        parser.error("Specify -num N[,M,...], --auto, --mostfreq N, --neighbors, or --neighborstats")

    if args.color:
        enable_ansi()

    try:
        date_min = parse_date(args.datemin) if args.datemin else None
    except ValueError:
        sys.exit(f"Invalid --datemin format: '{args.datemin}'. Expected DD.MM.YYYY")
    try:
        date_max = parse_date(args.datemax) if args.datemax else None
    except ValueError:
        sys.exit(f"Invalid --datemax format: '{args.datemax}'. Expected DD.MM.YYYY")
    columns = parse_format(args.format)

    counts, total_draws, total_numbers = load_data(args.infile, columns, date_min, date_max)

    if total_numbers == 0:
        print("No data")
        sys.exit(1)

    if args.auto or args.mostfreq or args.num:
        print(f"Total draws: {total_draws}")

    if args.auto:
        show_histogram(counts, total_draws, total_numbers, args.color, args.accuracy, args.mostfreq)
    elif args.mostfreq:
        show_mostfreq(counts, args.mostfreq, total_draws, total_numbers, args.color, args.accuracy)
    elif args.neighbors:
        show_neighbors(args.infile, columns, date_min, date_max, args.color, args.nncolor, args.nosort)
    elif args.neighborstats:
        show_neighborstats(args.infile, columns, date_min, date_max, args.color, args.accuracy)
    else:
        for num in args.num:
            show_single(counts, num, total_draws, total_numbers, args.color, args.accuracy)


if __name__ == "__main__":
    main()
