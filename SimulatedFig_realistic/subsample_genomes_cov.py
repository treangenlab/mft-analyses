import os
import random

out_base     = "/dodo/rdd4/mft-data/seq-gen-data-cov"
n            = 200
scales       = [0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5]
n_reps       = 10
seeds        = [123, 456, 789, 101112, 131415, 161718, 192021, 222324, 252627, 282930]
subset_sizes = [5, 10, 25, 50, 75, 100]

# Match whatever subfolders the transform step produces
subfolders = ["nucleotide", "mft_w5", "mft_w8", "mft_w11"]


def get_genome_names(folder):
    nuc = os.path.join(folder, "nucleotide")
    return sorted(f for f in os.listdir(nuc) if f.endswith(".fna"))


for i in range(1, n_reps + 1):
    # Determine the genome list from the first scale — names are identical across scales
    ref_folder  = os.path.join(out_base, f"{n}_{scales[0]}_rep{i}")
    all_genomes = get_genome_names(ref_folder)

    assert len(all_genomes) == n, \
        f"Expected {n} genomes in {ref_folder}/nucleotide, found {len(all_genomes)}"

    # Shuffle with the replicate's fixed seed, then take nested prefixes
    rng = random.Random(seeds[i - 1])
    rng.shuffle(all_genomes)

    for s in scales:
        src_base_dir = os.path.join(out_base, f"{n}_{s}_rep{i}")

        for size in subset_sizes:
            chosen = all_genomes[:size]
            dest_base_dir = os.path.join(out_base, f"{size}_{s}_rep{i}")

            for sub in subfolders:
                src_sub  = os.path.join(src_base_dir, sub)
                dest_sub = os.path.join(dest_base_dir, sub)

                if not os.path.isdir(src_sub):
                    continue

                os.makedirs(dest_sub, exist_ok=True)

                for genome in chosen:
                    src  = os.path.join(src_sub, genome)
                    dest = os.path.join(dest_sub, genome)
                    if not os.path.exists(dest):
                        os.symlink(src, dest)

    print(f"Rep {i}: nested subsets {subset_sizes} created for all scales.")

print("Done.")
