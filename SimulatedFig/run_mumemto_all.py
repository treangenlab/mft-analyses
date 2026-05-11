import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

min_l = 10
k = 2
num_workers = 50
data_root = "/dodo/rdd4/mft-data/data_longer_sequences"


def run_mumemto(folder_path, output):
    input_pattern = os.path.join(folder_path, "*.fasta")
    cmd = f"mumemto {input_pattern} -k {k} -l {min_l} -o {output}"
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error on {folder_path}: {e.stderr}")
        raise


# Collect all pending jobs across every {n}_{alpha} combo.
jobs = []

for combo in sorted(os.listdir(data_root)):
    combo_path = os.path.join(data_root, combo)
    if not os.path.isdir(combo_path):
        continue

    for sub in sorted(os.listdir(combo_path)):
        sub_path = os.path.join(combo_path, sub)
        if not os.path.isdir(sub_path):
            continue

        out_destination = os.path.join(combo_path, sub)
        output_file = f"{out_destination}.mums"
        if not os.path.exists(output_file):
            jobs.append((sub_path, out_destination))

total = len(jobs)
print(f"Found {total} mumemto jobs to run across {num_workers} workers...\n")

with ThreadPoolExecutor(max_workers=num_workers) as executor:
    futures = {executor.submit(run_mumemto, folder, out): (folder, out) for folder, out in jobs}
    completed = 0
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            folder, out = futures[future]
            print(f"FAILED: {folder} -> {e}")
        completed += 1
        if completed % 20 == 0 or completed == total:
            print(f"  {completed}/{total} jobs complete")

print("Done.")
