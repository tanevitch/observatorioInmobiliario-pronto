"""
Randomize the order of the URIs in the file.
Create a file with matched uris.
Mutate the data file to have the info of every matched uri and a few
    non matched uris, removing data that would match with the latter.
"""


import csv
import random
import sys


try:
    dups_file = sys.argv[1]
except:
    dups_file = "data/uris_duplicados.csv"

try:
    data_file = sys.argv[2]
except:
    data_file = "data/data_file.csv"

try:
    new_file = sys.argv[3]
except:
    new_file = "data/positivos.csv"


with open(dups_file, "r") as f:
    dups = list(csv.reader(f))

random.shuffle(dups)

dups = [d[0].split(";") for d in dups]

matched_uris = dups[: len(dups) // 2]

# unmatched_uris = []
uris_to_remove = []
for uris in dups[len(dups) // 2 :]:
    selected = random.choice(uris)
    # unmatched_uris.append(selected)
    uris_to_remove.extend([u for u in uris if u != selected])

del dups

for u in uris_to_remove:
    print(u)

positive_pairs = []
for p in matched_uris:
    positive_pairs.extend(
        [[p[i], p[j]] for i in range(len(p)) for j in range(i + 1, len(p))]
    )


matched_uris = [
    # ["+"] + ids + [round(random.uniform(0.93, 0.98), 2)] for ids in positive_pairs
    ["+"] + ids + [0.0]
    for ids in positive_pairs
]
del positive_pairs

with open(new_file, "w") as f:
    writer = csv.writer(f)
    writer.writerows(matched_uris)


# with open("data/negativos.csv", "w") as f:
#     writer = csv.writer(f)
#     length = len(negatives)
#     for i in range(length):
#         id = negatives.pop()
#         for negative_id in negatives:
#             writer.writerow(
#                 ["-", id, negative_id, round(random.uniform(0.85, 0.98), 2)]
#             )
#         for positive_ids in positives:
#             writer.writerow(
#                 [
#                     "-",
#                     id,
#                     random.choice(positive_ids[1:-1]),
#                     round(random.uniform(0.85, 0.98), 2),
#                 ]
#             )
