""" Convert a CSV file to an RDF file following the Pronto ontology. """

# import multiprocessing

# import concurrent
# import concurrent.futures
import argparse
import csv
from io import TextIOWrapper
import logging

import rdflib

from converter import create_graph


def main() -> None:
    args: argparse.Namespace = parse_args()

    logging.basicConfig(
        level=args.verbose or args.very_verbose or logging.WARNING,
        format=f"%(asctime)s [%(module)s]: %(message)s",
        datefmt="%I:%M:%S %p",
    )

    with open(args.input, "r") as csv_file:
        graph: rdflib.Graph = rdflib.Graph()

        graph.parse(args.ontology)

        for row in progressBar(
            csv_file, prefix="Progress:", suffix="Complete", length=50
        ):
            graph += create_graph(row)

        # with multiprocessing.Pool() as pool:
        #     graphs = pool.map(create_graph, csv_reader)
        #     for g in graphs:
        #         graph += g

        # with concurrent.futures.ProcessPoolExecutor() as executor:
        #     graphs = executor.map(create_graph, csv_reader)
        #     for g in graphs:
        #         graph += g

    graph.serialize(args.output, format=args.format)


def progressBar(
    file: TextIOWrapper,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 1,
    length: int = 100,
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

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "-v", "--verbose", help="Verbose mode", action="store_const", const=logging.INFO
    )
    group.add_argument(
        "-vv",
        "--very-verbose",
        help="Very verbose mode",
        action="store_const",
        const=logging.DEBUG,
    )

    parser.add_argument("--input", help="CSV file to convert", required=True, type=str)
    parser.add_argument("--output", help="RDF file to write", required=True, type=str)
    # add ontology argument
    parser.add_argument("--ontology", help="Ontology to use", required=True, type=str)
    # argument to know where to store the output graph

    parser.add_argument("-f", "--format", help="RDF format", required=True, type=str)

    return parser.parse_args()


if __name__ == "__main__":
    main()
