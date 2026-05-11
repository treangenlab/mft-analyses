import subprocess
import os

tree_file = "/home/Users/rdd4/mft-analyses/Figure4/cov_200_parsnp_raxml/parsnp.tree"
out_base  = "/dodo/rdd4/mft-data/seq-gen-data-cov"

n        = 200
scale    = [0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5]
n_reps   = 10
seeds = [123, 456, 789, 101112, 131415, 161718, 192021, 222324, 252627, 282930]


def split_multifasta(folder):
    multifasta = os.path.join(folder, "_1.fasta")
    current_header = None
    current_lines  = []

    with open(multifasta) as f:
        for line in f:
            if line.startswith(">"):
                if current_header is not None:
                    out_path = os.path.join(folder, f"{current_header}")
                    with open(out_path, "w") as out:
                        out.write(f">{current_header}\n")
                        out.writelines(current_lines)
                current_header = line[1:].strip()
                current_lines  = []
            else:
                current_lines.append(line)

    if current_header is not None:
        out_path = os.path.join(folder, f"{current_header}")
        with open(out_path, "w") as out:
            out.write(f">{current_header}\n")
            out.writelines(current_lines)

    os.remove(multifasta)


for i in range(1, n_reps + 1):
    for s in scale:
        folder = os.path.join(out_base, f"{n}_{s}_rep{i}")
        os.makedirs(folder, exist_ok=True)

        cmd = ["seq-gen", "-mGTR", "-l10000", "-ofs", f"-s{s}", f"-z{seeds[i-1]}", "-y", "test"]
        with open(tree_file) as tree_in:
            print(f"Running replicate {i} -> {folder}")
            subprocess.run(cmd, stdin=tree_in, cwd=folder, check=True)

        print(f"  Splitting _1.fasta into individual files...")
        split_multifasta(folder)
