""" Convert a CSV file to an RDF graph following the Pronto ontology """

import argparse
import csv

import rdflib
from src.converter import create_graph
from tqdm import tqdm
from joblib import Parallel, delayed

def main() -> None:
    args: argparse.Namespace = parse_args()

    with open(args.source, "r", encoding="utf-8") as csv_file:
        graph: rdflib.Graph = rdflib.Graph()

        graph.parse(args.ontology)

        total_rows = sum(1 for _ in csv.reader(csv_file))
        csv_file.seek(0)
        graph = Parallel(n_jobs=-1, backend='multiprocessing')(delayed(create_graph)(row) for row,_ in zip(csv.DictReader(csv_file), tqdm(range(total_rows))))

    graph.serialize(args.destination, format=args.format)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "-s", "--source", help="CSV file to convert", required=True, type=str
    )
    parser.add_argument(
        "-d", "--destination", help="RDF file to write", required=True, type=str
    )

    parser.add_argument(
        "-o", "--ontology", help="Ontology to use", required=True, type=str
    )

    parser.add_argument(
        "-f", "--format", help="RDF format of the output", required=True, type=str
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
