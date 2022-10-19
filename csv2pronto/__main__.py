""" Convert a CSV file to an RDF graph following the Pronto ontology """

import argparse
import csv
from io import TextIOWrapper

import rdflib

from converter import create_graph


def main() -> None:
    args: argparse.Namespace = parse_args()

    with open(args.source, "r", encoding="utf-8") as csv_file:
        graph: rdflib.Graph = rdflib.Graph()

        graph.parse(args.ontology)

        for row in progressBar(csv_file):
            graph += create_graph(row)

    graph.serialize(args.destination, format=args.format)


def progressBar(
    file: TextIOWrapper,
    prefix: str = "Progress:",
    suffix: str = "Complete",
    decimals: int = 1,
    length: int = 50,
    fill: str = "█",
    printEnd: str = "\r",
):
    """
    Call in a loop to create terminal progress bar
    @params:
        file        - Required  : file object (TextIOWrapper)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """

    # Calculate the number of lines in the file
    total = sum(1 for _ in csv.DictReader(file))
    file.seek(0)
    csv_reader = csv.DictReader(file)

    # Progress Bar Printing Function
    def printProgressBar(iteration):
        percent = ("{0:." + str(decimals) + "f}").format(
            100 * (iteration / float(total))
        )
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + "-" * (length - filledLength)
        print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)

    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(csv_reader):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("-s", "--source", help="CSV file to convert", required=True, type=str)
    parser.add_argument("-d", "--destination", help="RDF file to write", required=True, type=str)
    # add ontology argument
    parser.add_argument("-o", "--ontology", help="Ontology to use", required=True, type=str)
    # argument to know where to store the output graph

    parser.add_argument("-f", "--format", help="RDF format of the output", required=True, type=str)

    return parser.parse_args()


if __name__ == "__main__":
    main()
