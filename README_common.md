# lottery_common.py — Find Common Numbers Between CSV Files

A versatile Python tool for analyzing lottery draw data in CSV format. It can **cross-check numbers between two files**, **search for specific number combinations**, **find the most frequent number pairs/triplets/etc.**, and **filter by date range** — all with optional ANSI color highlighting.

---

## Table of Contents

- [Quick Start](#quick-start)
- [CSV Format Requirements](#csv-format-requirements)
- [Option Reference](#option-reference)
  - [Mutually Exclusive Modes](#mutually-exclusive-modes)
  - [Common Options](#common-options)
- [Mode 1: Cross-check two files (`-ina` + `-inb`)](#mode-1-cross-check-two-files--ina--inb)
- [Mode 2: Search for specific numbers (`-sn` / `--searchnumbers`)](#mode-2-search-for-specific-numbers--sn---searchnumbers)
- [Mode 3: Find most frequent combinations (`-sf` / `--searchfreq`)](#mode-3-find-most-frequent-combinations--sf---searchfreq)
- [Display Options](#display-options)
- [Filtering & Performance](#filtering--performance)
- [Option Compatibility Matrix](#option-compatibility-matrix)
- [Complete Examples](#complete-examples)

---

## Quick Start

```bash
# Most common pairs in lotto draws (columns 3-8)
python lottery_common.py -inb lotto2.csv --lotto -sf 2 --sort desc --top 30

# Most common triplets in 2020-2026
python lottery_common.py -inb lotto2.csv --lotto -sf 3 --sort desc --top 10 --from 2020 --to 2026

# Find all rows containing numbers 1, 17, and 38
python lottery_common.py -inb lotto2.csv --lotto --color --searchnumbers 1,17,38 --searchm all

# Find rows containing any of 1, 17, or 38
python lottery_common.py -inb lotto2.csv --lotto --color --searchnumbers 1,17,38 --searchm one

# Cross-check two files
python lottery_common.py -ina result1000_a.csv -colsa 1,2,3,4,5,6 -inb lotto2.csv -colsb 3,4,5,6,7,8 --color
```

---

## CSV Format Requirements

### File B (`-inb`) — required for all modes
- Any CSV file. For `--from`/`--to` date filtering, column 2 (index 1) must contain dates in `DD.MM.YYYY` format.
- Use `--colsb` to select which columns to analyze.
- **lotto2.csv** example: `[draw_id, date, num1, num2, num3, num4, num5, num6]`

### File A (`-ina`) — only for cross-check mode
- A CSV file whose rows are compared against file B.
- Use `--colsa` to select which columns to analyze.
- **result1000_a.csv** example: `[draw_id, num1, num2, num3, num4, num5, num6]`

### Column Notation
Columns are specified as comma-separated 1-indexed numbers, with range support:
- `1,2,3` → columns 1, 2, 3
- `1-3,5,7-8` → columns 1, 2, 3, 5, 7, 8
- `--lotto` is shorthand for `--colsb 3,4,5,6,7,8`

---

## Option Reference

### Mutually Exclusive Modes

Exactly **one** of these three must be specified:

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `-ina` | — | string | Path to file A. Cross-checks every row of A against every row of B, showing matches. |
| `--searchnumbers` | `-sn` | string | Comma-separated list of numbers to search for in file B. |
| `--searchfreq` | `-sf` | int | Combination size (2 = pairs, 3 = triplets, etc.). Finds most frequent `k`-number combinations in file B. |

### Common Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-inb` | string | **required** | Path to file B (the target file for all modes). |
| `--colsa` | string | all cols | Columns from file A to use for comparison. |
| `--colsb` | string | all cols | Columns from file B to use for comparison. |
| `--lotto` | flag | off | Shorthand for `--colsb 3,4,5,6,7,8`. |
| `--color` | flag | off | Highlight matched numbers in red using ANSI escape codes. |
| `--displaycola` | string | same as `--colsa` | Which columns from file A to **display** (can differ from comparison columns). |
| `--displaycolb` | string | same as `--colsb` | Which columns from file B to **display** (can differ from comparison columns). |
| `--searchm` | `all` / `one` | `all` | For `--searchnumbers`: `all` = ALL numbers must be present, `one` = ANY number suffices. |
| `--sort` | `asc` / `desc` | `asc` | For `-sf`: sort results by frequency ascending or descending. |
| `--top` | int | 0 (all) | For `-sf`: limit results to top N (0 = show all). |
| `-w` | string | — | Write all output to a file instead of stdout. |
| `-t` | int | 1 | Number of worker threads for parallel processing (cross-check mode only). |
| `--pause` | flag | off | Pause after each screenful of output (Windows only). Any key except ESC continues, ESC exits. |
| `--from` | int | — | Start year (filters file B rows by date in column 2). |
| `--to` | int | — | End year (filters file B rows by date in column 2). |
| `-h`, `--help` | flag | — | Show help message and exit. |

---

## Mode 1: Cross-check two files (`-ina` + `-inb`)

Compares **every row** of file A against **every row** of file B (Cartesian product). When a row A and row B share at least one common number, both rows are displayed side by side with the common numbers highlighted.

### How it works

```
For each row_a in file A:
    For each row_b in file B:
        If row_a and row_b have any number in common → display both rows
```

### Example

```bash
python lottery_common.py -ina result1000_a.csv -colsa 1,2,3,4,5,6 -inb lotto2.csv -colsb 3,4,5,6,7,8 --color
```

Output (abbreviated):
```
0001 22 40 44 24 46  05 10 11 22 25 27
0001 22 40 44 24 46  02 11 14 37 40 45
...
```

Numbers appearing in both rows are shown in **red** when `--color` is used.

### Multi-threading

Use `-t N` to split file A rows across N threads:

```bash
python lottery_common.py -ina result1000_a.csv -colsa 1,2,3 -inb lotto2.csv --lotto -t 4 --color
```

**Note:** Threading speeds up comparison but does not reduce total output volume. For large files, use `--searchnumbers` or `-sf` instead for more focused results.

### Practical use cases

- Check which draws from file A have numbers matching any draw in the main lotto history.
- Find overlapping number patterns between two sets of lottery results.

---

## Mode 2: Search for specific numbers (`-sn` / `--searchnumbers`)

Search file B for rows that contain a specific set of numbers. All numbers are zero-padded to 2 digits for CSV compatibility.

### `--searchm all` (default) — ALL numbers must be present

Only rows containing **every** specified number are shown:

```bash
python lottery_common.py -inb lotto2.csv --lotto --color --searchnumbers 1,17,38 --searchm all
```

Output:
```
01 17 38  01 11 17 21 23 38
01 17 38  01 15 17 18 35 38
01 17 38  01 08 17 21 38 40
01 17 38  01 02 17 29 38 47
01 17 38  01 17 29 34 38 46
...
Found: N rows
```

Each line shows the searched numbers (A side) and the matching B row. Numbers highlighted in red with `--color`.

### `--searchm one` — ANY number suffices

Rows containing **at least one** of the specified numbers are shown:

```bash
python lottery_common.py -inb lotto2.csv --lotto --color --searchnumbers 1,17,38 --searchm one
```

This finds many more rows because any row containing 01, 17, OR 38 qualifies.

### Understanding the difference

| `--searchm` | Row must contain | Example: `-sn 1,17,38` matches row `01 05 10 17 25 30`? |
|-------------|------------------|----------------------------------------------------------|
| `all` | 1 AND 17 AND 38 | ❌ No (missing 38) |
| `one` | 1 OR 17 OR 38 | ✅ Yes (has 17) |

### Practical use cases

- Find all draws where your lucky numbers appeared together.
- Check if a specific triplet has ever been drawn (simpler than `-sf`).
- Find draws sharing at least one number with a given set.

---

## Mode 3: Find most frequent combinations (`-sf` / `--searchfreq`)

Analyzes file B and identifies the most common `k`-number combinations (pairs, triplets, quadruples, etc.) across all rows.

The parameter `n` specifies the **combination size**:
- `-sf 2` = find most frequent **pairs**
- `-sf 3` = find most frequent **triplets**
- `-sf 4` = find most frequent **quadruples**
- etc.

### Basic usage

```bash
python lottery_common.py -inb lotto2.csv --lotto -sf 2 --sort desc --top 10
```

Output:
```
 1  31 42 : 124
 2  21 39 : 122
 3  17 26 : 120
 4  07 46 : 120
 5  01 17 : 119
 6  17 38 : 119
 7  21 42 : 119
 8  10 11 : 118
 9  10 43 : 117
10  15 42 : 117
Total: 7358 rows, 1176 unique combinations
```

### Sorting

```bash
# Most frequent first (descending)
python lottery_common.py -inb lotto2.csv --lotto -sf 2 --sort desc --top 10

# Least frequent first (ascending — default)
python lottery_common.py -inb lotto2.csv --lotto -sf 2 --sort asc --top 10
```

### All combinations vs top N

```bash
# Top 30 most common triplets
python lottery_common.py -inb lotto2.csv --lotto -sf 3 --sort desc --top 30

# ALL triplets (18418 unique — large output!)
python lottery_common.py -inb lotto2.csv --lotto -sf 3 --sort desc
```

Without `--top`, all unique combinations are shown. With 49 numbers there are 18424 possible triplets — most will appear at least once in 7358 draws.

### Combined with date filtering

```bash
# Most common pairs in draws from 2020 to 2026
python lottery_common.py -inb lotto2.csv --lotto -sf 2 --sort desc --top 10 --from 2020 --to 2026
```

### With result1000_a.csv (no date column, in-house draws)

```bash
python lottery_common.py -inb result1000_a.csv -colsb 1,2,3,4,5,6 -sf 2 --sort desc --top 5
```

Output:
```
1  42 5 : 106
2  19 3 : 104
3  23 42 : 101
4  25 9 : 100
5  27 41 : 100
Total: 9000 rows, 46176 unique combinations
```

### Practical use cases

- Find which number pairs appear together most often.
- Discover over/under-performing combinations.
- Hot number analysis for lottery strategy.
- Identify rarely occurring pairs/triplets.

---

## Display Options

### Column selection for display (`--displaycola`, `--displaycolb`)

You can compare using one set of columns but display a different set:

```bash
# Compare using columns 1-6 but display only columns 1 and 3 from A,
# and only column 3 from B
python lottery_common.py -ina result1000_a.csv -inb lotto2.csv -colsa 1,2,3 -colsb 4,5,6 --displaycola 1,3 --displaycolb 3 --color
```

Output:
```
0001 40  43
0001 40  31
0001 40  5
...
```

### Color output (`--color`)

Highlights matched numbers in red using ANSI escape codes. Works on most modern terminals. On Windows, `colorama` is auto-detected; if unavailable, `os.system('color')` is used as fallback.

### Pause mode (`--pause`)

Displays results one screenful at a time (Windows only — requires `msvcrt` module, unavailable on Linux/macOS). After each screen:
- Press **any key** (except ESC) → show next page
- Press **ESC** → exit

### File output (`-w`)

Redirects all output to a file:

```bash
python lottery_common.py -inb lotto2.csv --lotto -sf 3 --sort desc --top 100 -w results.txt
```

---

## Filtering & Performance

### Date filtering (`--from`, `--to`)

Filter file B rows by year. Requires column 2 (index 1) to contain dates in `DD.MM.YYYY` format.

```bash
# Only draws from 2020-2026
python lottery_common.py -inb lotto2.csv --lotto -sf 3 --sort desc --top 10 --from 2020 --to 2026
```

Works with ALL modes (`-ina`, `-sn`, `-sf`).

### Threading (`-t`)

Only applies to cross-check mode (`-ina`). Splits file A into chunks and processes them in parallel:

```bash
python lottery_common.py -ina result1000_a.csv -colsa 1,2,3 -inb lotto2.csv --lotto -t 8 --color
```

**Caveat:** The cross-check is a Cartesian product. With e.g. 1000 rows in A and 7358 rows in B, that is 7.3 million comparisons. Threading helps but the output will be very large if many matches exist. For targeted searches, prefer `--searchnumbers` or `-sf`.

---

## Option Compatibility Matrix

| Options | Compatibility | Notes |
|---------|--------------|-------|
| `-ina` + `-inb` | ✅ Required combo | Core cross-check mode. `-colsa` and `-colsb` select comparison columns. |
| `-sn` + `-inb` | ✅ Required combo | Search mode. `--searchm` controls strictness. |
| `-sf` + `-inb` | ✅ Required combo | Frequency mode. `--sort` and `--top` control output. |
| `--color` | ✅ With all modes | ANSI color highlighting. |
| `--lotto` | ✅ With all modes | Shorthand for `--colsb 3,4,5,6,7,8`. |
| `--displaycola/b` | ✅ With `-ina` | Controls display columns separately from comparison columns. |
| `--displaycola/b` | ✅ With `-sn` | Controls how search numbers and B rows are displayed. |
| `--displaycola/b` | ⚠️ With `-sf` | Has no effect in frequency mode. |
| `--searchm` | ✅ Only with `-sn` | `all` (default) or `one`. |
| `--sort` / `--top` | ✅ Only with `-sf` | Controls frequency output sorting and limiting. |
| `-w` | ✅ With all modes | Redirects stdout to file. |
| `-t` | ✅ With `-ina` | Multi-threaded cross-check. Does not affect other modes. |
| `-t` | ⚠️ With `-sn` / `-sf` | No effect — these modes are single-threaded. |
| `--pause` | ✅ With all modes | Screen-by-screen output. |
| `--from` / `--to` | ✅ With all modes | Date filtering on file B. |
| `--color` + `-w` | ⚠️ Works but color codes are written to file | Typically not useful. |
| `--pause` + `-w` | ⚠️ No effect | Pausing makes no sense when writing to a file. |

---

## Complete Examples

### Example 1: Top 10 most frequent pairs in lotto history

```bash
python lottery_common.py -inb lotto2.csv --lotto -sf 2 --sort desc --top 10
```

```
 1  31 42 : 124
 2  21 39 : 122
 3  17 26 : 120
 4  07 46 : 120
 5  01 17 : 119
 6  17 38 : 119
 7  21 42 : 119
 8  10 11 : 118
 9  10 43 : 117
10  15 42 : 117
Total: 7358 rows, 1176 unique combinations
```

### Example 2: Top triplets in recent years, with color

```bash
python lottery_common.py -inb lotto2.csv --lotto -sf 3 --sort desc --top 5 --from 2020 --to 2026 --color
```

```
1  14 45 49 : 7
2  06 15 42 : 6
3  07 29 46 : 6
4  03 19 45 : 6
5  13 24 39 : 6
Total: 1003 rows, 12242 unique combinations
```

### Example 3: Colorful search for a specific triplet

```bash
python lottery_common.py -inb lotto2.csv --lotto --color --searchnumbers 14,45,49 --searchm all
```

### Example 4: Search for any of your lucky numbers

```bash
python lottery_common.py -inb lotto2.csv --lotto --color --searchnumbers 7,21,33 --searchm one
```

### Example 5: Cross-check with custom display columns

```bash
python lottery_common.py -ina result1000_a.csv -colsa 1,2,3,4,5,6 -inb lotto2.csv --lotto --displaycola 1,2 --color
```

### Example 6: Save pairs analysis to file

```bash
python lottery_common.py -inb lotto2.csv --lotto -sf 2 --sort desc --top 50 -w top50_pairs.txt
```

### Example 7: Threaded cross-check with pausing

```bash
python lottery_common.py -ina result1000_a.csv -colsa 1,2,3 -inb lotto2.csv --lotto -t 4 --color --pause
```

### Example 8: Least common pairs (ascending sort)

```bash
python lottery_common.py -inb lotto2.csv --lotto -sf 2 --sort asc --top 5
```

### Example 9: All triplets from a smaller dataset

```bash
python lottery_common.py -inb result1000_a.csv -colsb 1,2,3,4,5,6 -sf 3 --sort desc --top 10
```

### Example 10: Check with error handling (empty result)

```bash
python lottery_common.py -inb lotto2.csv --lotto --searchnumbers 99 --searchm all
# (no output — no matches found)
```

---

## Notes

- **Zero-padding**: Search numbers are automatically zero-padded (1 → 01) to match CSV format.
- **Duplicate numbers**: If your search list has duplicates (e.g., `-sn 3,3,3`), they are deduplicated in the match set.
- **Large outputs**: For `-sf` without `--top`, all possible combinations are shown. With 49 numbers, there are 1176 pairs and 18424 triplets — most will appear in the data.
- **Encoding**: All files are read/written with UTF-8 encoding.
- **Platform**: `--pause` relies on the Windows-only `msvcrt` module and will exit with an error on Linux/macOS.
- **Output file**: When using `-w`, output is buffered and flushed on normal exit. Unexpected termination may lose buffered data.

---

## Requirements

- Python 3.3+ (for `os.get_terminal_size()`, `shutil` not needed)
- `colorama` (optional, for Windows color support)
- Standard library: `argparse`, `csv`, `sys`, `os`, `concurrent.futures`, `collections`, `itertools`
- **Windows-only**: `msvcrt` module (required for `--pause` mode; not available on Linux/macOS)
