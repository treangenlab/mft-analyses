import subprocess
import os
import csv
import glob

MFT_TOOLS_DIR = os.path.expanduser("~/mft-tools")
MAPPINGS_DIR  = os.path.expanduser("~/mft-analyses/Table3/mappings")
ORDERINGS_DIR = os.path.expanduser("~/mft-analyses/Table3/orderings")
EVALS_DIR     = os.path.expanduser("~/mft-analyses/Table3/evaluations")
OUTPUT_CSV    = os.path.expanduser("~/mft-analyses/Table3/results.csv")

NUKE_COLS = ["A->C","A->G","A->T","C->A","C->G","C->T",
             "G->A","G->C","G->T","T->A","T->C","T->G"]

os.makedirs(EVALS_DIR, exist_ok=True)

# ── 1. Run evaluations ────────────────────────────────────────────────────────

ordering_files = sorted(glob.glob(os.path.join(ORDERINGS_DIR, "*.txt")))
mapping_files = sorted(glob.glob(os.path.join(MAPPINGS_DIR, "*.txt")))

total = len(mapping_files) * len(ordering_files)
done  = 0

for mpath in mapping_files:
    mbase = os.path.splitext(os.path.basename(mpath))[0]
        
    for opath in ordering_files:
        obase = os.path.splitext(os.path.basename(opath))[0]
        out = os.path.join(EVALS_DIR, f"{obase}.txt")
        done += 1
        print(f"[{done}/{total}] {mbase} x {obase}")
        if os.path.exists(out):
            print("  (skipping — already exists)")
            continue
        cmd = [
            "cargo", "run", "--",
            "evaluate",
            "-k", "3",
            "-w", "5",
            "-m", mpath,
            "-b", opath,
            "-o", out,
        ]
        result = subprocess.run(cmd, cwd=MFT_TOOLS_DIR)
        if result.returncode != 0:
            print(f"  ERROR: cargo run failed for {mbase} x {obase}")

# ── 2. Parse evaluations into a single CSV ────────────────────────────────────

rows = []
for fpath in sorted(glob.glob(os.path.join(EVALS_DIR, "*.txt"))):
    fname = os.path.splitext(os.path.basename(fpath))[0]
    # filename is  <mapping>_<ordering>  — split on first underscore
    parts = fname.split("_", 1)
    mapping  = parts[0] if len(parts) > 1 else fname
    ordering = parts[1] if len(parts) > 1 else ""

    vals = {}
    with open(fpath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            key, value = line.split("\t", 1)
            vals[key] = value

    row = {"mapping": mapping, "ordering": ordering,
           "global_masking_rate": vals.get("global_masking_rate", ""),
           "entropy":             vals.get("entropy", "")}
    for col in NUKE_COLS:
        row[col] = vals.get(col, "")
    rows.append(row)

fieldnames = ["mapping", "ordering", "global_masking_rate", "entropy"] + NUKE_COLS

with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nWrote {len(rows)} rows to {OUTPUT_CSV}")
