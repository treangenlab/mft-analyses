import os
import glob
import subprocess
from multiprocessing import Pool

num_workers = 16

data_root        = "/dodo/rdd4/mft-data/seq-gen-data-cov"
ordering_balanced = "/home/Users/rdd4/mft-analyses/Table1/orderings/8_110.txt"
mapping_table    = "/home/Users/rdd4/mft-analyses/Table1/mappings/110.txt"
mft_dir          = "/home/Users/rdd4/mft-tools"

windows = [5, 8, 11]


def transform_one(args):
    fasta, w, out_dir = args
    base_name = os.path.splitext(os.path.basename(fasta))[0]
    out_path  = os.path.join(out_dir, f"{base_name}.fna")
    subprocess.run([
        "cargo", "run", "--",
        "transform",
        "-w", str(w),
        "-m", mapping_table,
        "-b", ordering_balanced,
        "-g", fasta,
        "-o", out_path,
    ], cwd=mft_dir, check=True)


jobs = []
for folder in sorted(os.listdir(data_root)):
    folder_path = os.path.join(data_root, folder)
    if not os.path.isdir(folder_path):
        continue

    nuc_dir = os.path.join(folder_path, "nucleotide")
    if not os.path.isdir(nuc_dir):
        continue

    fastas = sorted(glob.glob(os.path.join(nuc_dir, "*.fna")))
    for w in windows:
        out_dir = os.path.join(folder_path, f"mft_w{w}")
        os.makedirs(out_dir, exist_ok=True)
        for fasta in fastas:
            jobs.append((fasta, w, out_dir))

print(f"Found {len(jobs)} transform jobs across {num_workers} workers...")

with Pool(num_workers) as pool:
    pool.map(transform_one, jobs)

print("Done.")
