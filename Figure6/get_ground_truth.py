#!/usr/bin/env python3
import os
import glob
from pathlib import Path
from collections import defaultdict

import numpy as np

DATA_ROOT = "/dodo/rdd4/mft-data/seq-gen-data-cov"

def read_fasta_seq(filepath):
    parts = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(">"):
                continue
            parts.append(line)
    return "".join(parts).upper()


def write_truth_vcf(dataset_dir):
    nuc_dir = os.path.join(dataset_dir, "nucleotide")
    all_files = sorted(glob.glob(os.path.join(nuc_dir, "*.fna")))

    if not all_files:
        print(f"  SKIP (no .fna files): {dataset_dir}")
        return

    ref_path = all_files[0]  # first alphabetically is the reference
    ref_seq = read_fasta_seq(ref_path)
    ref_arr = np.frombuffer(ref_seq.encode(), dtype=np.uint8)

    genome_files = all_files[1:]

    if not genome_files:
        print(f"  SKIP (no alt genomes): {dataset_dir}")
        return

    genome_names = [Path(f).stem for f in genome_files]

    # snps[(1-based pos, ref_base, alt_base)] -> list of 0/1 per genome
    # Build per-genome SNP sets then aggregate
    snp_alleles: dict[tuple[int, str, str], list[int]] = defaultdict(
        lambda: [0] * len(genome_names)
    )

    for col_idx, gfile in enumerate(genome_files):
        gseq = read_fasta_seq(gfile)
        g_arr = np.frombuffer(gseq.encode(), dtype=np.uint8)

        # Positions where sequences differ
        min_len = min(len(ref_arr), len(g_arr))
        diff_pos = np.where(ref_arr[:min_len] != g_arr[:min_len])[0]

        for pos0 in diff_pos:
            r = chr(ref_arr[pos0])
            a = chr(g_arr[pos0])
            if r in "ACGT" and a in "ACGT":
                key = (int(pos0) + 1, r, a)  # 1-based
                snp_alleles[key][col_idx] = 1

    out_path = os.path.join(dataset_dir, "truth_snps.vcf")
    sorted_keys = sorted(snp_alleles.keys())

    with open(out_path, "w") as f:
        f.write("\t".join(["POS", "REF", "ALT"] + genome_names) + "\n")
        for key in sorted_keys:
            pos, ref_base, alt_base = key
            row = [str(pos), ref_base, alt_base] + [str(v) for v in snp_alleles[key]]
            f.write("\t".join(row) + "\n")

    print(f"  {os.path.basename(dataset_dir)}: {len(sorted_keys)} SNP records -> {out_path}")


def main():
    dirs = sorted(
        d for d in glob.glob(os.path.join(DATA_ROOT, "*")) if os.path.isdir(d)
    )
    print(f"Processing {len(dirs)} dataset directories...")
    for d in dirs:
        write_truth_vcf(d)
    print("Done.")


if __name__ == "__main__":
    main()
