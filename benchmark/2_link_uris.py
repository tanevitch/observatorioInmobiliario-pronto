"Take the matched IDs and create a file of matched URIs"


import csv
import sys


def create_uri(id: str, url: str) -> str:
    if "argenprop" in url:
        site = "site1"
    elif "mercadolibre" in url:
        site = "site2"
    else:
        site = "site3"

    return f"https://raw.githubusercontent.com/fdioguardi/pronto/main/ontology/pronto.owl#listing_{site}_{id}"



try:
    dups_file = sys.argv[1]
except:
    dups_file = "data/train.csv"

try:
    data_file = sys.argv[2]
except:
    data_file = "data/clean_data.csv"

try:
    new_file = sys.argv[3]
except:
    new_file = "data/uris_duplicados.csv"


with open(dups_file, "r") as dups, open(data_file, "r") as data, open(new_file, "w") as uris:

    reader_dups = csv.reader(dups)
    reader_data = csv.DictReader(data)

    id_url = {}
    for row in reader_data:
        id_url[row["listing_id"]] = row["url"]

    writer_uris = csv.writer(uris)

    for dup_row in reader_dups:
        if dup_row[1] != "Seguro es un duplicado":
            continue

        ids = []
        for id in filter(bool, map(lambda id: id.strip(), dup_row[0].split(";"))):
            ids.append(create_uri(id, id_url[id]))

        writer_uris.writerow([";".join(ids)])
