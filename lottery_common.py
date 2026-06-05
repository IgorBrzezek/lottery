import argparse
import csv
import sys
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations

VERSION = 0.1
AUTHOR = "igor.brzezek@gmail.com"
GITHUB = "https://github.com/IgorBrzezek/lottery_common"

try:
    import colorama
    colorama.init()
except ImportError:
    if os.name == 'nt':
        os.system('color')

try:
    import msvcrt
except ImportError:
    msvcrt = None


def parse_cols(s):
    if s is None:
        return None
    parts = []
    for token in s.split(','):
        token = token.strip()
        if '-' in token:
            try:
                a, b = token.split('-', 1)
                start, end = int(a.strip()), int(b.strip())
                parts.extend(range(start, end + 1))
            except ValueError:
                sys.exit(f"Invalid column range: {token}")
        else:
            try:
                parts.append(int(token))
            except ValueError:
                sys.exit(f"Invalid column: {token}")
    return parts


def RED(s, color):
    return f'\033[91m{s}\033[0m' if color else s


def fmt_row(row, wspolne, color):
    return ' '.join(RED(e, color) if e in wspolne else e for e in row)


def szukaj(args):
    row_a, rows_a_disp, idx_a, rows_b, rows_b_disp, color, all_match = args
    zbior_a = set(row_a)
    wyniki = []
    for idx_b, row_b in enumerate(rows_b, 1):
        wspolne = zbior_a & set(row_b)
        if wspolne and (not all_match or wspolne == zbior_a):
            wyniki.append((idx_a, rows_a_disp[idx_a - 1], idx_b, rows_b_disp[idx_b - 1], wspolne))
    return wyniki


def show_compact_help(parser):
    print('=== LOTTERY COMMON v{} ==='.format(VERSION))
    print('Usage: lottery_common.py [OPTIONS]')
    print()
    print('Options:')
    print('  -h                    Show this compact help')
    print('  --help                Show detailed help')
    print('  -ina FILE             Input file A')
    print('  --searchnumbers, -sn NUMS  Search by numbers (comma/range-separated)')
    print('  -sf, --searchfreq N   Search by k-number frequency')
    print('  -inb FILE             Input file B (required)')
    print('  -colsa COLS           Columns for file A (comma/range-separated)')
    print('  -colsb COLS           Columns for file B (comma/range-separated)')
    print('  --color               Enable ANSI color output')
    print('  --lotto               Shorthand for --colsb 3,4,5,6,7,8')
    print('  --displaycola COLS    Columns from file A to display')
    print('  --displaycolb COLS    Columns from file B to display')
    print('  --searchm MODE        Search mode: all | one (default: all)')
    print('  --sort ORDER          Sort order for -sf: asc | desc (default: asc)')
    print('  --top N               Limit -sf results (0 = all, default: 0)')
    print('  -w FILE               Write output to file')
    print('  -t N                  Number of worker threads (default: 1)')
    print('  --pause               Pause after each screenful (Windows only)')
    print('  --from YEAR           Start year (filters by date in col 2)')
    print('  --to YEAR             End year (filters by date in col 2)')


def show_rich_help(parser):
    print('=== LOTTERY COMMON v{} ==='.format(VERSION))
    print('Author: {}'.format(AUTHOR))
    print('GitHub: {}'.format(GITHUB))
    print()
    print('DESCRIPTION')
    print('  Finds common numbers between two CSV files. Supports searching by')
    print('  specific numbers or by frequency of k-number combinations.')
    print()
    print('USAGE')
    print('  lottery_common.py -ina FILE_A -inb FILE_B [OPTIONS]')
    print('  lottery_common.py -sn NUMS -inb FILE_B [OPTIONS]')
    print('  lottery_common.py -sf N -inb FILE_B [OPTIONS]')
    print()
    print('REQUIRED ARGUMENTS')
    print('  One of -ina, --searchnumbers (-sn), or -sf (--searchfreq) must be provided.')
    print('  -inb FILE             Input CSV file B (always required).')
    print()
    print('SEARCH MODES (mutually exclusive, one required)')
    print('  -ina FILE             Read search numbers from column(s) in CSV file A.')
    print('                        Each row in file A is compared against every row in')
    print('                        file B. Matching rows (with at least one common number)')
    print('                        are printed side by side.')
    print()
    print('  --searchnumbers NUMS, -sn NUMS')
    print('                        Search by literal numbers instead of file A. Provide')
    print('                        numbers as a comma-separated list (e.g. 1,5,12) or')
    print('                        ranges (e.g. 1-10). With --searchm all, only rows that')
    print('                        contain ALL given numbers are shown; with --searchm one,')
    print('                        rows with ANY of the numbers match.')
    print()
    print('  -sf N, --searchfreq N')
    print('                        Search by frequency of N-number combinations across all')
    print('                        rows in file B. Finds and counts every unique combination')
    print('                        of N numbers appearing in the specified columns. Results')
    print('                        are sorted by frequency (use --sort asc/desc, default asc).')
    print('                        Use --top to limit the number of results shown.')
    print()
    print('COLUMN OPTIONS')
    print('  -colsa COLS           Columns in file A to use for number comparison.')
    print('                        Format: comma/range-separated, 1-indexed.')
    print('                        Example: 1,2,3 or 1-5 or 1,3-5,7')
    print()
    print('  -colsb COLS           Columns in file B to use for number comparison.')
    print('                        Same format as -colsa.')
    print()
    print('  --displaycola COLS    Columns from file A to display in output.')
    print('                        Defaults to -colsa if not specified.')
    print()
    print('  --displaycolb COLS    Columns from file B to display in output.')
    print('                        Defaults to -colsb if not specified.')
    print()
    print('  --lotto               Shorthand for --colsb 3,4,5,6,7,8.')
    print('                        Convenience option for Lotto CSV files where the draw')
    print('                        numbers are in columns 3 through 8.')
    print()
    print('OUTPUT OPTIONS')
    print('  --color               Enable ANSI color output. Common numbers between rows')
    print('                        are highlighted in red.')
    print()
    print('  -w FILE               Redirect all output to the specified file.')
    print()
    print('  --pause               Pause after each screenful of output (Windows only).')
    print('                        Requires the msvcrt module. Press any key to continue,')
    print('                        ESC to exit.')
    print()
    print('FILTER OPTIONS')
    print('  --from YEAR           Only process rows from file B where the year')
    print('                        (extracted from column 2) is >= YEAR.')
    print()
    print('  --to YEAR             Only process rows from file B where the year')
    print('                        (extracted from column 2) is <= YEAR.')
    print()
    print('PERFORMANCE OPTIONS')
    print('  -t N                  Number of worker threads for parallel processing.')
    print('                        Default: 1 (single-threaded). Use more threads for')
    print('                        large files to speed up comparison.')
    print()
    print('  --searchm MODE        Search mode for --searchnumbers.')
    print('                        all - row must contain ALL specified numbers (default)')
    print('                        one - row must contain ANY of the specified numbers')
    print()
    print('  --sort ORDER          Sort order for -sf (--searchfreq) results.')
    print('                        asc - ascending (rarest first, default)')
    print('                        desc - descending (most frequent first)')
    print()
    print('  --top N               Limit the number of results shown by -sf.')
    print('                        0 = show all results (default).')


class _CompactHelpAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        show_compact_help(parser)
        sys.exit(0)


class _RichHelpAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        show_rich_help(parser)
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(add_help=False, description='Finds common numbers between CSV files')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-ina')
    group.add_argument('--searchnumbers', '-sn')
    group.add_argument('-sf', '--searchfreq', type=int)
    parser.add_argument('-inb', required=True)
    parser.add_argument('-colsa')
    parser.add_argument('-colsb')
    parser.add_argument('--color', action='store_true', help='ANSI color output')
    parser.add_argument('--lotto', action='store_true', help='Shorthand for --colsb 3,4,5,6,7,8')
    parser.add_argument('--displaycola', help='Columns from file A to display')
    parser.add_argument('--displaycolb', help='Columns from file B to display')
    parser.add_argument('--searchm', choices=['all', 'one'], default='all', help='Search mode for --searchnumbers')
    parser.add_argument('--sort', choices=['asc', 'desc'], default='asc', help='Sort order for -sf results')
    parser.add_argument('--top', type=int, default=0, help='Limit -sf results (0 = all)')
    parser.add_argument('-w', help='Write output to file')
    parser.add_argument('-t', type=int, default=1, help='Number of worker threads')
    parser.add_argument('--pause', action='store_true', help='Pause after each screenful (Windows only)')
    parser.add_argument('--from', type=int, dest='from_', help='Start year (filters by date in col 2)')
    parser.add_argument('--to', type=int, dest='to_', help='End year (filters by date in col 2)')
    parser.add_argument('-h', action=_CompactHelpAction, nargs=0, help=argparse.SUPPRESS)
    parser.add_argument('--help', action=_RichHelpAction, nargs=0, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.lotto:
        args.colsb = '3,4,5,6,7,8'

    out_file = None
    if args.w:
        out_file = open(args.w, 'w', encoding='utf-8')
        sys.stdout = out_file

    try:
        colsa = parse_cols(args.colsa)
        colsb = parse_cols(args.colsb)
        dispcola = parse_cols(args.displaycola) or colsa
        dispcolb = parse_cols(args.displaycolb) or colsb

        with open(args.inb, newline='', encoding='utf-8') as fb:
            reader_b = list(csv.reader(fb))

        if args.from_ is not None or args.to_ is not None:
            filtered = []
            for row in reader_b:
                year = int(row[1].rsplit('.', 1)[-1])
                if args.from_ is not None and year < args.from_:
                    continue
                if args.to_ is not None and year > args.to_:
                    continue
                filtered.append(row)
            reader_b = filtered

        def extract(row, cols):
            if cols:
                return [row[i-1].strip() for i in cols if i-1 < len(row)]
            return [x.strip() for x in row]

        if args.searchfreq is not None:
            k = args.searchfreq
            counter = Counter()
            for row in reader_b:
                extracted = extract(row, colsb)
                if len(extracted) >= k:
                    for combo in combinations(sorted(extracted), k):
                        counter[combo] += 1
            items = counter.most_common()
            if args.sort == 'asc':
                items = list(reversed(items))
            if args.top:
                items = items[:args.top]
            width = len(str(len(items)))
            show_rows = dispcolb != colsb
            for i, (combo, count) in enumerate(items, 1):
                print(f'{str(i).rjust(width)}  {" ".join(combo)} : {count}')
                if show_rows:
                    set_combo = set(combo)
                    for row in reader_b:
                        extracted = extract(row, colsb)
                        if len(extracted) >= k and set_combo.issubset(set(extracted)):
                            print('  ', fmt_row(extract(row, dispcolb), set_combo, args.color))
            print(f'Total: {len(reader_b)} rows, {len(counter)} unique combinations')
            return

        if args.ina:
            with open(args.ina, newline='', encoding='utf-8') as fa:
                reader_a = list(csv.reader(fa))
            all_match = False
        else:
            reader_a = [[str(n).zfill(2) for n in (parse_cols(args.searchnumbers) or [])]]
            all_match = args.searchm == 'all'

        if not reader_a or not reader_b:
            print("One of the files is empty.")
            sys.exit(1)

        rows_a = [extract(r, colsa) for r in reader_a]
        rows_b = [extract(r, colsb) for r in reader_b]
        rows_a_disp = [extract(r, dispcola) for r in reader_a]
        rows_b_disp = [extract(r, dispcolb) for r in reader_b]

        pause_cnt = 0
        term_h = 0

        if args.pause:
            if msvcrt is None:
                sys.exit("--pause is only supported on Windows (requires msvcrt module)")
            term_h = os.get_terminal_size().lines - 1

        count = 0

        if args.t > 1:
            chunk = max(1, len(rows_a) // args.t)
            batches = []
            for i in range(0, len(rows_a), chunk):
                batch = rows_a[i:i+chunk]
                batches.append([(row_a, rows_a_disp, i + 1 + bi, rows_b, rows_b_disp, args.color, all_match) for bi, row_a in enumerate(batch)])
            with ThreadPoolExecutor(max_workers=args.t) as pool:
                futures = [pool.submit(szukaj, b) for batch in batches for b in batch]
                for f in as_completed(futures):
                    for idx_a, row_a, idx_b, row_b, wspolne in f.result():
                        print(fmt_row(row_a, wspolne, args.color), fmt_row(row_b, wspolne, args.color), sep='  ')
                        count += 1
                        if args.pause:
                            pause_cnt += 1
                            if pause_cnt >= term_h:
                                sys.stdout.write('--- More ---')
                                sys.stdout.flush()
                                assert msvcrt is not None
                                k = msvcrt.getch()
                                sys.stdout.write('\r' + ' ' * 80 + '\r')
                                sys.stdout.flush()
                                if k == b'\x1b':
                                    sys.exit(0)
                                os.system('cls')
                                pause_cnt = 0
        else:
            for idx_a, row_a in enumerate(rows_a, 1):
                zbior_a = set(row_a)
                for idx_b, row_b in enumerate(rows_b, 1):
                    wspolne = zbior_a & set(row_b)
                    if wspolne and (not all_match or wspolne == zbior_a):
                        print(fmt_row(rows_a_disp[idx_a - 1], wspolne, args.color), fmt_row(rows_b_disp[idx_b - 1], wspolne, args.color), sep='  ')
                        count += 1
                        if args.pause:
                            pause_cnt += 1
                            if pause_cnt >= term_h:
                                sys.stdout.write('--- More ---')
                                sys.stdout.flush()
                                assert msvcrt is not None
                                k = msvcrt.getch()
                                sys.stdout.write('\r' + ' ' * 80 + '\r')
                                sys.stdout.flush()
                                if k == b'\x1b':
                                    sys.exit(0)
                                os.system('cls')
                                pause_cnt = 0

        if args.searchnumbers and count:
            print(f'Found: {count} rows')
    finally:
        if out_file:
            out_file.close()
            sys.stdout = sys.__stdout__


if __name__ == '__main__':
    main()
