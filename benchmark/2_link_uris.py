"Take the matched IDs and create a file of matched URIs"


import csv


def create_uri(id: str, url: str) -> str:
    if "argenprop" in url:
        site = "site1"
    elif "mercadolibre" in url:
        site = "site2"
    else:
        site = "site3"

    return f"https://raw.githubusercontent.com/fdioguardi/pronto/main/ontology/pronto.owl#listing_{site}_{id}"


with open("data/duplicados_seguros.csv", "r") as dups, open(
    "data/data.csv", "r"
) as data, open("data/uris_duplicados.csv", "w") as uris:

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
