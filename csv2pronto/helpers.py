"""Helper structures for the `csv2pronto` module."""

from datetime import datetime
import enum
import itertools
from urllib.parse import quote

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace._XSD import XSD


# Type definitions


Node = URIRef | BNode


# Null Objects


class NoneLiteral(Literal):
    """Class that represents the `Literal` of a None value."""

    def __bool__(self):
        return False

    def __len__(self):
        return 0


class NoneNode(BNode):
    """
    Class that represents a `Node` that is None.

    Instances of this class indicate the absence of knowledge.
    Triplets with this class as a subject or object should never be
    considered when building a knowledge graph.
    """

    def __bool__(self):
        return False

    def __len__(self):
        return 0


# Incrementals


def timestamp() -> str:
    "Returns the current timestamp as a str, leaving only the digits."
    return str(datetime.now().timestamp()).replace(".", "")


class Incremental(enum.Enum):
    """
    Enumeration of an `itertools.count`-like incremental for each class.
    """

    REAL_ESTATE = itertools.count()
    SPACE = itertools.count()
    LISTING = itertools.count()

    def fragment(self) -> str:
        """
        Return the fragment part of a URI, consisting of the class name
        in lowercase and the next value of the incremental.
        """
        return self.name.lower() + "_" + timestamp() + "_" + str(next(self.value))


# Wrappers considering None values


class SafeNamespace(Namespace):
    """Namespace that builds URIs with urllib.parse.quote()"""

    def term(self, name: str) -> URIRef:
        return super().term(quote(name))


class SafeGraph(Graph):
    """Graph that doesn't add None 'objects'."""

    def add(self, triple: tuple[Node, URIRef, Node | Literal]) -> None:
        if all(triple):
            super().add(triple)


class SafeLiteral(Literal):
    """Literal that returns a NoneLiteral if the value is None"""

    def __new__(cls, value, *args, **kwargs):
        if value is None:
            return NoneLiteral(value, *args)
        return super().__new__(cls, value, *args, **kwargs)


# Helper methods


def Boolean(value) -> SafeLiteral:
    "A `Literal` of type `XSD.boolean`"
    return SafeLiteral(value, datatype=XSD.boolean)


def DateTime(value) -> SafeLiteral:
    "A `Literal` of type `XSD.dateTime`"
    return SafeLiteral(value, datatype=XSD.dateTime)


def Double(value) -> SafeLiteral:
    "A `Literal` of type `XSD.double`"
    return SafeLiteral(value, datatype=XSD.double)


def Float(value) -> SafeLiteral:
    "A `Literal` of type `XSD.float`"
    return SafeLiteral(value, datatype=XSD.float)


def Integer(value) -> SafeLiteral:
    "A `Literal` of type `XSD.integer`"
    return SafeLiteral(value, datatype=XSD.integer)


def String(value) -> SafeLiteral:
    "A `Literal` of type `XSD.string`"
    return SafeLiteral(value, datatype=XSD.string)


def default_to_BNode(func):
    """
    Decorator that returns a `BNode` if the URI creation raises a
    `KeyError`.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return BNode()

    return wrapper


def default_to_NoneNode(func):
    """
    Decorator that returns a `NoneNode` if the URI creation raises a
    `KeyError`.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return NoneNode()

    return wrapper


def default_to_incremental(ns: Namespace, inc: Incremental):
    """
    Decorator that returns a URI with an incremental value if the URI
    creation raises a `KeyError`.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyError:
                return ns[inc.fragment()]

        return wrapper

    return decorator
