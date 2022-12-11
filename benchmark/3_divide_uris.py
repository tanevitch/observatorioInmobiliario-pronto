"""
Randomize the order of the URIs in the file and divide them into 2
files, one of positive duplicates, and one of negative duplicates.
"""


import csv
import random

with open("data/uris_duplicados.csv", "r") as f:
    dups = list(csv.reader(f))

random.shuffle(dups)

dups = [d[0].split(";") for d in dups]

positives = dups[: len(dups) // 2]
negatives = [random.choice(n) for n in dups[len(dups) // 2 :]]
del dups

positive_pairs = []
for p in positives:
    positive_pairs.extend(
        [[p[i], p[j]] for i in range(len(p)) for j in range(i + 1, len(p))]
    )


positives = [
    ["+"] + ids + [round(random.uniform(0.93, 0.98), 2)] for ids in positive_pairs
]
del positive_pairs

with open("data/positivos.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerows(positives)


with open("data/negativos.csv", "w") as f:
    writer = csv.writer(f)
    length = len(negatives)
    for i in range(length):
        id = negatives.pop()
        for negative_id in negatives:
            writer.writerow(
                ["-", id, negative_id, round(random.uniform(0.85, 0.98), 2)]
            )
        for positive_ids in positives:
            writer.writerow(
                [
                    "-",
                    id,
                    random.choice(positive_ids[1:-1]),
                    round(random.uniform(0.85, 0.98), 2),
                ]
            )
