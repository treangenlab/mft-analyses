import subprocess
from pathlib import Path
import os
from multiprocessing import Pool

min_l = 10
num_workers = 4


def run_mumemto(args):
    folder_path, k, l, output = args
    input_pattern = os.path.join(folder_path, "*.fna")
    cmd = f"mumemto {input_pattern} -l {l} -o {output} -r"
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running mumemto on {folder_path}: {e.stderr}")


data_folder = '/dodo/rdd4/mft-data/genomes/final_experiments/sars-cov-2'
# data_folder = '/dodo/rdd4/mft-data/genomes/final_experiments/measles'
# data_folder = '/dodo/rdd4/mft-data/genomes/final_experiments/adenovirus'
# data_folder = '/dodo/rdd4/mft-data/genomes/final_experiments/ebola'


jobs = []
for parent in os.listdir(data_folder):
    parent_path = os.path.join(data_folder, parent)
    if os.path.isdir(parent_path):
        for sub in os.listdir(parent_path):
            sub_path = os.path.join(parent_path, sub)
            if os.path.isdir(sub_path):
                out_destination = os.path.join(parent_path, sub)
                jobs.append((sub_path, 2, min_l, out_destination))

with Pool(num_workers) as pool:
    pool.map(run_mumemto, jobs)
