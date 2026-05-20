"""
For each .mums file per folder, compute chained MUM coverage: merge nearby
location-consistent, all-present MUMs into collinear blocks and report total
covered bases. Outputs chained_coverage.csv into each subfolder.

Only MUMs where:
  - Present_Count == n  (all genomes carry the MUM)
  - Location_Consistency == 1  (all positions are identical across genomes)
are used. Position is taken as the single shared value from column 2.
"""

import os
import re
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd

data_root   = "/dodo/rdd4/mft-data/seq-gen-data-cov"
num_workers = multiprocessing.cpu_count()

# Chaining distances to sweep — MUMs within D bp of the current block end are merged
D_values = [0, 50, 100, 150, 200, 500, 1000]
D_values = [100]

# Minimum MUM lengths to filter by before chaining
min_length_values = [10, 20, 30]

seq_length = 10000

target_files = [
    ('nucleotide.mums', 'Nucleotide'),
    ('mft_w5.mums',     'MFT (w=5)'),
    ('mft_w8.mums',     'MFT (w=8)'),
    ('mft_w11.mums',    'MFT (w=11)'),
]


def parse_anchors(filepath, n, filter_location_inconsistent=True):
    """Return sorted list of (position, length) for all-present, location-consistent MUMs."""
    anchors = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 2:
                continue
            length = int(parts[0])
            positions = [x.strip() for x in parts[1].split(',') if x.strip() != '']
            if len(positions) != n:
                continue
            if filter_location_inconsistent and len(set(positions)) != 1:
                continue
            if int(positions[0]) + length > seq_length:
                continue
            anchors.append((int(positions[0]), length))
    anchors.sort()
    return anchors


def filter_anchors(anchors, min_length):
    return [(pos, length) for pos, length in anchors if length >= min_length]


def chain(anchors, D):
    """Greedy merge: extend current block if next anchor starts within D of block end."""
    if not anchors:
        return 0, 0
    blocks = []
    start, end = anchors[0][0], anchors[0][0] + anchors[0][1]
    for pos, length in anchors[1:]:
        if pos <= end + D:
            end = max(end, pos + length)
        else:
            blocks.append(end - start)
            start, end = pos, pos + length
    blocks.append(end - start)
    return sum(blocks), len(blocks)


def process_folder(combo):
    combo_path = os.path.join(data_root, combo)
    out_csv    = os.path.join(combo_path, 'chained_coverage_no_filter.csv')

    # if os.path.exists(out_csv):
    #     return combo, 'skipped'

    m = re.match(r'^(\d+)_([\d.]+)_rep(\d+)$', combo)
    if not m:
        return combo, 'skipped (unrecognised name)'

    n_val     = int(m.group(1))
    alpha_val = float(m.group(2))
    rep_val   = int(m.group(3))

    rows = []
    for filename, label in target_files:
        filepath = os.path.join(combo_path, filename)
        if not os.path.exists(filepath):
            continue

        anchors = parse_anchors(filepath, n_val)

        for min_len in min_length_values:
            filtered = filter_anchors(anchors, min_len)
            for D in D_values:
                covered, n_blocks = chain(filtered, D)
                mean_block = covered / n_blocks if n_blocks > 0 else 0
                rows.append({
                    'Dataset':           label,
                    'Min_Length':        min_len,
                    'D':                 D,
                    'Chained_Coverage':  covered,
                    'Num_Blocks':        n_blocks,
                    'Mean_Block_Length': mean_block,
                    'n':                 n_val,
                    'Alpha':             alpha_val,
                    'Replicate':         rep_val,
                })

    if not rows:
        return combo, 'no mums files found'

    pd.DataFrame(rows).to_csv(out_csv, index=False)
    return combo, 'done'


combos = [
    c for c in sorted(os.listdir(data_root))
    if os.path.isdir(os.path.join(data_root, c))
]

total = len(combos)
print(f"Processing {total} folders with {num_workers} workers...\n")

with ProcessPoolExecutor(max_workers=num_workers) as executor:
    futures = {executor.submit(process_folder, c): c for c in combos}
    completed = 0
    for future in as_completed(futures):
        combo, status = future.result()
        completed += 1
        if completed % 20 == 0 or completed == total:
            print(f"  {completed}/{total}  [{status}] {combo}")

print("\nDone.")
