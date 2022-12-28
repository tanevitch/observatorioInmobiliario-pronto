"Take the original CSV and remove every non-labeled row."


import csv
import sys

try:
    dups_file = sys.argv[1]
except:
    dups_file = "data/train.csv"

try:
    data_file = sys.argv[2]
except:
    data_file = "data/data.csv"

try:
    new_file = sys.argv[3]
except:
    new_file = "data/clean_data.csv"




def create_uri(id: str, url: str) -> str:
    if "argenprop" in url:
        site = "site1"
    elif "mercadolibre" in url:
        site = "site2"
    else:
        site = "site3"

    return f"https://raw.githubusercontent.com/fdioguardi/pronto/main/ontology/pronto.owl#listing_{site}_{id}"

duplicated_ids = dict()

with open(dups_file, "r") as f:
    reader = csv.reader(f)
    for row in reader:
        if row[1] != "Seguro es un duplicado":
            continue

        for id in filter(bool, map(lambda id: id.strip(), row[0].split(";"))):
            duplicated_ids[id] = True

with open(data_file, "r") as old, open(new_file, "w") as new:
    reader = csv.DictReader(old)
    writer = csv.DictWriter(new, fieldnames=sorted(reader.fieldnames+["uri"]))
    writer.writeheader()
    for row in reader:
        if duplicated_ids.get(row["listing_id"], False):
            row["uri"] = create_uri(row["listing_id"], row["url"])
            writer.writerow(row)
