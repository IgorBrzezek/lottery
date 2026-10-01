import csv
import math
import numpy as np
from scipy import stats
from collections import defaultdict, Counter
from itertools import combinations
from datetime import datetime

SEP = "=" * 56

# ── Load data ──────────────────────────────────────────────────────────
draws = []
all_numbers = []
with open("a.csv", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) < 3:
            continue
        try:
            nums = [int(x) for x in row[2:8]]
        except (ValueError, IndexError):
            continue
        draws.append(nums)
        all_numbers.extend(nums)

total_draws = len(draws)
N = total_draws * 6
print(f"Total draws: {total_draws}")
print(f"Total numbers drawn: {N}")
print()

# ── 1. Basic frequency & chi-squared ──────────────────────────────────
freq = Counter(all_numbers)
expected = N / 49
print(f"Expected frequency per number: {expected:.1f}")
print()

# Chi-squared test
chi2_stat = sum((freq.get(i, 0) - expected)**2 / expected for i in range(1, 50))
chi2_p = 1 - stats.chi2.cdf(chi2_stat, 48)
print(SEP)
print("  1. CHI-SQUARED GOODNESS-OF-FIT TEST")
print(SEP)
print(f"  chi^2 = {chi2_stat:.2f}  (df=48)")
print(f"  p     = {chi2_p:.6f}")
if chi2_p < 0.05:
    print("  RESULT: Significant deviation (p<0.05)")
    print("  Distribution differs from uniform")
else:
    print("  RESULT: No significant deviation (p>=0.05)")
    print("  Distribution consistent with uniform")
print(SEP)
print()

# Human pattern detection
consec_draws = sum(1 for d in draws if any(sorted(d)[i+1] - sorted(d)[i] == 1 for i in range(len(d)-1)))
odd_counts = [sum(1 for n in d if n % 2 == 1) for d in draws]
total_odd = sum(odd_counts)
total_even = N - total_odd
z_odd = (total_odd - N*0.5) / math.sqrt(N*0.5*0.5)
p_odd = 2 * (1 - stats.norm.cdf(abs(z_odd)))

print(SEP)
print("  HUMAN PATTERN DETECTION")
print(SEP)
p_consec = consec_draws / total_draws * 100
print(f"  Draws with consecutive numbers: {consec_draws}/{total_draws} ({p_consec:.1f}%)")
avg_odd = np.mean(odd_counts)
print(f"  Avg odd numbers per draw: {avg_odd:.2f} of 6")
print(f"  Odd/even balance: z={z_odd:.2f} p={p_odd:.4f}")
if p_odd < 0.05:
    print("  -> Significant skew towards odd numbers!")
else:
    print("  -> Odd/even balance consistent with random")
print(SEP)
print()

# ── 2. Trend analysis: recent windows ─────────────────────────────────
print(SEP)
print("  2. TREND ANALYSIS (HOT/COLD NUMBERS)")
print(SEP)
for window in [100, 500, 1000, 2000]:
    recent_draws = draws[-window:]
    recent_freq = Counter()
    for d in recent_draws:
        recent_freq.update(d)
    exp_recent = window * 6 / 49

    sorted_recent = sorted(recent_freq.items(), key=lambda x: -x[1])
    top3 = [str(n) for n, c in sorted_recent[:3]]
    bot3 = [str(n) for n, c in sorted_recent[-3:]]
    all_nums_set = set(range(1, 50))
    missing = all_nums_set - set(recent_freq.keys())

    print(f"  Window: last {window:>4} draws")
    print(f"  Hottest: {', '.join(top3):>8}  Coldest: {', '.join(bot3):>8}")
    if missing:
        print(f"  Missing (0 times): {','.join(str(x) for x in sorted(missing))}")
    print(f"  Expected per num: {exp_recent:.1f}")

    chi2_recent = sum((recent_freq.get(i, 0) - exp_recent)**2 / exp_recent for i in range(1, 50))
    p_recent = 1 - stats.chi2.cdf(chi2_recent, 48)
    sig = "SIGNIFICANT" if p_recent < 0.05 else "not significant"
    print(f"  Chi^2={chi2_recent:.1f} p={p_recent:.4f} ({sig})")
    print()
print(SEP)
print()

# ── 3. Gap analysis ──────────────────────────────────────────────────
gaps = {i: [] for i in range(1, 50)}
last_seen = {i: None for i in range(1, 50)}
for idx, d in enumerate(draws):
    for n in d:
        if last_seen[n] is not None:
            gaps[n].append(idx - last_seen[n])
        last_seen[n] = idx

current_gaps = {i: total_draws - last_seen[i] for i in range(1, 50)}

print(SEP)
print("  3. GAP ANALYSIS")
print(SEP)
print("  Number  | Avg Gap  | Curr Gap")
print("-" * 35)
all_gaps_sorted = sorted([(i, current_gaps[i]) for i in range(1, 50)], key=lambda x: -x[1])
for rank, (i, curr) in enumerate(all_gaps_sorted[:10], 1):
    avg = np.mean(gaps[i]) if gaps[i] else 0
    print(f"  {rank:3d}.  #{i:2d}   |   {avg:5.1f}   |   {curr:3d}")
print("  ... (top 10 longest gaps)")
print()
print("  Most overdue numbers:")
for i, g in all_gaps_sorted[:6]:
    avg = np.mean(gaps[i]) if gaps[i] else 0
    print(f"    #{i:2d}  {g} draws ago (avg gap: {avg:.0f})")
print()
print("  Most recent numbers:")
all_gaps_sorted_asc = sorted([(i, current_gaps[i]) for i in range(1, 50)], key=lambda x: x[1])
for i, g in all_gaps_sorted_asc[:6]:
    avg = np.mean(gaps[i]) if gaps[i] else 0
    print(f"    #{i:2d}  {g} draws ago (avg gap: {avg:.0f})")
print(SEP)
print()

# ── 4. Pair analysis ──────────────────────────────────────────────────
pair_counts = Counter()
for d in draws:
    for pair in combinations(sorted(d), 2):
        pair_counts[pair] += 1

total_pairs = total_draws * 15
n_pairs = 49 * 48 / 2
exp_pair_freq = total_pairs / n_pairs

print(SEP)
print("  4. PAIR CO-OCCURRENCE ANALYSIS")
print(SEP)
print("  Most frequent pairs (top 15):")
most_common_pairs = pair_counts.most_common(15)
for rank, (pair, count) in enumerate(most_common_pairs, 1):
    ratio = count / exp_pair_freq
    print(f"  {rank:2d}. {pair[0]:2d}-{pair[1]:2d}  count={count:3d}  ({ratio:.2f}x expected)")
print()
print("  Least frequent pairs (bottom 10):")
least_common_pairs = pair_counts.most_common()[:-51:-1]
for rank, (pair, count) in enumerate(least_common_pairs[:10], 1):
    ratio = count / exp_pair_freq
    print(f"  {rank:2d}. {pair[0]:2d}-{pair[1]:2d}  count={count:3d}  ({ratio:.2f}x expected)")
print(SEP)
print()

# ── 5. Draw-level statistics ──────────────────────────────────────────
sums = [sum(d) for d in draws]
even_counts = [sum(1 for n in d if n % 2 == 0) for d in draws]
range_vals = [max(d) - min(d) for d in draws]
neighbor_counts = []
for d in draws:
    s = sorted(d)
    nc = sum(1 for i in range(len(s)-1) if s[i+1] - s[i] == 1)
    neighbor_counts.append(nc)
nc_dist = Counter(neighbor_counts)

print(SEP)
print("  5. DRAW-LEVEL STATISTICS")
print(SEP)
print(f"  Sum distribution:")
print(f"    mean={np.mean(sums):.1f}  median={np.median(sums):.0f}  min={min(sums)}  max={max(sums)}")
print(f"    Expected mean for uniform: 147.0")
print(f"  Even count per draw: mean={np.mean(even_counts):.2f}")
print(f"  Distribution: {dict(sorted(Counter(even_counts).items()))}")
print(f"  Range: mean={np.mean(range_vals):.1f}  median={np.median(range_vals):.0f}")
print(f"  Consecutive neighbor count distribution: {dict(sorted(nc_dist.items()))}")
print(SEP)
print()

# ── 6. Benford's law ──────────────────────────────────────────────────
first_digits = []
for num in all_numbers:
    first_digits.append(int(str(num)[0]))
digit_freq = Counter(first_digits)
total_digits = len(first_digits)

print(SEP)
print("  6. BENFORD'S LAW ANALYSIS")
print(SEP)
print("  Digit | Observed | Expected(Benford) | Ratio")
print("-" * 50)
benford_chi2 = 0
for d in range(1, 10):
    observed = digit_freq.get(d, 0)
    expected_benford = total_digits * math.log10(1 + 1/d)
    ratio = observed / expected_benford if expected_benford > 0 else 0
    benford_chi2 += (observed - expected_benford)**2 / expected_benford
    print(f"  {d:5d} | {observed:8d} | {expected_benford:10.0f}       | {ratio:.2f}")

benford_p = 1 - stats.chi2.cdf(benford_chi2, 8)
print(f"  Chi^2={benford_chi2:.2f} p={benford_p:.4f}")
if benford_p < 0.05:
    print("  -> Deviates from Benford (possible manipulation)")
else:
    print("  -> Consistent with Benford's law")
print(SEP)
print()

# ── 7. Hot/cold composite score ─────────────────────────────────────
recent_100 = Counter()
for d in draws[-100:]:
    recent_100.update(d)
recent_500 = Counter()
for d in draws[-500:]:
    recent_500.update(d)

overall_min = min(freq.values())
overall_max = max(freq.values())
recent100_min = min(recent_100.get(i, 0) for i in range(1, 50))
recent100_max = max(recent_100.get(i, 0) for i in range(1, 50))
recent500_min = min(recent_500.get(i, 0) for i in range(1, 50))
recent500_max = max(recent_500.get(i, 0) for i in range(1, 50))
gap_min = min(current_gaps.values())
gap_max = max(current_gaps.values())
gap_range = gap_max - gap_min if gap_max > gap_min else 1

scores = {}
for i in range(1, 50):
    overall_score = (freq[i] - overall_min) / (overall_max - overall_min) if overall_max > overall_min else 0.5
    r100 = recent_100.get(i, 0)
    r100_score = (r100 - recent100_min) / (recent100_max - recent100_min) if recent100_max > recent100_min else 0.5
    r500 = recent_500.get(i, 0)
    r500_score = (r500 - recent500_min) / (recent500_max - recent500_min) if recent500_max > recent500_min else 0.5
    gap_score = (current_gaps[i] - gap_min) / gap_range if gap_range > 0 else 0.5
    scores[i] = (0.20 * overall_score + 0.35 * r100_score + 0.20 * r500_score + 0.25 * gap_score)

print(SEP)
print("  7. COMPOSITE PREDICTION MODEL")
print(SEP)
print("  Factors: Overall freq 20%, Recent 100 35%, Recent 500 20%, Gap 25%")
print("-" * 50)
print("  Rank | #  | Score | Freq  | R100 | Gap ")
print("-" * 42)
ranked = sorted(scores.items(), key=lambda x: -x[1])
for rank, (num, score) in enumerate(ranked[:10], 1):
    print(f"  {rank:3d}. | #{num:2d} | {score:.3f} | {freq[num]:4d} | {recent_100.get(num, 0):3d} | {current_gaps[num]:3d}")
print()
print("  Bottom 5 (least likely):")
for rank, (num, score) in enumerate(ranked[-5:], 1):
    print(f"  {rank:3d}. | #{num:2d} | {score:.3f} | {freq[num]:4d} | {recent_100.get(num, 0):3d} | {current_gaps[num]:3d}")
print(SEP)
print()

# ── 8. FINAL PREDICTION ──────────────────────────────────────────────
prediction = ranked[:6]
pred_nums = [num for num, score in prediction]

print(SEP)
print("  8. FINAL PREDICTION")
print(SEP)
print()
print("  MOST PROBABLE 6 NUMBERS (Composite Model):")
print()
pred_str = "  --  ".join(f"#{n:2d}" for n in pred_nums)
print(f"    {pred_str}")
print()
print(f"  Sorted: {sorted(pred_nums)}")
print(f"  Sum: {sum(pred_nums)} (expected ~147)")
odd_count = sum(1 for n in pred_nums if n % 2 == 1)
print(f"  Odd/Even: {odd_count}/{6-odd_count}")
s = sorted(pred_nums)
has_neighbors = any(s[i+1] - s[i] == 1 for i in range(len(s)-1))
print(f"  Has consecutive neighbors: {'YES' if has_neighbors else 'NO'}")
print()
print("  Justification:")
for num, score in prediction:
    r100 = recent_100.get(num, 0)
    r500 = recent_500.get(num, 0)
    gap = current_gaps[num]
    print(f"    #{num:2d}: freq={freq[num]:3d}, last {gap:3d} draws ago, recent={r100}/{r500} (100/500), score={score:.3f}")
print()
print(SEP)
print()

# ── 9. Alternate predictions ──────────────────────────────────────────
top_overdue = sorted([(i, current_gaps[i]) for i in range(1, 50)], key=lambda x: -x[1])[:6]
overdue_nums = [n for n, g in top_overdue]
print(SEP)
print("  9. ALTERNATE PREDICTIONS")
print(SEP)
print("  Strategy A: Most Overdue (numbers 'due')")
print(f"    {', '.join(f'#{n:2d}(gap={g:3d})' for n, g in top_overdue)}")
print(f"    Sorted: {sorted(overdue_nums)}  Sum: {sum(overdue_nums)}")
print()

hot_recent = sorted([(i, recent_100.get(i, 0)) for i in range(1, 50)], key=lambda x: -x[1])[:6]
hot_nums = [n for n, c in hot_recent]
print("  Strategy B: Hottest in Last 100 Draws")
print(f"    {', '.join(f'#{n:2d}(cnt={c:2d})' for n, c in hot_recent)}")
print(f"    Sorted: {sorted(hot_nums)}  Sum: {sum(hot_nums)}")
print(SEP)
print()

# ── 10. SUMMARY ──────────────────────────────────────────────────────
print(SEP)
print("  SUMMARY OF ALL FINDINGS")
print(SEP)
print(f"  1. Overall distribution: {'non-uniform (p<0.05)' if chi2_p < 0.05 else 'consistent with random'}")
print(f"  2. Odd/even balance: {'skewed to odd' if p_odd < 0.05 else 'balanced'}")
print(f"  3. Consecutive neighbors: {p_consec:.1f}% of draws have them")
print(f"  4. Benford: {'passes' if benford_p >= 0.05 else 'FAILS'} test (p={benford_p:.3f})")
print()
print("  RECOMMENDED BET (Composite Model):")
print(f"    Sorted: {sorted(pred_nums)}")
print()
print("  BACKUP BET (Overdue):")
print(f"    Sorted: {sorted(overdue_nums)}")
print()
print("  BACKUP BET (Hot streak):")
print(f"    Sorted: {sorted(hot_nums)}")
print(SEP)
