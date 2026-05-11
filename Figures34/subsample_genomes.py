import os
import random
import glob

seed        = 42
src_base    = "/dodo/rdd4/mft-data/genomes/final_experiments/sars-cov-2/n_2717"
# src_base    = "/dodo/rdd4/mft-data/genomes/final_experiments/measles/n_849"
# src_base    = "/dodo/rdd4/mft-data/genomes/final_experiments/adenovirus/n_686"
# src_base    = "/dodo/rdd4/mft-data/genomes/final_experiments/ebola/n_496"


out_base    = "/dodo/rdd4/mft-data/genomes/final_experiments/sars-cov-2"
# out_base    = "/dodo/rdd4/mft-data/genomes/final_experiments/measles"
# out_base    = "/dodo/rdd4/mft-data/genomes/final_experiments/adenovirus"
# out_base    = "/dodo/rdd4/mft-data/genomes/final_experiments/ebola"


n_reps      = 5
subset_sizes = [10, 25, 50, 75, 100, 200, 500] ## Covid, rotavirus
subset_sizes = [10, 25, 50, 75, 100, 200] ## Measles + Adenovirus + ebola
subfolders  = ["nucleotide", "mft_w5", "mft_w8", "mft_w11", "mft_w5_cov", "mft_w8_cov", "mft_w11_cov"] #covid
subfolders  = ["nucleotide", "mft_w5", "mft_w8", "mft_w11"] ## others

# All genome basenames (without extension) from nucleotide/
all_genomes = sorted(
    os.path.splitext(f)[0]
    for f in os.listdir(os.path.join(src_base, "nucleotide"))
    if f.endswith(".fna")
)

max_subset_size = max(subset_sizes)
total_needed    = n_reps * max_subset_size

rng = random.Random(seed)

# Build a stream: deal from a shuffled deck; when exhausted, reshuffle and continue
stream = []
while len(stream) < total_needed:
    deck = all_genomes[:]
    rng.shuffle(deck)
    stream.extend(deck)

pools = [stream[(rep - 1) * max_subset_size : rep * max_subset_size]
         for rep in range(1, n_reps + 1)]

print(f"{len(all_genomes)} genomes, {n_reps} reps × {max_subset_size} = {total_needed} needed "
      f"({'disjoint' if total_needed <= len(all_genomes) else 're-shuffled'})")

for rep in range(1, n_reps + 1):
    pool_n = pools[rep - 1]

    for size in subset_sizes:
        chosen = pool_n[:size]
        dest_dir = os.path.join(out_base, f"n_{size}_rep{rep}")

        for sub in subfolders:
            sub_dir = os.path.join(dest_dir, sub)
            os.makedirs(sub_dir, exist_ok=True)

            src_sub = os.path.join(src_base, sub)
            for name in chosen:
                src  = os.path.join(src_sub, f"{name}.fna")
                dest = os.path.join(sub_dir, f"{name}.fna")
                if not os.path.lexists(dest):
                    os.symlink(src, dest)

    print(f"Rep {rep}: created nested subsets {subset_sizes} from pool of {max_subset_size}")

print("Done.")
