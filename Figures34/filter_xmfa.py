#!/usr/bin/env python3
import re
import argparse

HEADER_RE = re.compile(r'^>\s*(\d+):(\d+)-(\d+)\s')


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_xmfa(input_path):
    """Return (preamble_lines, clusters).

    Each cluster is {'lines': [...], 'seq_data': {seq_idx: (start, end)}}.
    """
    preamble = []
    clusters = []
    current_lines = []
    seq_data = {}

    with open(input_path) as f:
        for line in f:
            if not current_lines and line.startswith('#'):
                preamble.append(line)
                continue

            if line.strip() == '=':
                if current_lines and seq_data:
                    clusters.append({'lines': current_lines, 'seq_data': seq_data})
                current_lines = []
                seq_data = {}
                continue

            m = HEADER_RE.match(line)
            if m:
                seq_idx = int(m.group(1))
                seq_data[seq_idx] = (int(m.group(2)), int(m.group(3)))

            current_lines.append(line)

    if current_lines and seq_data:
        clusters.append({'lines': current_lines, 'seq_data': seq_data})

    return preamble, clusters


# ---------------------------------------------------------------------------
# Greedy collinear filtering
# ---------------------------------------------------------------------------

def cluster_length(cluster):
    """Total alignment length summed across all sequences."""
    start, end = cluster['seq_data'][1]
    length =  end-start
    print(length)
    return length

def _sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


def is_collinear_insertion(accepted, cand_seq_data, ins_pos):
    """
    Return True if inserting the candidate at ins_pos in the ref-sorted
    accepted list keeps all sequences monotonically ordered.

    For each sequence i present in the candidate:
      - If there are accepted neighbours on both sides, the candidate's
        start must lie strictly between them (in either direction).
      - If there is only one side with enough history to determine direction,
        enforce that direction.
    """
    for i, (cand_start, _) in cand_seq_data.items():
        before = [ac['seq_data'][i][0] for ac in accepted[:ins_pos] if i in ac['seq_data']]
        after  = [ac['seq_data'][i][0] for ac in accepted[ins_pos:] if i in ac['seq_data']]

        if before and after:
            lo, hi = before[-1], after[0]
            if not (lo < cand_start < hi or lo > cand_start > hi):
                return False

        elif before and len(before) >= 2:
            direction = _sign(before[-1] - before[-2])
            if direction > 0 and cand_start <= before[-1]:
                return False
            if direction < 0 and cand_start >= before[-1]:
                return False

        elif after and len(after) >= 2:
            direction = _sign(after[1] - after[0])
            if direction > 0 and cand_start >= after[0]:
                return False
            if direction < 0 and cand_start <= after[0]:
                return False

    return True


MIN_CLUSTER_LENGTH = 50


def greedy_collinear_filter(clusters, min_length=MIN_CLUSTER_LENGTH):
    """
    Sort clusters by total alignment length (descending), then greedily
    accept each cluster if it keeps all sequence positions collinear with
    the already-accepted set.  Clusters shorter than min_length nucleotides
    are dropped before the greedy pass.

    Returns accepted clusters in reference (seq 1) start order.
    """
    sorted_clusters = sorted(
        (c for c in clusters if cluster_length(c) >= min_length),
        key=cluster_length, reverse=True,
    )
    accepted = []  # kept sorted by seq-1 start throughout

    for cand in sorted_clusters:
        ref_start = cand['seq_data'].get(1, (0, 0))[0]

        # Find insertion position by ref start
        ins_pos = sum(1 for ac in accepted if ac['seq_data'].get(1, (0, 0))[0] < ref_start)

        if is_collinear_insertion(accepted, cand['seq_data'], ins_pos):
            accepted.insert(ins_pos, cand)
        else:
            print("Rejected cluster")

    return accepted


# I/O
def write_xmfa(output_path, preamble, clusters):
    with open(output_path, 'w') as out:
        for line in preamble:
            out.write(line)
        for cluster in clusters:
            for line in cluster['lines']:
                out.write(line)
            out.write('=\n')


def filter_xmfa(input_path, output_path, min_length=MIN_CLUSTER_LENGTH):
    preamble, clusters = parse_xmfa(input_path)
    accepted = greedy_collinear_filter(clusters, min_length=min_length)
    write_xmfa(output_path, preamble, accepted)
    removed = len(clusters) - len(accepted)
    print(f"Kept {len(accepted)} / {len(clusters)} clusters (removed {removed})")
    return removed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Filter XMFA clusters to the longest collinear subset across all sequences."
    )
    parser.add_argument('input',  help="Input XMFA file")
    parser.add_argument('output', help="Output XMFA file")
    parser.add_argument('--min-length', type=int, default=MIN_CLUSTER_LENGTH,
                        help=f"Minimum cluster length in nucleotides (default: {MIN_CLUSTER_LENGTH})")
    args = parser.parse_args()
    filter_xmfa(args.input, args.output, min_length=args.min_length)
