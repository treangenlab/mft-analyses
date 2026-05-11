import os
import glob
import shutil
import subprocess
from multiprocessing import Pool

num_workers = 16

def setup_directories(dirs):
    """Creates directories, clearing them if they already exist."""
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)


def build_mft(mft_dir):
    subprocess.run(["cargo", "build", "--release"], cwd=mft_dir, check=True)
    return os.path.join(mft_dir, "target", "release", "mft")


def transform_one(args):
    fasta, w, ordering, out_dir, binary, mapping_table = args
    base_name = os.path.splitext(os.path.basename(fasta))[0]
    out_path  = os.path.join(out_dir, f"{base_name}.fna")
    subprocess.run([
        binary,
        "transform",
        "-w", str(w),
        "-m", mapping_table,
        "-b", ordering,
        "-g", fasta,
        "-o", out_path,
    ], check=True)


windows = [5, 8, 11]

cov_genomes = sorted(glob.glob("/dodo/rdd4/mft-data/genomes/final_experiments/measles/n_849/nucleotide/*.fna"))
# cov_genomes = sorted(glob.glob("/dodo/rdd4/mft-data/genomes/final_experiments/adenovirus/n_686/nucleotide/*.fna"))
cov_genomes = sorted(glob.glob("/dodo/rdd4/mft-data/genomes/final_experiments/ebola/n_496/nucleotide/*.fna"))
cov_genomes = sorted(glob.glob("/dodo/rdd4/mft-data/genomes/final_experiments/sars-cov-2/n_2717/nucleotide/*.fna"))


out_base = "/dodo/rdd4/mft-data/genomes/final_experiments/measles/n_849"
# out_base = "/dodo/rdd4/mft-data/genomes/final_experiments/adenovirus/n_686"
out_base = "/dodo/rdd4/mft-data/genomes/final_experiments/ebola/n_496"
out_base = "/dodo/rdd4/mft-data/genomes/final_experiments/sars-cov-2/n_2717"





ordering_balanced = "/home/Users/rdd4/mft-analyses/Table1/orderings/8_110.txt"
ordering_cov      = "/home/Users/rdd4/mft-analyses/Table3/orderings/78_110_cov.txt"
mapping_table     = "/home/Users/rdd4/mft-analyses/Table1/mappings/110.txt"
mft_dir           = "/home/Users/rdd4/mft-tools"

binary = build_mft(mft_dir)

# Set up all output dirs before launching parallel jobs
# for w in windows:
#     setup_directories([
#         os.path.join(out_base, f'mft_w{w}'),
#         os.path.join(out_base, f'mft_w{w}_cov'),
#     ])

# jobs = [
#     (fasta, w, ordering, os.path.join(out_base, out_subdir), binary, mapping_table)
#     for w in windows
#     for ordering, out_subdir in [
#         (ordering_balanced, f'mft_w{w}'),
#         (ordering_cov,      f'mft_w{w}_cov'),
#     ]
#     for fasta in cov_genomes
# ]

# with Pool(num_workers) as pool:
#     pool.map(transform_one, jobs)

for w in windows:
    setup_directories([
        os.path.join(out_base, f'mft_w{w}')
    ])

jobs = [
    (fasta, w, ordering, os.path.join(out_base, out_subdir), binary, mapping_table)
    for w in windows
    for ordering, out_subdir in [
        (ordering_balanced, f'mft_w{w}')
    ]
    for fasta in cov_genomes
]

with Pool(num_workers) as pool:
    pool.map(transform_one, jobs)
