#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
from multiprocessing import Pool

# Import filter_xmfa from the same directory as this script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filter_xmfa import filter_xmfa

DATASETS = ["nucleotide", "mft_w5", "mft_w8", "mft_w11"]


def process_one(ds_dir):
    xmfa_in  = os.path.join(ds_dir, "parsnp.xmfa")
    xmfa_out = os.path.join(ds_dir, "parsnp_filtered.xmfa")
    vcf_out  = os.path.join(ds_dir, "parsnp_filtered.vcf")

    if not os.path.exists(xmfa_in):
        print(f"Skipping (no parsnp.xmfa): {ds_dir}")
        return

    print(f"Filtering: {ds_dir}")
    num_LCBs_filtered = filter_xmfa(xmfa_in, xmfa_out)

    with open(os.path.join(ds_dir, "fp_lcbs.txt"), 'w') as fp:
        fp.write(str(num_LCBs_filtered) + '\n')

    print(f"Running harvesttools: {ds_dir}")
    subprocess.run(
        ["harvesttools", "-x", xmfa_out, "-V", vcf_out],
        check=True,
    )
    print(f"Done: {ds_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter parsnp.xmfa and generate VCFs across all subfolders."
    )
    parser.add_argument("root", help="Root directory (e.g. /dodo/ab235/actual-final/adenovirus)")
    parser.add_argument("--workers", type=int, default=8, help="Parallel workers (default: 8)")
    args = parser.parse_args()

    jobs = []
    for rep_folder in sorted(os.listdir(args.root)):
        rep_path = os.path.join(args.root, rep_folder)
        if not os.path.isdir(rep_path):
            continue
        for ds in DATASETS:
            ds_dir = os.path.join(rep_path, ds)
            if os.path.isdir(ds_dir):
                jobs.append(ds_dir)

    print(f"Found {len(jobs)} dataset directories.")

    with Pool(args.workers) as pool:
        pool.map(process_one, jobs)

    print("All done.")
