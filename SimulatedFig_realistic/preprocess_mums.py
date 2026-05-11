"""
One-time preprocessing: parse all .mums files per {n}_{alpha}_rep{N} folder
and save a parsed.csv into each. Re-run safely — skips folders that already
have a parsed.csv.
"""

import os
import re
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

data_root = "/dodo/rdd4/mft-data/seq-gen-data-cov"
num_workers = 64

seq_len = 10000

target_files = [
    ('nucleotide.mums', 'Nucleotide'),
    ('mft_w5.mums',     'MFT (w=5)'),
    ('mft_w8.mums',     'MFT (w=8)'),
    ('mft_w11.mums',    'MFT (w=11)'),
]


def parse_mums_file(filepath, label):
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 2:
                continue
            length = int(parts[0])
            presence_list = [x.strip() for x in parts[1].split(',') if x.strip() != '']
            present_count = len(presence_list)
            is_consistent = 1 if len(set(presence_list)) == 1 else 0
            
            if is_consistent:
                if length + int(presence_list[0]) > seq_len:
                    continue
            
            data.append({
                'Length': length,
                'Present_Count': present_count,
                'Location_Consistency': is_consistent,
                'Dataset': label,
            })
    return pd.DataFrame(data)


def process_folder(combo):
    combo_path = os.path.join(data_root, combo)
    out_csv = os.path.join(combo_path, 'parsed.csv')

    # if os.path.exists(out_csv):
    #     return combo, 'skipped'

    # Accept both {n}_{alpha}_rep{N} and legacy {n}_{alpha}
    m = re.match(r'^(\d+)_([\d.]+)_rep(\d+)$', combo)
    if m:
        n_val, alpha_val, rep_val = int(m.group(1)), float(m.group(2)), int(m.group(3))
    else:
        try:
            n_str, alpha_str = combo.split('_', 1)
            n_val, alpha_val, rep_val = int(n_str), float(alpha_str), None
        except ValueError:
            return combo, 'skipped (unrecognised name)'

    frames = []
    for filename, w_label in target_files:
        filepath = os.path.join(combo_path, filename)
        if os.path.exists(filepath):
            df = parse_mums_file(filepath, w_label)
            df['n']     = n_val
            df['Alpha'] = alpha_val
            if rep_val is not None:
                df['Replicate'] = rep_val
            frames.append(df)

    if frames:
        pd.concat(frames, ignore_index=True).to_csv(out_csv, index=False)
        return combo, 'done'
    return combo, 'no mums files found'


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
