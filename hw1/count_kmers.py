#!/usr/bin/env python3

import argparse
import json
from collections import defaultdict

def read_fasta(filename):
    sequences = {}
    current_id = None
    current_seq = []
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                if current_id:
                    sequences[current_id] = ''.join(current_seq)
                current_id = line[1:]  # убираем '>'
                current_seq = []
            else:
                current_seq.append(line)
        if current_id:
            sequences[current_id] = ''.join(current_seq)
    
    return sequences

def count_kmers(sequence, k=2):
    kmers = defaultdict(int)
    seq_len = len(sequence)
    
    for i in range(seq_len - k + 1):
        kmer = sequence[i:i+k]
        kmers[kmer] += 1
    
    return dict(kmers)

parser = argparse.ArgumentParser(description='Count k-mers in FASTA file')
parser.add_argument('--fa', required=True, help='Input FASTA file')
parser.add_argument('-k', type=int, default=4, help='k-mer length (default: 4)')
parser.add_argument('--out', default='cnts.json', help='Output JSON file (default: cnts.json)')
args = parser.parse_args()
sequences = read_fasta(args.fa)
   
results = {}
for seq_id, sequence in sequences.items():
    results[seq_id] = count_kmers(sequence, k=4)
   
with open('cnts.json', 'w') as f:
    json.dump(results, f, indent=2)


