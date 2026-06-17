# lottery_compare.py — Compare Lottery Draws Against Ticket Sets

Compare a single lottery draw row against multiple ticket rows from separate CSV files. Supports **multiple ticket sets** (separated by blank lines), **multi-set statistics**, and **optional ANSI color output**.

**Version:** 0.1
**Author:** igor.brzezek@gmail.com
**Repository:** https://github.com/IgorBrzezek/lottery_compare

---

## Table of Contents

- [Quick Start](#quick-start)
- [What is a set?](#what-is-a-set)
- [CSV Format Requirements](#csv-format-requirements)
- [Option Reference](#option-reference)
- [Usage Details](#usage-details)
  - [Single set comparison](#single-set-comparison)
  - [Comparing against multiple sets](#comparing-against-multiple-sets)
  - [Per-set statistics](#per-set-statistics)
  - [Overall hits summary](#overall-hits-summary)
- [Display Options](#display-options)
- [Complete Examples](#complete-examples)

---

## Quick Start

```bash
# Compare a draw against a single ticket set
python lottery_compare.py -a lotto.csv -b moje.csv

# Compare given numbers against tickets
python lottery_compare.py --mynumbers 1,2,3,4,5,6 -b moje.csv

# Compare against all ticket sets with statistics
python lottery_compare.py -a lotto.csv -b moje.csv --setb all --stat

# Plain ASCII output (no colors)
python lottery_compare.py -a lotto.csv -b moje.csv --mono

# Show only the combined overall hits summary
python lottery_compare.py -a lotto.csv -b moje.csv --summaryonly
```

---

## What is a set?

The script compares numbers from **setA** (a single reference draw) against numbers in **setB** (one or more ticket groups).

- **setA** — a **single row** from file `-a`, selected by `--seta` (1-based, default: row 1). This is the reference draw.
- **setB** — a **group of rows** from file `-b`. A set can have **1 or many rows**. Multiple sets in the same file are separated by **blank lines** (at least 1 empty row).

Example: if file B contains:
```
1,10,20,30,40,50
2,11,22,33,44,55

1,12,24,36,48,49

1,05,15,25,35,45
2,07,17,27,37,47
```
Then there are **3 sets**:
- Set 1 — 2 rows
- Set 2 — 1 row
- Set 3 — 2 rows

Use `--setb` to select which set(s) to compare (by number, comma-separated, or `"all"`).

---

## CSV Format Requirements

### File A (`-a`)
- A CSV file containing one or more rows of drawn numbers.
- Use `--seta` to select which row to analyze (1-based, default: 1).
- All columns are treated as drawn numbers, or use `--colsa` to select specific columns.
- Instead of `-a`, you can use `--mynumbers` to supply draw numbers directly on the command line.
- Example (`lotto.csv`): `05,10,15,20,25,30`

### File B (`-b`)
- A CSV file containing ticket rows.
- **Empty rows** separate different ticket sets.
- Each non-empty row must contain a **ticket ID** as the first column, followed by the ticket numbers.
- Use `--colsb` to select specific numeric columns (non-numeric columns like dates are safely ignored).
- Use `--displaycolsb` to show any column regardless of type.
- Example (`moje.csv`):
  ```
  1,05,10,15,20,25,30
  2,01,11,21,31,41,48

  1,07,14,21,28,35,42
  2,03,06,09,12,15,18
  ```
  (Two sets separated by a blank line.)

---

## Option Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-a` | string | — | File with drawn numbers (CSV). Alternative to `--mynumbers`. |
| `--mynumbers` | string | — | Comma-separated numbers to check (e.g. `1,2,3,4,5,6`). Alternative to `-a`. |
| `-b` | string | **required** | File with ticket numbers; empty line separates sets (CSV). |
| `--seta` | int | `1` | Row in `-a` to analyze (1-based). |
| `--setb` | string | `1` | Set(s) in `-b`: comma-separated list of 1-based numbers or `"all"`. |
| `--stat` | flag | off | Show per-set hit statistics. |
| `--mono` | flag | off | Plain ASCII output, no ANSI colors. |
| `--ppcolor` | flag | off | Color the "SET" labels in multi-set separators. |
| `--rownumbers` | flag | off | Show ticket row numbers in display. |
| `--summaryonly` | flag | off | Show only the combined overall hits summary (skip per-set display). |
| `--showdata` | flag | off | Show full data rows from file B with their file line numbers. |
| `--summary` | flag | off | Show data line counts (non-empty, non-comment) for both input files. |
| `--colsa` | string | — | Columns from file A to use (1-based, comma-separated or range, e.g. `"3-8"`). |
| `--colsb` | string | — | Columns from file B to use (1-based, comma-separated or range, or `"all"`). All selected columns are matchable numbers. |
| `--displcolsa` | string | — | Columns from file A to display only (does not affect matching). |
| `--displaycolsb` | string | — | Columns from file B to display only (does not affect matching). |
| `-h` | flag | — | Show simple help message and exit. |
| `--help` | flag | — | Show extended help message with examples and exit. |

---

## Usage Details

### Single set comparison

By default, `--setb 1` — the first set in file B is compared:

```bash
python lottery_compare.py -a lotto.csv -b moje.csv
```

You can also supply the draw numbers directly instead of using `-a`:

```bash
python lottery_compare.py --mynumbers 1,2,3,4,5,6 -b moje.csv
```

Output:
```
         Draw                Tickets
------------------------------------------
 05 10 15 20 25 30   05 10 15 20 25 30
                     01 11 21 31 41 48
```

Each row from file B is shown on its own line. Numbers that match the draw are highlighted in color (when `--mono` is not used). The first occurrence shows the draw line; subsequent lines show only the ticket side.

### Comparing against multiple sets

Use `--setb` with comma-separated numbers or `"all"`:

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --setb all
```

Each set is separated by a `=== SET N ===...` banner:

```
         Draw                Tickets
------------------------------------------
=== SET 1 =================================
         Draw                Tickets
------------------------------------------
...
------------------------------------------
=== SET 2 =================================
         Draw                Tickets
------------------------------------------
...
------------------------------------------
```

### Per-set statistics

Add `--stat` to see hit counts per set:

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --setb all --stat
```

Output after each set:
```
Hits: 1 -- 3
Hits: 2 -- 1
Hits: 3 -- 0
...
```

With `--setb all`, statistics are shown automatically.

### Overall hits summary

When comparing multiple sets, an overall summary is printed at the end:

```
        Overall Hits
==========================================
Hits: 1 -- 12
Hits: 2 -- 5
Hits: 3 -- 2
...
==========================================
```

Use `--summaryonly` to see only this summary without per-set detail:

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --summaryonly
```

---

## Display Options

### Colors

Colors are enabled by default (ANSI escape codes). Each match count has a distinct color:

| Hits | Color |
|------|-------|
| 0 | Gray (dim) |
| 1 | Bright white |
| 2 | Yellow |
| 3 | Green |
| 4 | Cyan |
| 5 | Red |
| 6 | Blue |

Use `--mono` to disable all color codes.

### `--ppcolor`

In multi-set mode (`--setb` with multiple values or `"all"`), the `=== SET N ===` separators are normally plain. With `--ppcolor`, the word "SET" and the number are colored for visual clarity.

### `--showdata`

Show every row from file B in full, prefixed by its file line number (1-based position in file B). Each line shows: `LINE_NUM: FIRST_COL, NUM1, NUM2, ...` (comma-separated). The first column (ticket ID) is shown in gray; matchable numbers are colored as usual.

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --showdata
```

Output:
```
         Draw                    Data from B
-----------------------------------------------
 05 10 15 20 25 30   1: 1, 05, 10, 15, 20, 25, 30
                     2: 2, 01, 11, 21, 31, 41, 48
```

Useful for inspecting the raw content of file B alongside the comparison results.

### Column Selection (`--colsa`, `--colsb`, `--displcolsa`, `--displaycolsb`)

By default, all columns from both files are used for comparison. Use `--colsa` and `--colsb` to focus on specific columns for matching. Use `--displcolsa` and `--displaycolsb` to control which columns are displayed without affecting matching:

```bash
# Use only columns 2-7 from the ticket file (all six are numbers)
python lottery_compare.py -a lotto.csv -b result1000_a.csv --colsb 2-7
```

Column numbers are 1-based. Accepts comma-separated values (`1,2,3`), ranges (`1-6`), or `all` (use all columns). When `--colsb` is used, ALL selected columns are matchable numbers (no column is treated as a ticket ID). Use `--rownumbers` to show the file line number.

**Non-numeric columns** (dates, text) are handled gracefully:
- `--colsb` only parses the selected columns as numbers; other columns are safely ignored
- `--displaycolsb` shows non-numeric values as-is (gray) — useful for displaying dates alongside numbers

### Display-Only Column Selection (`--displcolsa`, `--displaycolsb`)

These options control which columns are **displayed** without affecting the matching logic:

```bash
# Display only columns 1-6 from file A (matching still uses all columns)
python lottery_compare.py -a result1000_a.csv -b moje.csv --displcolsa 1-6

# Calculate using columns 2-7, display columns 1,3,5,7 from file B
python lottery_compare.py -a lotto.csv -b result1000_a.csv --colsb 2-7 --displaycolsb 1,3,5,7
```

- `--displcolsa` selects which columns of file A appear in the output (left side). Matching still uses `--colsa` or all columns.
- `--displaycolsb` selects which columns of file B appear in the output (right side). Displayed values are colored by match status based on the calculated numbers.
- All displayed values from file B are colored (no gray ID column), since the user explicitly chooses what to display.
- Column numbers are 1-based; accepts comma-separated values, ranges, or `"all"`.
- **Non-numeric columns** (dates, text) are shown as-is in gray; only numeric values participate in match coloring.

### `--summary`

Show the number of data lines (non-empty rows) in both input files. For file B, comment lines (rows whose first column starts with `#`) are excluded from the count.

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --summary
```

Output:
```
File "lotto.csv": 1512 data line(s)
File "moje.csv": 7 data line(s)
```

Useful for quickly checking how many rows are in each file before running a comparison.

### `--rownumbers`

Show the ticket ID (first column from file B) next to each ticket row:

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --rownumbers
```

Output:
```
         Draw                Tickets
------------------------------------------
 05 10 15 20 25 30   1: 05 10 15 20 25 30
                     2: 01 11 21 31 41 48
```

---

## Complete Examples

### Example 1: Basic comparison

```bash
python lottery_compare.py -a lotto.csv -b moje.csv
```

Compare the first row of `lotto.csv` against the first set in `moje.csv`.

### Example 2: All sets with statistics

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --setb all --stat
```

### Example 3: Specific sets with row numbers

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --setb 1,3 --rownumbers
```

### Example 4: Summary only (no per-set output)

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --setb all --summaryonly
```

### Example 5: Pick a specific draw row

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --seta 2
```

Use row 2 from `lotto.csv` as the draw reference instead of row 1.

### Example 6: Plain ASCII output

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --mono
```

### Example 7: Colorful separators in multi-set mode

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --setb all --ppcolor
```

### Example 8: Select specific columns

```bash
python lottery_compare.py -a result1000_a.csv -b moje.csv --colsa 3-8
```

Use only columns 3 through 8 from the draw file (skipping draw number and date columns).

### Example 9: Select columns from both files

```bash
python lottery_compare.py -a result1000_a.csv -b result1000_b.csv --colsa 3-8 --colsb 2-7
```

Use columns 3-8 from file A (draw numbers) and columns 2-7 from file B (all six are ticket numbers).

### Example 10: Display-only columns from file A

```bash
python lottery_compare.py -a result1000_a.csv -b moje.csv --displcolsa 1-6
```

Display only columns 1-6 from the draw file; matching still uses all columns.

### Example 12: Compare from command line

```bash
python lottery_compare.py --mynumbers 1,2,3,4,5,6 -b moje.csv
```

Supply draw numbers directly on the command line instead of from a CSV file.

### Example 13: Show data line summary

```bash
python lottery_compare.py -a lotto.csv -b moje.csv --summary
```

Display the count of data lines in both files. Useful before running a full comparison.

### Example 11: Different calculation and display columns from file B

```bash
python lottery_compare.py -a lotto.csv -b result1000_a.csv --colsb 2-7 --displaycolsb 1,3,5,7
```

Calculate matches using columns 2-7 from file B, but display columns 1, 3, 5, and 7 (colored by match status).

---

## Notes

- **Color support**: ANSI colors work on most modern terminals. On Windows, install `colorama` (`pip install colorama`) for proper color rendering in legacy console windows.
- **Row numbers in file B**: The first column of each non-empty row in `-b` is treated as a ticket ID / row number, displayed when `--rownumbers` is used. When using `--colsb`, no column is treated as an ID; use `--rownumbers` to show the file line number instead.
- **Column selection format**: `--colsa`, `--colsb`, `--displcolsa`, and `--displaycolsb` accept 1-based column numbers, comma-separated (`1,2,3`), ranges (`3-8`), or `"all"`.
- **Display-only columns**: `--displcolsa` and `--displaycolsb` control display without affecting matching. Useful for showing a different subset of columns than what is used for calculation.
- **Non-numeric columns**: Files may contain dates or text alongside numbers. Use `--colsb` to select only the numeric columns for matching; non-numeric columns are safely ignored. `--displaycolsb` shows any column type — numeric values are colored by match, non-numeric values appear as-is in gray.
- **Empty rows in file B**: Consecutive empty rows are collapsed (only one set increment per block of empty lines).
- **Missing sets**: If `--setb` references a set number not present in file B, a warning is printed and that set is skipped.
- **Large files**: With many tickets, the output can be long. Use `--summaryonly` for a condensed overview.
- **File A rows**: `--seta` is validated against the actual row count. An error is shown if the selected row does not exist.
- **Non-numeric file A data**: If file A contains non-numeric cells (e.g. dates), use `--colsa` to select only the numeric columns.

---

## Requirements

- Python 3.3+
- `colorama` (optional, for Windows color support)
- Standard library only: `argparse`, `csv`
- **Encoding:** CSV files are expected to be UTF-8 encoded
- **Numeric data:** All columns selected for matching (`--colsa`, `--colsb`, or all columns by default) must contain numeric values. Non-numeric values cause an error with a clear message. Use `--colsb`/`--displaycolsb` to skip date or text columns.
