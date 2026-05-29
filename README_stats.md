# lottery_stats.py

A Python tool for analyzing lottery draw statistics from CSV files. It calculates the percentage share of each number across all draws and presents the results as text or a horizontal histogram.

**Version:** 0.2
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

Date filtering (`--datemin`, `--datemax`) is only available in `lotto` mode (where column 2 is expected to contain a date).

## Requirements

- Python 3.6 or later
- No external dependencies required for basic operation

Optional dependency for Windows ANSI color support:

- `colorama` – enables colored output on Windows terminals (`pip install colorama`)

## Usage

### Modes

You must specify exactly one mode:

| Option | Description |
|--------|-------------|
| `-num N` | Show statistics for a single number |
| `--auto` | Display a histogram of percentage shares for numbers 1–49 |
| `--mostfreq N` | Show the N most frequent numbers with a ranked list |

### General options

| Option | Description |
|--------|-------------|
| `-in FILE` | Input CSV file (required) |
| `-acc N` | Number of decimal places in percentage output (default: 2) |
| `--color` | Enable ANSI colored output |
| `--format FORMAT` | Column layout: `lotto` (default) or `cols col1,col2,...` |
| `--datemin DD.MM.YYYY` | Include draws on or after this date (lotto format only) |
| `--datemax DD.MM.YYYY` | Include draws on or before this date (lotto format only) |
| `-h` | Show condensed help |
| `--help` | Show full help with all options |

### Examples

**Statistics for a single number:**

```bash
python lottery_stats.py -in lotto.csv -num 7
```

Output:

```
Number 7 appears 889 times out of 44148 numbers drawn (7358 draws)
Percentage share: 2.01%
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

**Filtering by date range:**

```bash
python lottery_stats.py -in lotto.csv --auto --datemin 01.01.2000 --datemax 31.12.2010
```

**Custom precision:**

```bash
python lottery_stats.py -in lotto.csv -num 17 -acc 4
```

Output:

```
Number 17 appears 974 times out of 44148 numbers drawn (7358 draws)
Percentage share: 2.2062%
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
```

## How it works

1. The script reads the CSV file row by row.
2. Each number in the selected columns is counted.
3. The percentage share for a given number is calculated as:

   ```
   (count of the number ÷ total count of all drawn numbers) × 100
   ```

4. The result is displayed according to the selected mode (`-num`, `--auto`, or `--mostfreq`).

## Windows color support

On Windows, the `--color` flag attempts to enable ANSI escape sequence processing in the following order:

1. If `colorama` is installed, it is used to translate ANSI codes to Windows console API calls.
2. As a fallback, the script attempts to enable virtual terminal processing via the Windows Console API (`SetConsoleMode` with `ENABLE_VIRTUAL_TERMINAL_PROCESSING`).

If neither method succeeds, colors will not be displayed and the output falls back to plain text.
