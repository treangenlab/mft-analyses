import random
import os
import shutil
import subprocess

import pandas as pd
import numpy as np

def generate_random_dna(length, seed=10):
    """Generates a random DNA sequence of specified length."""
    random.seed(seed)
    return "".join(random.choices("ACGT", k=length))

def mutate_sequence(seq, sub_rate=0.05, indel_rate=0.00, seed=20):
    """
    Introduces mutations to simulate a related sequence.
    sub_rate: Probability of a single-base substitution.
    indel_rate: Probability of a 1bp insertion or deletion.
    """
    mutated = []
    i = 0
    random.seed(seed)

    while i < len(seq):
        r = random.random()
        if r < indel_rate:
            if random.random() < 0.5: # Insertion
                mutated.append(random.choice("ACGT"))
                mutated.append(seq[i])
            else: # Deletion
                pass
        elif r < (sub_rate + indel_rate): # Substitution
            mutated.append(random.choice([b for b in "ACGT" if b != seq[i]]))
        else: # Match
            mutated.append(seq[i])
        i += 1
    return "".join(mutated)

def write_fasta(sequences, filename):
    """Writes a list of sequences to a FASTA file."""
    with open(filename, 'w') as f:
        for i, seq in enumerate(sequences):
            f.write(f">seq_{i}\n{seq}\n")
    print(f"--- Created {filename} ---")


def setup_directories(dirs):
    """Creates directories, clearing them if they already exist."""
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)

def run_mumemto(folder_path, k=2, l=20, output='output'):
    """Runs mumemto on all fasta files within a folder."""
    # We use os.path.join to handle the wildcard safely
    input_pattern = os.path.join(folder_path, "*.fasta")
    
    # In some shells, subprocess needs shell=True to expand the '*' wildcard
    cmd = f"mumemto {input_pattern} -k {k} -l {l} -o {output}"
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running mumemto on {folder_path}: {e.stderr}")


def parse_mums_file(filepath, label):
    """
    Parses a .mums file.
    - length: 1st column
    - present_count: number of non-empty values in 2nd column
    """
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 2:
                continue
            
            # 1st column is the length of the MUM
            length = int(parts[0])
            
            # 2nd column contains comma-separated indices/values
            # We count only the non-empty entries
            presence_list = parts[1].split(',')
            present_count = sum(1 for x in presence_list if x.strip() != '')
            
            data.append({
                'Length': length,
                'Present_Count': present_count,
                'Dataset': label
            })
    return pd.DataFrame(data)

def calculate_n50(lengths):
    if len(lengths) == 0: return 0
    sorted_lengths = np.sort(lengths)[::-1]
    total_sum = np.sum(sorted_lengths)
    cumulative_sum = np.cumsum(sorted_lengths)
    return sorted_lengths[np.where(cumulative_sum >= total_sum / 2)[0][0]]


alphas = [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]
windows = [5, 8, 11]
seed = 10
n_genomes = 100
ordering = "/home/Users/rdd4/mft-analyses/Table1/orderings/8_110.txt"
mapping_table = "/home/Users/rdd4/mft-analyses/Table1/mappings/110.txt"
mft_dir = "/home/Users/rdd4/mft-tools"

for alpha in alphas:
    print(f"Simulating genomes with alpha={alpha}")
    # Step 1: Generate reference genome
    ref_genome = generate_random_dna(10000)
    
    # Step 2: Generate related genomes with mutations
    related_genomes = [mutate_sequence(ref_genome, sub_rate=alpha, indel_rate=0.00, seed=20 + i) for i in range(n_genomes-1)]
    
    # Step 3: Write genomes to FASTA files
    dir_name = f"/home/Users/rdd4/mft-analyses/Figure2/data/alpha_{alpha}"
    baseline_folder = os.path.join(dir_name, "nucleotide")
    setup_directories([dir_name, baseline_folder])
    
    fasta_file_locations = []
    
    for i, genome in enumerate([ref_genome] + related_genomes):
        fasta_out = os.path.join(dir_name, "nucleotide", f"genome_{i}.fasta")
        fasta_file_locations.append(fasta_out)
        write_fasta([genome], fasta_out)
            
        # Step 3: Generate MFT transformations 
    
    for w in windows:
        print(f"Transforming with w={w}")
        out_window_dir = os.path.join(dir_name, f'mft_w{w}')
        setup_directories([out_window_dir])
        for i, baseline_fasta in enumerate(fasta_file_locations):
            out_transfomed = os.path.join(out_window_dir, f"genome_{i}.fasta")
            subprocess.run([
                "cargo", "run", "--",
                "transform",
                "-w", str(w),
                "-m", mapping_table,
                "-b", ordering,
                "-g", baseline_fasta,
                "-o", out_transfomed,
            ], cwd=mft_dir, check=True)
        
        
        
        # Step 4: Run mumemto
        # run_mumemto(dir_name, k=2, l=window, output=os.path.join(dir_name, "output"))