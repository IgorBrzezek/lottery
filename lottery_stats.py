import argparse
import csv
import sys
from datetime import datetime

VERSION = 0.7
AUTHOR = "igor.brzezek@gmail.com"
GITHUB = "https://github.com/IgorBrzezek/lottery_stats"

HEADER = f"lottery_stats.py {VERSION} by {AUTHOR}\n{GITHUB}"

RESET = "\033[0m"
BOLD = "\033[1m"
COLORS = ["\033[31m", "\033[32m", "\033[33m", "\033[34m", "\033[35m", "\033[36m"]

MAX_CONSECUTIVE = 6


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


class OpStats:
    def __init__(self):
        self.total_rows = 0
        self.skipped_rows = 0
        self.analyzed_rows = 0
        self.matched_rows = 0
        self.printed_rows = 0


def iter_rows(path, columns, date_min, date_max, stats):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            stats.total_rows += 1
            if columns is not None:
                if any(i >= len(row) for i in columns):
                    stats.skipped_rows += 1
                    continue
                numbers = [row[i] for i in columns]
                prefix = ""
            else:
                if len(row) < 3:
                    stats.skipped_rows += 1
                    continue
                date_str = row[1].strip()
                if date_min and parse_date(date_str) < date_min:
                    stats.skipped_rows += 1
                    continue
                if date_max and parse_date(date_str) > date_max:
                    stats.skipped_rows += 1
                    continue
                numbers = row[2:]
                prefix = f"{row[0]} {row[1]}:"
            stats.analyzed_rows += 1
            yield prefix, numbers


def load_data(path, columns=None, date_min=None, date_max=None, stats=None):
    stats = stats if stats is not None else OpStats()
    counts = {}
    draw_hits = {}
    total_draws = 0
    total_numbers = 0

    for prefix, numbers in iter_rows(path, columns, date_min, date_max, stats):
        total_draws += 1
        seen = set()
        for n in numbers:
            total_numbers += 1
            try:
                val = int(n)
            except ValueError:
                continue
            counts[val] = counts.get(val, 0) + 1
            seen.add(val)
        for val in seen:
            draw_hits[val] = draw_hits.get(val, 0) + 1

    return counts, draw_hits, total_draws, total_numbers


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

    return len(items)


def neighbor_ints_of(sorted_ints):
    neighbor_ints = set()
    for i in range(len(sorted_ints) - 1):
        if sorted_ints[i + 1] - sorted_ints[i] == 1:
            neighbor_ints.add(sorted_ints[i])
            neighbor_ints.add(sorted_ints[i + 1])
    return neighbor_ints


def show_neighbor_rows(path, columns, date_min, date_max, use_color, nncolor=False, nosort=False, stats=None, want=None):
    stats = stats if stats is not None else OpStats()
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    shown = 0
    for prefix, numbers in iter_rows(path, columns, date_min, date_max, stats):
        int_nums = [int(n) for n in numbers]
        sorted_ints = sorted(int_nums)
        display = int_nums if nosort else sorted_ints

        neighbor_ints = neighbor_ints_of(sorted_ints)

        if want is None:
            if neighbor_ints:
                stats.matched_rows += 1
        elif len(neighbor_ints) == want:
            stats.matched_rows += 1
        else:
            continue

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
        shown += 1
        stats.printed_rows += 1
        if prefix:
            print(f"{prefix} {line}")
        else:
            print(line)

    if want is not None and shown == 0:
        print(f"No rows with exactly {want} consecutive number(s) found")


def show_notneighbors(path, columns, date_min, date_max, use_color, nncolor=False, nosort=False, stats=None):
    stats = stats if stats is not None else OpStats()
    YELLOW = "\033[33m"
    shown = 0
    for prefix, numbers in iter_rows(path, columns, date_min, date_max, stats):
        int_nums = [int(n) for n in numbers]
        sorted_ints = sorted(int_nums)
        display = int_nums if nosort else sorted_ints

        has_neighbor = False
        for i in range(len(sorted_ints) - 1):
            if sorted_ints[i + 1] - sorted_ints[i] == 1:
                has_neighbor = True
                break

        if has_neighbor:
            continue

        stats.matched_rows += 1

        parts = []
        for n in display:
            parts.append(YELLOW + str(n) + RESET if nncolor else str(n))
        line = ", ".join(parts)
        shown += 1
        stats.printed_rows += 1
        if prefix:
            print(f"{prefix} {line}")
        else:
            print(line)

    if shown == 0:
        print("No rows without consecutive numbers found")


def show_pairstats(path, columns, date_min, date_max, use_color, acc, stats=None):
    stats = stats if stats is not None else OpStats()
    pair_counts = {}

    for prefix, numbers in iter_rows(path, columns, date_min, date_max, stats):
        ints = sorted(int(n) for n in numbers)
        row_has_neighbor = False
        for i in range(len(ints) - 1):
            if ints[i + 1] - ints[i] == 1:
                row_has_neighbor = True
                pair = (ints[i], ints[i + 1])
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
        if row_has_neighbor:
            stats.matched_rows += 1

    if not pair_counts:
        print("No consecutive pairs found")
        return 0

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

    return len(sorted_pairs)


def count_consecutive_rows(path, columns, date_min, date_max, stats):
    stats = stats if stats is not None else OpStats()
    counts = dict.fromkeys(range(2, MAX_CONSECUTIVE + 1), 0)
    more = 0

    for prefix, numbers in iter_rows(path, columns, date_min, date_max, stats):
        cnt = len(neighbor_ints_of(sorted(int(n) for n in numbers)))
        if cnt < 2:
            continue
        stats.matched_rows += 1
        if cnt <= MAX_CONSECUTIVE:
            counts[cnt] += 1
        else:
            more += 1

    return counts, more


def show_neighborstats(counts, more, total_rows, use_color, acc):
    items = [("All rows", total_rows)]
    items += [(f"{n} consecutive numbers", counts[n]) for n in range(2, MAX_CONSECUTIVE + 1)]
    if more:
        items.append((f">{MAX_CONSECUTIVE} consecutive numbers", more))

    print(f"\n  Rows by number of consecutive numbers:\n")
    max_pct = max(count / total_rows * 100 for _, count in items) if total_rows else 0
    for rank, (label, count) in enumerate(items):
        pct = count / total_rows * 100 if total_rows else 0
        bar_len = round(pct / max_pct * 40) if max_pct > 0 else 0
        bar = "#" * bar_len
        pct_str = c(f"{pct:{acc+4}.{acc}f}%", rank, use_color)
        count_str = c(f"{count:>7}", rank + 1, use_color)
        print(f"{pct_str} {bar:<40} {label:<24}{count_str}")
    print(f"\n  Consecutive numbers are drawn values differing by 1; "
          f"rows with fewer than 2 are listed under 'All rows' only.")


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

    return len(sorted_items)


def file_row_stats(stats):
    return [
        ("Rows in file", stats.total_rows, None, ""),
        ("Rows skipped", stats.skipped_rows, stats.total_rows, "all rows"),
        ("Rows analyzed", stats.analyzed_rows, None, ""),
    ]


def show_opstats(use_color, acc, title, entries):
    width = max(len(label) for label, _, _, _ in entries)
    print(f"\n  {title}\n")
    for rank, (label, count, base, base_label) in enumerate(entries):
        value_str = c(f"{count:>8}", rank + 1, use_color)
        pct_str = ""
        if base:
            pct_str = c(f" ({count / base * 100:.{acc}f}% of {base} {base_label})", rank + 2, use_color)
        print(f"  {label}:{' ' * (width - len(label))} {value_str}{pct_str}")


SHORT_HELP = f"""{HEADER}

usage: lottery_stats.py -in FILE [-num N] [--auto] [--mostfreq N] [--neighbors] [options]

Analyze lottery CSV data. Columns: draw_nr, date, num1..num6.

Modes (one required):
  -in FILE               Input CSV file
  -num N[,M,...]         Stats for one or more numbers (comma-separated)
  --auto                 Histogram for numbers 1-49
  --mostfreq N           Top N most frequent numbers
  --neighbors            Show rows with consecutive numbers
  --notneighbors         Show rows without consecutive numbers
  --neighbor2            Show rows with exactly 2 consecutive numbers
  --neighbor3            Show rows with exactly 3 consecutive numbers
  --neighbor4            Show rows with exactly 4 consecutive numbers
  --neighborstats        Histogram of rows by number of consecutive numbers
  --pairstats            Statistics for consecutive number pairs

Options:
  -h                     This short help
  --help                 Full help (all options)
  -acc N                 Decimal places (default: 2)
  --stats                Summary of the performed operation (rows, matches, %)
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
        description=HEADER + "\n\nAnalyze lottery draw statistics from a CSV file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("-in", dest="infile", required=True, help="Input CSV file with lottery results")
    parser.add_argument("-num", type=parse_num_list, help="Number(s) to analyze (comma-separated: N[,M,...])")
    parser.add_argument("--auto", action="store_true", help="Show percentage histogram for numbers 1-49")
    parser.add_argument("--mostfreq", type=int, metavar="N", help="Show top N most frequent numbers")
    parser.add_argument("--neighbors", action="store_true", help="Show rows with consecutive numbers (neighbors)")
    parser.add_argument("--notneighbors", action="store_true", help="Show only rows without consecutive numbers")
    parser.add_argument("--neighbor2", dest="neighborn", action="store_const", const=2, help="Show only rows with exactly 2 consecutive numbers")
    parser.add_argument("--neighbor3", dest="neighborn", action="store_const", const=3, help="Show only rows with exactly 3 consecutive numbers")
    parser.add_argument("--neighbor4", dest="neighborn", action="store_const", const=4, help="Show only rows with exactly 4 consecutive numbers")
    parser.add_argument("--neighborstats", action="store_true", help="Histogram of rows by the number of consecutive numbers (2-6)")
    parser.add_argument("--pairstats", action="store_true", help="Statistics for most frequent consecutive number pairs")
    parser.add_argument("--nncolor", action="store_true", help="Highlight rows without neighbors in yellow")
    parser.add_argument("--stats", action="store_true", help="Show summary of the performed operation (rows read, rows matching the condition, percentage share)")
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

    if not args.num and not args.auto and not args.mostfreq and not args.neighbors and not args.notneighbors and not args.neighborn and not args.neighborstats and not args.pairstats:
        parser.error("Specify -num N[,M,...], --auto, --mostfreq N, --neighbors, --notneighbors, --neighbor2/3/4, --neighborstats, or --pairstats")

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

    stats = OpStats()
    counts, draw_hits, total_draws, total_numbers = load_data(args.infile, columns, date_min, date_max, stats)

    if total_numbers == 0:
        print("No data")
        sys.exit(1)

    if args.auto or args.mostfreq or args.num:
        print(f"Total draws: {total_draws}")

    if args.auto:
        shown = show_histogram(counts, total_draws, total_numbers, args.color, args.accuracy, args.mostfreq)
        entries = [("Numbers displayed", shown, None, "")]
        mode_label = "--auto"
    elif args.mostfreq:
        shown = show_mostfreq(counts, args.mostfreq, total_draws, total_numbers, args.color, args.accuracy)
        entries = [("Numbers displayed", shown, None, "")]
        mode_label = "--mostfreq"
    elif args.neighbors:
        stats = OpStats()
        show_neighbor_rows(args.infile, columns, date_min, date_max, args.color, args.nncolor, args.nosort, stats)
        entries = [("Rows with neighbors", stats.matched_rows, stats.analyzed_rows, "analyzed rows")]
        entries.append(("Rows displayed", stats.printed_rows, stats.analyzed_rows, "analyzed rows"))
        mode_label = "--neighbors"
    elif args.neighborn:
        stats = OpStats()
        show_neighbor_rows(args.infile, columns, date_min, date_max, args.color, args.nncolor, args.nosort, stats, args.neighborn)
        entries = [(f"Rows with exactly {args.neighborn} consecutive numbers", stats.matched_rows, stats.analyzed_rows, "analyzed rows")]
        entries.append(("Rows displayed", stats.printed_rows, stats.analyzed_rows, "analyzed rows"))
        mode_label = f"--neighbor{args.neighborn}"
    elif args.notneighbors:
        stats = OpStats()
        show_notneighbors(args.infile, columns, date_min, date_max, args.color, args.nncolor, args.nosort, stats)
        entries = [("Rows without neighbors", stats.matched_rows, stats.analyzed_rows, "analyzed rows")]
        entries.append(("Rows displayed", stats.printed_rows, stats.analyzed_rows, "analyzed rows"))
        mode_label = "--notneighbors"
    elif args.neighborstats:
        stats = OpStats()
        counts_n, more = count_consecutive_rows(args.infile, columns, date_min, date_max, stats)
        show_neighborstats(counts_n, more, stats.analyzed_rows, args.color, args.accuracy)
        entries = [("Rows with neighbors", stats.matched_rows, stats.analyzed_rows, "analyzed rows")]
        mode_label = "--neighborstats"
    elif args.pairstats:
        stats = OpStats()
        pairs = show_pairstats(args.infile, columns, date_min, date_max, args.color, args.accuracy, stats)
        entries = [("Rows with neighbors", stats.matched_rows, stats.analyzed_rows, "analyzed rows")]
        entries.append(("Distinct pairs found", pairs, None, ""))
        mode_label = "--pairstats"
    else:
        for num in args.num:
            show_single(counts, num, total_draws, total_numbers, args.color, args.accuracy)
        entries = [(f"Rows with number {num}", draw_hits.get(num, 0), total_draws, "analyzed rows") for num in args.num]
        mode_label = "-num"

    if args.stats:
        show_opstats(args.color, args.accuracy, f"Operation statistics ({mode_label})", file_row_stats(stats) + entries)


if __name__ == "__main__":
    main()
