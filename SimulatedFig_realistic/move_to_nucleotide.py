import os
import shutil

out_base = "/dodo/rdd4/mft-data/seq-gen-data-cov"

for folder in sorted(os.listdir(out_base)):
    folder_path = os.path.join(out_base, folder)
    if not os.path.isdir(folder_path):
        continue

    fna_files = [f for f in os.listdir(folder_path) if f.endswith(".fna")]
    if not fna_files:
        continue

    nuc_dir = os.path.join(folder_path, "nucleotide")
    os.makedirs(nuc_dir, exist_ok=True)

    for f in fna_files:
        shutil.move(os.path.join(folder_path, f), os.path.join(nuc_dir, f))

    print(f"{folder}: moved {len(fna_files)} files -> nucleotide/")

print("Done.")
