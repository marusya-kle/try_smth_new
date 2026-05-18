#!/usr/bin/env python3

import argparse

def reverse_complement(seq):
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
    return ''.join(complement[base] for base in seq.upper()[::-1])

def gc_content(seq):
    seq = seq.upper()
    gc_count = seq.count('G') + seq.count('C')
    return round(gc_count / len(seq), 3)

parser = argparse.ArgumentParser(description='')
parser.add_argument('--seq', required=True, help='')
args = parser.parse_args()

seq_rc = reverse_complement(args.seq)
gc = gc_content(args.seq)

seq_rc = reverse_complement(seq)
gc = gc_content(seq)

print(seq_rc)
print(gc)
