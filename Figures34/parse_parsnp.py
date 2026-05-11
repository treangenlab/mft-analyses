import glob
import os
import re
import pandas as pd

RESULTS_ROOT = "/dodo/ab235/actual-final/measles"
RESULTS_ROOT = "/dodo/ab235/actual-final/adenovirus"
RESULTS_ROOT = "/dodo/ab235/actual-final/ebola"
RESULTS_ROOT = "/dodo/ab235/actual-final/covid"


datasets = ["nucleotide", "mft_w5", "mft_w8", "mft_w11"]


def parse_elapsed_seconds(time_str):
    """Convert h:mm:ss or m:ss.ss to total seconds."""
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return 0.0


def parse_time_log(path):
    """Return elapsed wall clock seconds from a /usr/bin/time -v log. Uses last match."""
    if not os.path.exists(path):
        return -1
    elapsed = None
    with open(path) as f:
        for line in f:
            m = re.search(r"Elapsed \(wall clock\) time.*?:\s+(\S+)", line)
            if m:
                elapsed = m.group(1)
    if elapsed is None:
        return -1
    return parse_elapsed_seconds(elapsed)


def parse_core_length(log_path):
    """Return the Total coverage percentage float from parsnpAligner.log."""
    if not os.path.exists(log_path):
        return 0.0
    with open(log_path) as f:
        for line in f:
            if "Total coverage among all sequences" in line:
                m = re.search(r"([\d.]+)%", line)
                if m:
                    return float(m.group(1))
    return 0.0


def parse_vcf_snps(vcf_path):
    """Return the number of variant records in a VCF (lines below the # header)."""
    if not os.path.exists(vcf_path):
        return 0
    count = 0
    with open(vcf_path) as f:
        for line in f:
            if not line.startswith("#"):
                count += 1
    return count


def parse_snps_length(mblocks_path):
    """Return the length of the first sequence in a fasta file."""
    if not os.path.exists(mblocks_path):
        return 0
    length = 0
    in_first = False
    with open(mblocks_path) as f:
        for line in f:
            if line.startswith(">"):
                if in_first:
                    break
                in_first = True
            elif in_first:
                length += len(line.strip())
    return length


def parse_fp_lcbs(fp_lcbs_path):
    """Return the number of FP LCBs filtered, or -1 if the file doesn't exist."""
    if not os.path.exists(fp_lcbs_path):
        return -1
    with open(fp_lcbs_path) as f:
        return int(f.read().strip())


XMFA_HEADER_RE = re.compile(r'^>\s*1:(\d+)-(\d+)\s')

def parse_xmfa_core_length(xmfa_path, ref_path):
    """Compute core coverage % from filtered XMFA vs reference FASTA length."""
    if not os.path.exists(xmfa_path) or not os.path.exists(ref_path):
        return 0.0
    total = 0
    with open(ref_path) as f:
        for line in f:
            if not line.startswith('>'):
                total += len(line.strip())
    aligned = 0
    with open(xmfa_path) as f:
        for line in f:
            m = XMFA_HEADER_RE.match(line)
            if m:
                aligned += int(m.group(2)) - int(m.group(1))
    return (aligned / total * 100) if total > 0 else 0.0


rows = []
folder_re = re.compile(r"^n_(\d+)(?:_rep(\d+))?$")

for folder in sorted(os.listdir(RESULTS_ROOT)):
    m = folder_re.match(folder)
    if not m:
        continue
    n_val  = int(m.group(1))
    rep    = int(m.group(2)) if m.group(2) else None
    folder_path = os.path.join(RESULTS_ROOT, folder)

    for ds in datasets:
        ds_dir         = os.path.join(folder_path, ds)
        time_log       = os.path.join(folder_path, f"{ds}_time.log")
        # aligner_log    = os.path.join(ds_dir, "log", "parsnpAligner.log")
        vcf_pre_path   = os.path.join(ds_dir, "parsnp.vcf")
        vcf_post_path  = os.path.join(ds_dir, "parsnp_filtered.vcf")
        xmfa_pre_path  = os.path.join(ds_dir, "parsnp.xmfa")
        xmfa_post_path = os.path.join(ds_dir, "parsnp_filtered.xmfa")
        fp_lcbs_path   = os.path.join(ds_dir, "fp_lcbs.txt")
        ref_hits       = glob.glob(os.path.join(ds_dir, "*.ref"))
        ref_path       = ref_hits[0] if ref_hits else ""

        time_s      = parse_time_log(time_log)
        core_pre    = parse_xmfa_core_length(xmfa_pre_path, ref_path)
        core_length = parse_xmfa_core_length(xmfa_post_path, ref_path)
        snps_pre    = parse_vcf_snps(vcf_pre_path)
        snps_length = parse_vcf_snps(vcf_post_path)
        fp_lcbs     = parse_fp_lcbs(fp_lcbs_path)

        rows.append({
            "dataset":     ds,
            "n":           n_val,
            "rep":         rep,
            "core_pre":    core_pre,
            "core_length": core_length,
            "snps_pre":    snps_pre,
            "snps_length": snps_length,
            "fp_lcbs":     fp_lcbs,
            "time_s":      time_s,
        })

    out_csv = os.path.join(folder_path, "parsnp_summary.csv")
    folder_rows = [r for r in rows if r["n"] == n_val and r["rep"] == rep]
    pd.DataFrame(folder_rows).to_csv(out_csv, index=False)
    print(f"Written: {out_csv}")

print(f"\nDone. {len(rows)} total rows across {len(rows) // len(datasets)} folders.")
