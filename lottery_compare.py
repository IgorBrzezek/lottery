#!/usr/bin/env python3
import argparse
import csv
import sys

VERSION = 0.2
AUTHOR = "igor.brzezek@gmail.com"
GITHUB = "https://github.com/IgorBrzezek/lottery_compare"

try:
    import colorama
    colorama.init()
except ImportError:
    pass

GRAY = '\033[90m'
WHITE = '\033[37m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
CYAN = '\033[96m'
RED = '\033[91m'
BRIGHT_WHITE = '\033[97m'
BLUE = '\033[94m'
RESET = '\033[0m'

MATCH_COLORS = {0: GRAY, 1: BRIGHT_WHITE, 2: YELLOW, 3: GREEN, 4: CYAN, 5: RED, 6: BLUE}


class _CustomHelpAction(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS,
                 help=None, extended=False):
        super().__init__(option_strings=option_strings, dest=dest, default=default,
                         nargs=0, help=help)
        self.extended = extended

    def __call__(self, parser, namespace, values, option_string=None):
        if self.extended:
            print(f'lottery_compare.py v{VERSION} - Compare Lotto draws against tickets')
            print(f'Author: {AUTHOR}')
            print(f'GitHub: {GITHUB}')
            print()
            parser.print_help()
            print('''\

EXAMPLES:
  python lottery_compare.py -a lotto.csv -b mydata.csv
      Compare one draw against tickets in a single set.

  python lottery_compare.py --mynumbers 1,2,3,4,5,6 -b mydata.csv
      Compare given numbers against tickets in a single set.

  python lottery_compare.py -a lotto.csv -b mydata.csv --setb all --stat
      Compare against all ticket sets and show per-set statistics.

  python lottery_compare.py -a lotto.csv -b lotto2.csv --setb 2,3 --rownumbers
      Compare against sets 2 and 3, showing row numbers for tickets.

  python lottery_compare.py -a lotto.csv -b mydata.csv --mono
      Plain ASCII output without ANSI color codes.

  python lottery_compare.py -a lotto.csv -b mydata.csv --summaryonly
      Skip per-set display, show only the combined overall hits summary.

  python lottery_compare.py -a result1000_a.csv -b mydata.csv --ppcolor
      Color the "SET" label and set number in multi-set separators.

  python lottery_compare.py -a lotto.csv -b mydata.csv --showdata
      Show full data rows from file B with their line numbers.

  python lottery_compare.py -a lotto.csv -b mydata.csv --summary
      Show the number of data lines (non-empty, non-comment) in both files.

  python lottery_compare.py -a result1000_a.csv -b mydata.csv --colsa 3-8
      Use only columns 3-8 from file A as the drawn numbers.

  python lottery_compare.py -a lotto.csv -b result1000_a.csv --colsb 2-7
      Use only columns 2-7 from file B as ticket numbers.

  python lottery_compare.py -a result1000_a.csv -b mydata.csv --displcolsa 1-6
      Display only columns 1-6 from file A (calculation still uses all columns).

  python lottery_compare.py -a lotto.csv -b result1000_a.csv --colsb 2-7 --displaycolsb 1,3,5,7
      Calculate using columns 2-7 from file B, display only columns 1,3,5,7.

FILE FORMAT:
  File A (--a):
    CSV file. Use --seta to select which row to analyze.
    All columns are treated as drawn numbers, or use --colsa to
    select specific columns (1-based).

  File B (--b):
    CSV file with ticket rows. Empty rows separate different ticket sets.
    Each non-empty row must have a ticket ID as the first column,
    followed by the ticket numbers.  Use --colsb to select specific
    columns (all selected columns are matchable numbers).  Columns not
    selected by --colsb (e.g. dates, text) are safely ignored.
    Use --displaycolsb to show any column regardless of type.

COLOR LEGEND (--mono disables all colors):
  0 hits: gray (dim)      1 hit:  bright white     2 hits: yellow
  3 hits: green           4 hits: cyan             5 hits: red
  6 hits: blue

NOTES:
  - Use --mono if colors are garbled or invisible on your terminal.
  - On Windows, install 'colorama' (pip install colorama) for proper
    ANSI color support in legacy console windows.
  - Rows with 0 matches appear in gray by default.
  - Combine --setb all with --summaryonly for a quick multi-set overview.
  - --colsa / --colsb and --displcolsa / --displaycolsb accept 1-based column
    numbers, comma-separated (e.g. "3,4,5,6,7,8"), ranges (e.g. "3-8"), or "all".
  - --colsa filters which columns of the draw file are used for matching.
  - --colsb filters which columns of the ticket file are used; all selected
    columns are matchable numbers (no ID treatment).
  - --displcolsa controls which columns of file A are displayed (does not
    affect matching).
  - --displaycolsb controls which columns of file B are displayed (does not
    affect matching).
  - Non-numeric columns (dates, text) are safe with --colsb / --displaycolsb:
    only the numeric columns selected by --colsb are parsed for matching;
    --displaycolsb shows non-numeric values as-is in gray.
''')
        else:
            print(f'lottery_compare.py v{VERSION}')
            print(f'Author: {AUTHOR}')
            print()
            print('Usage: lottery_compare.py (-a FILE | --mynumbers NUMBERS) -b FILE [--seta SETA] [--setb LIST] [--stat] [--mono] [--ppcolor] [--rownumbers] [--summaryonly] [--showdata] [--summary] [--colsa COLS] [--colsb COLS] [--displcolsa COLS] [--displaycolsb COLS]')
            print()
            print('Use --help for extended help with examples.')
        parser.exit()


def parse_setb(s):
    if s == 'all':
        return s
    parts = [x.strip() for x in s.split(',')]
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            raise argparse.ArgumentTypeError(f'invalid set number: {p}')
    return result


def parse_cols(s):
    if s is None or s.strip().lower() == 'all':
        return None
    parts = []
    for token in s.split(','):
        token = token.strip()
        if '-' in token:
            a, b = token.split('-', 1)
            parts.extend(range(int(a.strip()) - 1, int(b.strip())))
        else:
            parts.append(int(token) - 1)
    return parts


def main():
    parser = argparse.ArgumentParser(
        description='Compare a lottery draw against ticket sets',
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('-h', action=_CustomHelpAction, extended=False,
                        help='show this simple help message and exit')
    parser.add_argument('--help', action=_CustomHelpAction, extended=True,
                        help='show extended help message with examples and exit')
    parser.add_argument('-a', required=False, help='file with drawn numbers (CSV)')
    parser.add_argument('--mynumbers', type=str, help='comma-separated numbers to check (alternative to -a)')
    parser.add_argument('-b', required=True, help='file with ticket numbers; empty line = new set (CSV)')
    parser.add_argument('--seta', type=int, default=1, help='row in -a to analyze (1-based, default: 1)')
    parser.add_argument('--setb', type=parse_setb, default=[1], help='set(s) in -b: comma-separated numbers or "all" (default: 1)')
    parser.add_argument('--stat', action='store_true', help='show per-set hit statistics')
    parser.add_argument('--mono', action='store_true', help='plain ASCII output, no ANSI colors')
    parser.add_argument('--ppcolor', action='store_true', help='color the SET labels in multi-set separators')
    parser.add_argument('--rownumbers', action='store_true', help='show row numbers in ticket display')
    parser.add_argument('--summaryonly', action='store_true', help='show only the overall hits summary (skip per-set display)')
    parser.add_argument('--showdata', action='store_true', help='show full data rows with line numbers from file B')
    parser.add_argument('--colsa', type=str, help='columns from file A to use (1-based, comma-separated, e.g. "1,2,3" or "1-6")')
    parser.add_argument('--colsb', type=str, help='columns from file B to use (1-based, comma-separated, e.g. "2-7" or "all")')
    parser.add_argument('--displcolsa', type=str, help='columns from file A to display only (1-based, comma-separated, e.g. "1,2,3" or "1-6")')
    parser.add_argument('--displaycolsb', type=str, help='columns from file B to display only (1-based, comma-separated, e.g. "2-7" or "all")')
    parser.add_argument('--summary', action='store_true', help='show data line counts for both input files')
    args = parser.parse_args()
    if args.a is None and args.mynumbers is None:
        sys.exit("Either -a or --mynumbers must be provided")
    if args.a is not None and args.mynumbers is not None:
        sys.exit("-a and --mynumbers are mutually exclusive")

    G = '' if args.mono else GRAY
    W = '' if args.mono else WHITE
    Y = '' if args.mono else YELLOW
    G2 = '' if args.mono else GREEN
    C = '' if args.mono else CYAN
    R = '' if args.mono else RED
    BW = '' if args.mono else BRIGHT_WHITE
    B = '' if args.mono else BLUE
    X = '' if args.mono else RESET
    MC = {0: G, 1: BW, 2: Y, 3: G2, 4: C, 5: R, 6: B}

    colsa = parse_cols(args.colsa)
    colsb = parse_cols(args.colsb)
    displcolsa = parse_cols(args.displcolsa)
    displaycolsb = parse_cols(args.displaycolsb)

    if args.mynumbers is not None:
        try:
            ref = [int(x.strip()) for x in args.mynumbers.split(',')]
        except ValueError:
            sys.exit("Non-numeric value in --mynumbers")
        ref_set = set(ref)
        displ_ref = ref
    else:
        with open(args.a, encoding="utf-8") as f:
            reader = csv.reader(f)
            count = 0
            ref_row = None
            for row in reader:
                if not row or row[0].lstrip().startswith('#'):
                    continue
                count += 1
                if count == args.seta:
                    ref_row = row
                    break
            if ref_row is None:
                sys.exit(f"File {args.a} has fewer than {args.seta} data row(s)")
            if colsa:
                try:
                    ref = [int(ref_row[i].strip()) for i in colsa if i < len(ref_row)]
                except ValueError:
                    sys.exit(f"Non-numeric value in file A row {args.seta}, selected column(s)")
            else:
                try:
                    ref = [int(x.strip()) for x in ref_row]
                except ValueError:
                    sys.exit(f"Non-numeric value in file A row {args.seta}")

        ref_set = set(ref)
        if displcolsa:
            displ_ref = []
            for i in displcolsa:
                if i < len(ref_row):
                    v = ref_row[i].strip()
                    try:
                        displ_ref.append(int(v))
                    except ValueError:
                        displ_ref.append(v)
        else:
            displ_ref = ref
    left = ' '.join(f'{n:3d}' if isinstance(n, int) else n for n in displ_ref)
    left_width = len(left)

    sets = {}
    cur_set = 1
    prev_empty = False
    seen_data = False
    line_idx = 0
    with open(args.b, encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row:
                if not prev_empty and seen_data:
                    cur_set += 1
                prev_empty = True
                continue
            prev_empty = False
            if row[0].lstrip().startswith('#'):
                continue
            seen_data = True
            line_idx += 1
            full_row = tuple(row)
            if colsb:
                try:
                    nums = tuple(int(full_row[i].strip()) for i in colsb if i < len(full_row))
                except ValueError:
                    continue
                sets.setdefault(cur_set, []).append((line_idx, line_idx, nums, nums, full_row))
            else:
                try:
                    nums = tuple(int(x.strip()) for x in row)
                except ValueError:
                    continue
                sets.setdefault(cur_set, []).append((line_idx, nums[0], nums[1:], nums, full_row))

    sep_width = left_width + 2
    max_row_num_len = 0
    if args.rownumbers:
        for set_rows in sets.values():
            for line_idx, row_num, nums, show_vals, full_row in set_rows:
                for n in (row_num, line_idx):
                    rl = len(str(n))
                    if rl > max_row_num_len:
                        max_row_num_len = rl
    for set_rows in sets.values():
        for line_idx, row_num, nums, show_vals, full_row in set_rows:
            if args.showdata:
                if displaycolsb:
                    dv = [full_row[i].strip() for i in displaycolsb if i < len(full_row)]
                    parts = []
                    for v in dv:
                        try:
                            parts.append(f'{int(v):3d}')
                        except ValueError:
                            parts.append(v)
                    right_plain = (f'{line_idx:>{max_row_num_len}}: ' if args.rownumbers else '') + ', '.join(parts)
                else:
                    dv = [full_row[i].strip() for i in range(len(full_row))]
                    parts = []
                    for v in dv:
                        try:
                            parts.append(f'{int(v):3d}')
                        except ValueError:
                            parts.append(v)
                    right_plain = (f'{line_idx:>{max_row_num_len}}: ' if args.rownumbers else '') + ', '.join(parts)
            else:
                prefix = f'{row_num:>{max_row_num_len}}: ' if args.rownumbers else ''
                if displaycolsb:
                    dn = [full_row[i].strip() for i in displaycolsb if i < len(full_row)]
                    parts = []
                    for v in dn:
                        try:
                            parts.append(f'{int(v):3d}')
                        except ValueError:
                            parts.append(v)
                    right_plain = prefix + ' '.join(parts)
                else:
                    right_plain = prefix + ' '.join(f'{n:3d}' for n in nums)
            w = left_width + 2 + len(right_plain)
            if w > sep_width:
                sep_width = w

    selected = args.setb
    if selected == 'all':
        sets_to_show = sorted(sets.keys())
        show_stats = True
    else:
        sets_to_show = selected
        show_stats = args.stat

    total_stats = [0] * (len(ref) + 1)

    h1 = 'Draw'
    h2 = 'Data from B' if args.showdata else 'Tickets'
    right_width = max(sep_width - left_width - 2, 6 * 3 + 5)
    line = f'{h1:^{left_width}}  {h2:^{right_width}}'

    for s_idx, s in enumerate(sets_to_show):
        if s not in sets:
            if not args.summaryonly:
                print(f'Set {s} not found in {args.b}')
            continue

        if not args.summaryonly or args.showdata:
            if s_idx > 0:
                print()

            if len(sets_to_show) > 1:
                plain_label = f'SET {s}'
                plain_prefix = f'=== {plain_label} '
                pad = '=' * (sep_width - 1 - len(plain_prefix))
                if args.ppcolor:
                    top = f'=== {Y}SET{X} {C}{s}{X} {pad}'
                else:
                    top = f'{plain_prefix}{pad}'
                print(top)

            print(line)
            print('-' * sep_width)

            first = True
            for line_idx, row_num, nums, show_vals, full_row in sets[s]:
                matches = sum(1 for n in nums if n in ref_set)
                if args.summaryonly and args.showdata and matches == 0:
                    continue
                c = MC.get(matches, G)
                if displaycolsb:
                    display_vals = [full_row[i].strip() for i in displaycolsb if i < len(full_row)]
                    parts = []
                    for v in display_vals:
                        try:
                            n = int(v)
                            if n in ref_set:
                                parts.append(f'{c}{n:3d}{X}')
                            else:
                                parts.append(f'{G}{n:3d}{X}')
                        except ValueError:
                            parts.append(f'{G}{v}{X}')
                    right_numbers = ' '.join(parts)
                else:
                    parts = []
                    for n in nums:
                        if n in ref_set:
                            parts.append(f'{c}{n:3d}{X}')
                        else:
                            parts.append(f'{G}{n:3d}{X}')
                    right_numbers = ' '.join(parts)
                if args.showdata:
                    if displaycolsb:
                        disp_vals = [full_row[i].strip() for i in displaycolsb if i < len(full_row)]
                        colored_parts = []
                        for v in disp_vals:
                            try:
                                n = int(v)
                                clr = c if n in ref_set else G
                                colored_parts.append(f'{clr}{n:3d}{X}')
                            except ValueError:
                                colored_parts.append(f'{G}{v}{X}')
                        right = (f'{line_idx:>{max_row_num_len}}: ' if args.rownumbers else '') + ', '.join(colored_parts)
                    else:
                        dv = [full_row[i].strip() for i in range(len(full_row))]
                        colored_parts = []
                        for v in dv:
                            try:
                                n = int(v)
                                clr = c if n in ref_set else G
                                colored_parts.append(f'{clr}{n:3d}{X}')
                            except ValueError:
                                colored_parts.append(f'{G}{v}{X}')
                        right = (f'{line_idx:>{max_row_num_len}}: ' if args.rownumbers else '') + ', '.join(colored_parts)
                elif args.rownumbers:
                    right = f'{row_num:>{max_row_num_len}}: {right_numbers}'
                else:
                    right = right_numbers
                if first:
                    print(f'{left}  {right}')
                    first = False
                else:
                    print(f'{" " * left_width}  {right}')

            print('-' * sep_width)

            if show_stats and not args.summaryonly:
                stats = [0] * (len(ref) + 1)
                for line_idx, row_num, nums, show_vals, full_row in sets[s]:
                    stats[sum(1 for n in nums if n in ref_set)] += 1
                print()
                for m in range(1, len(ref) + 1):
                    c = MC.get(m, G)
                    print(f'{c}Hits: {m} -- {stats[m]}{X}')

            if len(sets_to_show) > 1:
                print('=' * sep_width)

        for line_idx, row_num, nums, show_vals, full_row in sets[s]:
            total_stats[sum(1 for n in nums if n in ref_set)] += 1

    if len(sets_to_show) > 1 or args.summaryonly or args.summary:
        if not args.summaryonly:
            print()
        print(f'{"Overall Hits":^{sep_width}}')
        print('=' * sep_width)
        for m in range(1, len(ref) + 1):
            c = MC.get(m, G)
            print(f'{c}Hits: {m} -- {total_stats[m]}{X}')
        print('=' * sep_width)

    if args.summary:
        if args.a:
            count_a = 0
            try:
                with open(args.a, encoding="utf-8") as f:
                    count_a = sum(1 for row in csv.reader(f) if row)
            except FileNotFoundError:
                sys.exit(f"File not found: {args.a}")
        try:
            with open(args.b, encoding="utf-8") as f:
                count_b = sum(
                    1 for row in csv.reader(f)
                    if row and not row[0].lstrip().startswith('#')
                )
        except FileNotFoundError:
            sys.exit(f"File not found: {args.b}")
        if args.a:
            print(f'File "{args.a}": {count_a} data line(s)')
        print(f'File "{args.b}": {count_b} data line(s)')


if __name__ == '__main__':
    main()
