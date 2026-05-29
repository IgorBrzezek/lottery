import argparse
import csv
import sys
from datetime import datetime

VERSION = 0.1
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


def load_data(path, columns=None, date_min=None, date_max=None):
    counts = {}
    total_draws = 0
    total_numbers = 0

    with open(path, newline="") as f:
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
                val = int(n)
                counts[val] = counts.get(val, 0) + 1

    return counts, total_draws, total_numbers


def c(text, color_index, use_color):
    if not use_color:
        return text
    return COLORS[color_index % len(COLORS)] + text + RESET


def show_single(counts, num, total_draws, total_numbers, use_color, acc):
    c_ = counts.get(num, 0)
    pct = c_ / total_numbers * 100
    num_str = c(f"{num}", 1, use_color)
    count_str = c(f"{c_}", 2, use_color)
    total_str = c(f"{total_numbers}", 3, use_color)
    draws_str = c(f"{total_draws}", 4, use_color)
    pct_str = c(f"{pct:.{acc}f}%", 1, use_color)
    print(f"Number {num_str} appears {count_str} times out of {total_str} numbers drawn ({draws_str} draws)")
    print(f"Percentage share: {pct_str}")


def show_histogram(counts, total_draws, total_numbers, use_color, acc, top_n=None):
    items = sorted(counts.items(), key=lambda x: -x[1])
    if top_n:
        items = items[:top_n]
    else:
        items = [(i, counts.get(i, 0)) for i in range(1, 50)]

    max_pct = max(c / total_numbers * 100 for _, c in items)

    for num, c_ in items:
        pct = c_ / total_numbers * 100
        bar_len = round(pct / max_pct * 40) if max_pct > 0 else 0
        bar = "#" * bar_len
        label = c(f"{num:2d}", num, use_color) if use_color else f"{num:2d}"
        pct_str = c(f"{pct:{acc+4}.{acc}f}%", num, use_color) if use_color else f"{pct:{acc+4}.{acc}f}%"
        print(f"{label} | {pct_str} {bar}")


def show_mostfreq(counts, n, total_draws, total_numbers, use_color, acc):
    sorted_items = sorted(counts.items(), key=lambda x: -x[1])[:n]
    print(f"\n  Most frequent numbers (top {n}):\n")
    for rank, (num, c_) in enumerate(sorted_items, 1):
        pct = c_ / total_numbers * 100
        bar_len = round(pct / (sorted_items[0][1] / total_numbers * 100) * 20) if c_ > 0 else 0
        bar = "#" * bar_len
        rank_s = c(f"{rank:2d}.", 0, use_color)
        num_s = c(f"{num:2d}", rank, use_color)
        count_s = c(f"{c_}", rank + 1, use_color)
        pct_s = c(f"{pct:{acc+4}.{acc}f}%", rank + 2, use_color)
        print(f"{rank_s} #{num_s}  {count_s:>4} times  {pct_s}  {bar}")


SHORT_HELP = """usage: lottery_stats.py -in FILE [-num N] [--auto] [--mostfreq N] [options]

Analyze lottery CSV data. Columns: draw_nr, date, num1..num6.

Modes (one required):
  -in FILE               Input CSV file
  -num N                 Stats for a single number
  --auto                 Histogram for numbers 1-49
  --mostfreq N           Top N most frequent numbers

Options:
  -h                     This short help
  --help                 Full help (all options)
  -acc N                 Decimal places (default: 2)
  --color                ANSI colored output
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
    parser.add_argument("-num", type=int, help="Number to analyze")
    parser.add_argument("--auto", action="store_true", help="Show percentage histogram for numbers 1-49")
    parser.add_argument("--mostfreq", type=int, metavar="N", help="Show top N most frequent numbers")
    parser.add_argument("--color", action="store_true", help="Enable ANSI colored output")
    parser.add_argument("--datemin", type=str, help="Start date (DD.MM.YYYY)")
    parser.add_argument("--datemax", type=str, help="End date (DD.MM.YYYY)")
    parser.add_argument("--format", type=str, default="lotto", help="Column format: \"lotto\" or \"cols 1,2,...\" (default: lotto)")
    parser.add_argument("-acc", "--accurancy", type=int, default=2, help="Decimal places for percentages (default: 2)")
    parser.add_argument("-h", action=ShortHelpAction, help="Show this short help")
    parser.add_argument("--help", action="help", help="Show full help with all options")
    args = parser.parse_args()

    if not args.num and not args.auto and not args.mostfreq:
        parser.error("Specify -num N, --auto, or --mostfreq N")

    if args.color:
        enable_ansi()

    date_min = parse_date(args.datemin) if args.datemin else None
    date_max = parse_date(args.datemax) if args.datemax else None
    columns = parse_format(args.format)

    counts, total_draws, total_numbers = load_data(args.infile, columns, date_min, date_max)

    if total_numbers == 0:
        print("No data")
        sys.exit(1)

    if args.auto:
        show_histogram(counts, total_draws, total_numbers, args.color, args.accurancy, args.mostfreq)
    elif args.mostfreq:
        show_mostfreq(counts, args.mostfreq, total_draws, total_numbers, args.color, args.accurancy)
    else:
        show_single(counts, args.num, total_draws, total_numbers, args.color, args.accurancy)


if __name__ == "__main__":
    main()
