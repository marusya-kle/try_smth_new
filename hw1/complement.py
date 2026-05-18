#!/usr/bin/env python3

import sys

def reverse_complement(seq):
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
    return ''.join(complement[base] for base in seq.upper()[::-1])

def gc_content(seq):
    seq = seq.upper()
    gc_count = seq.count('G') + seq.count('C')
    return round(gc_count / len(seq), 3)

seq = sys.argv[1]

seq_rc = reverse_complement(seq)
gc = gc_content(seq)

print(seq_rc)
print(gc)
