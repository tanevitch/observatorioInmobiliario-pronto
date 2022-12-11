"Take the original CSV and remove every non-labeled row."


import csv

duplicated_ids = dict()

with open("data/duplicados_seguros.csv", "r") as f:
    reader = csv.reader(f)
    for row in reader:
        if row[1] != "Seguro es un duplicado":
            continue

        for id in filter(bool, map(lambda id: id.strip(), row[0].split(";"))):
            duplicated_ids[id] = True

with open("data/data.csv", "r") as old, open("data/clean_data.csv", "w") as new:
    reader = csv.DictReader(old)
    writer = csv.DictWriter(new, fieldnames=reader.fieldnames)
    writer.writeheader()
    for row in reader:
        if duplicated_ids.get(row["listing_id"], False):
            writer.writerow(row)
