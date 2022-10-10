""" Convert a CSV file to an RDF file following the Pronto ontology. """

import argparse
import csv
import logging

import rdflib

from converter import create_graph


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


def main() -> None:
    args: argparse.Namespace = parse_args()

    logging.basicConfig(
        level=args.verbose or args.very_verbose or logging.WARNING,
        format=f"%(asctime)s [%(module)s]: %(message)s",
        datefmt="%I:%M:%S %p",
    )

    with open(args.input, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file)

        graph: rdflib.Graph = rdflib.Graph()

        graph.parse(args.ontology)

        for row in csv_reader:
            graph += create_graph(row)

    graph.serialize(args.output, format=args.format)


if __name__ == "__main__":
    main()
