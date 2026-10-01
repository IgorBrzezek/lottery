# lottery_stats.py

A Python tool for analyzing lottery draw statistics from CSV files. It calculates the percentage share of each number across all draws and presents the results as text or a horizontal histogram.

**Supports 10 analysis modes:**
- `-num N` — statistics for one or more specific numbers
- `--auto` — histogram for all numbers 1–49
- `--mostfreq N` — ranked list of the N most frequent numbers
- `--neighbors` — display rows with consecutive numbers highlighted
- `--notneighbors` — display only rows **without** consecutive numbers
- `--neighbor2` / `--neighbor3` / `--neighbor4` — display only rows containing exactly 2, 3 or 4 consecutive numbers
- `--neighborstats` — horizontal histogram of rows by the number of consecutive numbers (2–6)
- `--pairstats` — statistics for consecutive number pairs (1-2, 2-3, ...), sorted by pair value

**Version:** 0.7
**Author:** igor.brzezek@gmail.com
**Repository:** https://github.com/IgorBrzezek/lottery_stats

## CSV format

### Lotto format (default)

The default input format expects a CSV file with the following columns:

```
draw_number,date,num1,num2,num3,num4,num5,num6
```

Example:

```
0001,27.01.1957,08,12,31,39,43,45
0002,03.02.1957,05,10,11,22,25,27
```

- **Column 1** – draw / round number (not used in calculations)
- **Column 2** – date in `DD.MM.YYYY` format (used for `--datemin` / `--datemax` filtering)
- **Columns 3–8** – the six numbers drawn in that round

The bundled `lotto.csv` file uses this format with historical Polish Lotto draws.

### Custom column format

For files with a different structure, use `--format cols` followed by a comma-separated list of 1-based column indices:

```bash
--format "cols 1"
--format "cols 1,2,3"
--format "cols 3,4,5,6,7,8"
```

Date filtering (`--datemin`, `--datemax`) is only available in `lotto` mode (where column 2 is expected to contain a date). When using `--format cols ...`, date filters are ignored.

## Requirements

- Python 3.6 or later
- No external dependencies required for basic operation
- **Encoding:** CSV files are expected to be UTF-8 encoded

Optional dependency for Windows ANSI color support:

- `colorama` – enables colored output on Windows terminals (`pip install colorama`)

## Usage

### Modes

You must specify exactly one mode:

| Option | Description |
|--------|-------------|
| `-num N[,M,...]` | Show statistics for one or more comma-separated numbers (e.g., `-num 7` or `-num 7,12,34`) |
| `--auto` | Display a histogram of percentage shares for numbers 1–49 |
| `--mostfreq N` | Show the N most frequent numbers with a ranked list |
| `--neighbors` | Show all rows, with consecutive numbers highlighted in green |
| `--notneighbors` | Show only rows that contain no consecutive numbers |
| `--neighbor2` | Show only rows with exactly 2 consecutive numbers |
| `--neighbor3` | Show only rows with exactly 3 consecutive numbers |
| `--neighbor4` | Show only rows with exactly 4 consecutive numbers |
| `--neighborstats` | Horizontal histogram of rows by the number of consecutive numbers (2–6) |
| `--pairstats` | Statistics for consecutive number pairs (1-2, 2-3, ... 48-49), sorted by pair value |

### General options

| Option | Description |
|--------|-------------|
| `-in FILE` | Input CSV file (required) |
| `-acc N` | Number of decimal places in percentage output (default: 2) |
| `--color` | Enable ANSI colored output |
| `--nncolor` | Highlight rows without neighbors in yellow |
| `--nosort` | Display numbers in original CSV order (do not sort) |
| `--stats` | Print a summary of the performed operation (rows read, rows matching the condition, percentage share) |
| `--format FORMAT` | Column layout: `lotto` (default) or `cols col1,col2,...` |
| `--datemin DD.MM.YYYY` | Include draws on or after this date (lotto format only) |
| `--datemax DD.MM.YYYY` | Include draws on or before this date (lotto format only) |
| `-h` | Show condensed help |
| `--help` | Show full help with all options |

### Examples

**Statistics for one or more numbers:**

```bash
python lottery_stats.py -in lotto.csv -num 7
python lottery_stats.py -in lotto.csv -num 7,12,34
```

Output (single):

```
Number 7 appears 889 times out of 44148 numbers drawn (7358 draws)
Percentage share: 2.01%
```

Output (multiple):

```
Number 7 appears 889 times out of 44148 numbers drawn (7358 draws)
Percentage share: 2.01%

Number 12 appears 934 times out of 44148 numbers drawn (7358 draws)
Percentage share: 2.12%

Number 34 appears 950 times out of 44148 numbers drawn (7358 draws)
Percentage share: 2.15%
```

**Histogram for all numbers 1–49:**

```bash
python lottery_stats.py -in lotto.csv --auto
```

Output:

```
 1 |  2.07% ######################################
 2 |  2.08% ######################################
 3 |  2.04% #####################################
...
49 |  2.00% ####################################
```

**Histogram limited to the top 6 most frequent numbers:**

```bash
python lottery_stats.py -in lotto.csv --auto --mostfreq 6
```

Output:

```
17 |  2.21% ########################################
21 |  2.17% #######################################
34 |  2.15% #######################################
38 |  2.15% #######################################
27 |  2.15% #######################################
24 |  2.14% #######################################
```

**Ranked list of the top 10 most frequent numbers:**

```bash
python lottery_stats.py -in lotto.csv --mostfreq 10
```

Output:

```
  Most frequent numbers (top 10):

 1. #17   974 times   2.21%  ####################
 2. #21   959 times   2.17%  ####################
 3. #34   950 times   2.15%  ####################
 4. #38   949 times   2.15%  ###################
 5. #27   947 times   2.15%  ###################
 6. #24   944 times   2.14%  ###################
 7. # 6   943 times   2.14%  ###################
 8. # 4   931 times   2.11%  ###################
 9. #25   929 times   2.10%  ###################
10. #36   927 times   2.10%  ###################
```

**Rows with neighboring numbers:**

```bash
python lottery_stats.py -in lotto.csv --neighbors
python lottery_stats.py -in lotto.csv --neighbors --color
python lottery_stats.py -in lotto.csv --neighbors --nncolor
python lottery_stats.py -in lotto.csv --neighbors --color --nncolor
python lottery_stats.py -in lotto.csv --neighbors --nosort
python lottery_stats.py -in lotto.csv --neighbors --datemin 01.01.2020
```

Output (plain):

```
0001 27.01.1957: 8, 12, 31, 39, 43, 45
0002 03.02.1957: 5, 10, 11, 22, 25, 27
...
```

With `--color` consecutive pairs are highlighted in green. With `--nncolor` rows without any consecutive pairs are shown entirely in yellow. With `--nosort` numbers are displayed in their original order from the CSV instead of sorted ascending.

**Rows without neighboring numbers:**

```bash
python lottery_stats.py -in lotto.csv --notneighbors
python lottery_stats.py -in lotto.csv --notneighbors --nncolor
python lottery_stats.py -in lotto.csv --notneighbors --nosort
python lottery_stats.py -in lotto.csv --notneighbors --datemin 01.01.1957 --datemax 31.12.1957
```

Output:

```
0001 27.01.1957: 8, 12, 31, 39, 43, 45
0004 17.02.1957: 2, 11, 14, 37, 40, 45
0005 24.02.1957: 8, 10, 15, 35, 39, 49
...
```

`--notneighbors` is the counterpart of `--neighbors`: it prints only the rows in which no two drawn numbers are consecutive. The same modifiers apply as with `--neighbors` — `--nncolor` prints the remaining rows in yellow, `--nosort` keeps the original CSV order, and `--datemin` / `--datemax` limit the scanned range. If no qualifying row exists, the script prints `No rows without consecutive numbers found`.

**Rows with exactly 2, 3 or 4 consecutive numbers:**

```bash
python lottery_stats.py -in lotto.csv --neighbor2
python lottery_stats.py -in lotto.csv --neighbor3
python lottery_stats.py -in lotto.csv --neighbor4
python lottery_stats.py -in lotto.csv --neighbor2 --color
python lottery_stats.py -in lotto.csv --neighbor2 --stats
python lottery_stats.py -in lotto.csv --neighbor3 --datemin 01.01.2000
```

Output (`--neighbor2`, first rows):

```
0002 03.02.1957: 5, 10, 11, 22, 25, 27
0012 14.04.1957: 2, 4, 31, 38, 39, 46
0017 26.05.1957: 16, 24, 25, 29, 32, 36
```

These three modes print only the rows in which the number of consecutive numbers matches the option exactly. A number counts as consecutive if it belongs to a run of at least two consecutive values, and runs are summed together:

| Option | Matches | Example row |
|--------|---------|-------------|
| `--neighbor2` | exactly 2 consecutive numbers | `5, 10, 11, 22, 25, 27` (one pair: 10-11) |
| `--neighbor3` | exactly 3 consecutive numbers | `18, 19, 20, 26, 45, 49` (one run of three) |
| `--neighbor4` | exactly 4 consecutive numbers | `1, 15, 16, 19, 47, 48` (two pairs: 15-16 and 47-48) |
| — | not matched by any of them | `1, 15, 16, 17, 47, 48` (a run of three plus a pair — 5 consecutive numbers) |

The same modifiers apply as with `--neighbors`: `--color` highlights the consecutive numbers in green, `--nosort` keeps the original CSV order, and `--datemin` / `--datemax` limit the scanned range. If no qualifying row exists, the script prints `No rows with exactly N consecutive number(s) found`.

**Histogram of rows by number of consecutive numbers:**

```bash
python lottery_stats.py -in lotto.csv --neighborstats
python lottery_stats.py -in lotto.csv --neighborstats --color
python lottery_stats.py -in lotto.csv --neighborstats --stats
python lottery_stats.py -in lotto.csv --neighborstats --datemin 01.01.2000
```

Output:

```
  Rows by number of consecutive numbers:

100.00% ######################################## All rows                   7358
 38.99% ################                         2 consecutive numbers      2869
  3.98% ##                                       3 consecutive numbers       293
  6.05% ##                                       4 consecutive numbers       445
  0.76%                                          5 consecutive numbers        56
  0.16%                                          6 consecutive numbers        12

  Consecutive numbers are drawn values differing by 1; rows with fewer than 2 are listed under 'All rows' only.
```

The first column holds the percentage of all analyzed rows, followed by a horizontal bar, the label and the raw row count. Percentages are always relative to `All rows`, and `-acc` controls their precision. Rows with no consecutive numbers are not listed separately — they are only part of the `All rows` total. If a file holds more columns than a Lotto draw (`--format cols ...`), an extra `>6 consecutive numbers` line appears when such rows exist.

**Statistics for consecutive number pairs (sorted by pair value):**

```bash
python lottery_stats.py -in lotto.csv --pairstats
python lottery_stats.py -in lotto.csv --pairstats --color
```

Output (pairs sorted by value, not frequency):

```
  Consecutive pair statistics:

 1.   1-2    96  ##################################
 2.   2-3    93  #################################
...
48. 48-49    83  #############################
```

**Filtering by date range:**

```bash
python lottery_stats.py -in lotto.csv --auto --datemin 01.01.2000 --datemax 31.12.2010
```

**Custom precision:**

```bash
python lottery_stats.py -in lotto.csv -num 17,21 -acc 4
```

Output:

```
Number 17 appears 974 times out of 44148 numbers drawn (7358 draws)
Percentage share: 2.2062%

Number 21 appears 959 times out of 44148 numbers drawn (7358 draws)
Percentage share: 2.1722%
```

**Colored output (if your terminal supports ANSI):**

```bash
python lottery_stats.py -in lotto.csv --auto --color
```

**Analyzing a file with a non-standard format:**

If your CSV has numbers in columns 2 and 4 only (1-based indexing):

```bash
python lottery_stats.py -in mydata.csv --auto --format "cols 2,4"
```

**Single-column file:**

For a file containing just one number per line:

```bash
python lottery_stats.py -in numbers.csv -num 5 --format "cols 1"
python lottery_stats.py -in numbers.csv -num 5,8,13 --format "cols 1"
```

## How it works

1. The script reads the CSV file row by row.
2. Each number in the selected columns is counted.
3. The percentage share for a given number is calculated as:

   ```
   (count of the number ÷ total count of all drawn numbers) × 100
   ```

4. The result is displayed according to the selected mode (`-num`, `--auto`, `--mostfreq`, `--neighbors`, `--notneighbors`, `--neighbor2`/`3`/`4`, `--neighborstats`, or `--pairstats`).
5. Adding `--stats` appends a summary of the operation (see below).

## Operation statistics (`--stats`)

`--stats` is a modifier that can be combined with any mode. After the normal output it prints how many rows were read, how many were analyzed, how many matched the condition of the selected mode and what percentage that is:

```bash
python lottery_stats.py -in lotto.csv --notneighbors --stats
python lottery_stats.py -in lotto.csv --notneighbors --stats --datemax 31.12.1957
python lottery_stats.py -in lotto.csv --neighborstats --stats
python lottery_stats.py -in lotto.csv --pairstats --stats
python lottery_stats.py -in lotto.csv -num 7,12 --stats
```

Output (`--notneighbors` limited to 1957):

```
  Operation statistics (--notneighbors)

  Rows in file:               7371
  Rows skipped:              7324 (99.36% of 7371 all rows)
  Rows analyzed:                47
  Rows without neighbors:       33 (70.21% of 47 analyzed rows)
  Rows displayed:               33 (70.21% of 47 analyzed rows)
```

| Mode | Reported "condition" rows |
|------|---------------------------|
| `--neighbors` | Rows containing at least one consecutive pair (and the number of printed rows) |
| `--neighbor2` / `--neighbor3` / `--neighbor4` | Rows with exactly 2, 3 or 4 consecutive numbers (and the number of printed rows) |
| `--notneighbors` | Rows without any consecutive pair (and the number of printed rows) |
| `--neighborstats` | Rows containing at least one consecutive pair (the histogram itself is printed by the mode) |
| `--pairstats` | Rows containing at least one consecutive pair, plus the number of distinct pairs found |
| `-num N[,M,...]` | Draws in which each of the given numbers appeared (percentage of all draws) |
| `--auto`, `--mostfreq N` | Number of numbers displayed |

`Rows skipped` counts rows dropped before analysis — malformed rows, rows shorter than the selected column layout, or rows outside the `--datemin` / `--datemax` range. Percentages are relative to the base shown next to them, so `--datemin` / `--datemax` filtering does not distort the share of matching rows. The `-acc` option controls the number of decimal places in these percentages as well.

## Windows color support

On Windows, the `--color` flag attempts to enable ANSI escape sequence processing in the following order:

1. If `colorama` is installed, it is used to translate ANSI codes to Windows console API calls.
2. As a fallback, the script attempts to enable virtual terminal processing via the Windows Console API (`SetConsoleMode` with `ENABLE_VIRTUAL_TERMINAL_PROCESSING`).

If neither method succeeds, colors will not be displayed and the output falls back to plain text.

## Additional examples

**Top 6 most frequent numbers from a file with custom column layout (columns 3-8):**

```bash
python lottery_stats.py -in data.csv --format "cols 3,4,5,6,7,8" --mostfreq 6 --color
```

Output:
```
Total draws: 7358

  Statistics for 6 most frequent numbers:

 1. #17  974 times    2.21%  ####################
 2. #21  959 times    2.17%  ####################
 3. #34  950 times    2.15%  ####################
 4. #38  949 times    2.15%  ###################
 5. #27  947 times    2.15%  ###################
 6. #24  943 times    2.14%  ###################
```

**Show neighbors with custom column layout:**

```bash
python lottery_stats.py -in data.csv --format "cols 3,4,5,6,7,8" --neighbors --color
```