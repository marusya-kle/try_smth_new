seq = input()
seq_r = seq[::-1]


dict = {"A": "T", "T": "A", "C": "G", "G": "C"}
seq_rc = ''
for i in seq_r:
  seq_rc += (dict[i])
 
from collections import Counter
gc = Counter(seq)
GC = round((int(gc["G"])+int(gc["C"]))/len(seq), 3)

print(seq_rc)
print(GC)
