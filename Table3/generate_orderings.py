import subprocess
import os
import glob
import multiprocessing

MFT_TOOLS_DIR   = os.path.expanduser("~/mft-tools")
OUTPUT_DIR      = os.path.expanduser("~/mft-analyses/Table3/orderings")
MAPPINGS_DIR    = os.path.expanduser("~/mft-analyses/Table3/mappings")
TRANSITIONS_DIR = os.path.expanduser("~/mft-analyses/Table3/transition_tables")

MAX_WORKERS = 10

os.makedirs(OUTPUT_DIR, exist_ok=True)

mapping_files            = sorted(glob.glob(os.path.join(MAPPINGS_DIR, "*.txt")))
transition_weights_files = sorted(glob.glob(os.path.join(TRANSITIONS_DIR, "*.txt")))


def run_define_order(i):
    output_file = os.path.join(OUTPUT_DIR, f"{i}.txt")
    cmd = [
        "cargo", "run", "--",
        "define-order",
        "-k", "3",
        "-s", str(i),
        "-o", output_file,
    ]
    print(f"[{i+1}/100] seed={i} -> {output_file}", flush=True)
    result = subprocess.run(cmd, cwd=MFT_TOOLS_DIR)
    if result.returncode != 0:
        print(f"  ERROR: define-order failed for seed={i}", flush=True)
        return None
    return i


def run_optimize(args):
    i, mpath, t_path = args
    tw_base = os.path.splitext(os.path.basename(t_path))[0]
    m_base  = os.path.splitext(os.path.basename(mpath))[0]
    output_file = os.path.join(OUTPUT_DIR, f"{i}.txt")
    opt_out = os.path.join(OUTPUT_DIR, f"{i}_{m_base}_{tw_base}.txt")
    if os.path.exists(opt_out):
        return
    opt_cmd = [
        "cargo", "run", "--",
        "optimize",
        "-k", "3",
        "-w", "5",
        "-m", mpath,
        "-t", t_path,
        "-b", output_file,
        "-o", opt_out,
        "-i", "2000",
    ]
    print(f"  [{i}] optimizing {m_base} x {tw_base} -> {opt_out}", flush=True)
    result = subprocess.run(opt_cmd, cwd=MFT_TOOLS_DIR)
    if result.returncode != 0:
        print(f"  ERROR: optimize failed for seed={i}, mapping={m_base}, tw={tw_base}", flush=True)


if __name__ == "__main__":
    # Phase 1: run all define-order commands in parallel
    with multiprocessing.Pool(processes=MAX_WORKERS) as pool:
        results = pool.map(run_define_order, range(100))

    successful_seeds = [r for r in results if r is not None]

    # Phase 2: run all optimize combos in parallel across successful seeds
    combos = [
        (i, mpath, t_path)
        for i in sorted(successful_seeds)
        for mpath in mapping_files
        for t_path in transition_weights_files
    ]

    with multiprocessing.Pool(processes=MAX_WORKERS) as pool:
        pool.map(run_optimize, combos)
