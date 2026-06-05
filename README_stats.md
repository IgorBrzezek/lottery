# lottery_stats.py

A Python tool for analyzing lottery draw statistics from CSV files. It calculates the percentage share of each number across all draws and presents the results as text or a horizontal histogram.

**Supports 5 analysis modes:**
- `-num N` — statistics for one or more specific numbers
- `--auto` — histogram for all numbers 1–49
- `--mostfreq N` — ranked list of the N most frequent numbers
- `--neighbors` — display rows with consecutive numbers highlighted
- `--neighborstats` — statistics for consecutive number pairs (1-2, 2-3, ...), sorted by pair value

**Version:** 0.3
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
| `--neighborstats` | Statistics for consecutive number pairs (1-2, 2-3, ... 48-49), sorted by pair value |

### General options

| Option | Description |
|--------|-------------|
| `-in FILE` | Input CSV file (required) |
| `-acc N` | Number of decimal places in percentage output (default: 2) |
| `--color` | Enable ANSI colored output |
| `--nncolor` | Highlight rows without neighbors in yellow |
| `--nosort` | Display numbers in original CSV order (do not sort) |
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

**Statistics for consecutive number pairs (sorted by pair value):**

```bash
python lottery_stats.py -in lotto.csv --neighborstats
python lottery_stats.py -in lotto.csv --neighborstats --color
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

4. The result is displayed according to the selected mode (`-num`, `--auto`, `--mostfreq`, `--neighbors`, or `--neighborstats`).

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