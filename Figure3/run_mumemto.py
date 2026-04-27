import subprocess
from pathlib import Path
import os

min_l = 20


def run_mumemto(folder_path, k=2, l=10, output='output'):
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
        

data_folder = '/home/Users/rdd4/mft-analyses/Figure3/data'

for parent in os.listdir(data_folder):
    parent_path = os.path.join(data_folder, parent)
    
    # Ensure it's a directory
    if os.path.isdir(parent_path):
        
        # 2. Loop through the 4 Subfolders
        for sub in os.listdir(parent_path):
            sub_path = os.path.join(parent_path, sub)
            
            if os.path.isdir(sub_path):
                # 3. Define output path: inside the subfolder, named after the subfolder
                # e.g., .../parent/sub1/sub1
                out_destination = os.path.join(parent_path, sub)
                
                # 4. Call your function
                run_mumemto(sub_path, k=2, l=min_l, output=out_destination)