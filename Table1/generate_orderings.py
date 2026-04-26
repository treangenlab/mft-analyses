import subprocess
import os
import glob

MFT_TOOLS_DIR  = os.path.expanduser("~/mft-tools")
OUTPUT_DIR     = os.path.expanduser("~/mft-analyses/Table1/orderings")
MAPPINGS_DIR   = os.path.expanduser("~/mft-analyses/Table1/mappings")

os.makedirs(OUTPUT_DIR, exist_ok=True)

mapping_files = sorted(glob.glob(os.path.join(MAPPINGS_DIR, "*.txt")))

for i in range(100):
    seed = i
    output_file = os.path.join(OUTPUT_DIR, f"{i}.txt")
    cmd = [
        "cargo", "run", "--",
        "define-order",
        "-k", "3",
        "-s", str(seed),
        "-o", output_file,
    ]
    print(f"[{i+1}/100] seed={seed} -> {output_file}")
    result = subprocess.run(cmd, cwd=MFT_TOOLS_DIR)
    if result.returncode != 0:
        print(f"  ERROR: define-order failed for iteration {i} (seed={seed})")
        continue


    for mpath in mapping_files:
        mbase = os.path.splitext(os.path.basename(mpath))[0]
        opt_out = os.path.join(OUTPUT_DIR, f"{i}_{mbase}.txt")
        opt_cmd = [
            "cargo", "run", "--",
            "optimize",
            "-k", "3",
            "-w", "5",
            "-m", mpath,
            "-b", output_file,
            "-o", opt_out,
            "-i", "2000",
        ]
        print(f"  optimizing with mapping {mbase} -> {opt_out}")
        opt_result = subprocess.run(opt_cmd, cwd=MFT_TOOLS_DIR)
        if opt_result.returncode != 0:
            print(f"  ERROR: optimize failed for iteration {i}, mapping {mbase}")
        
    
