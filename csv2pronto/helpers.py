from urllib.parse import quote

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace._XSD import XSD

Node = URIRef | BNode

class SafeNamespace(Namespace):
    """Namespace that builds URIs with urllib.parse.quote()"""

    def term(self, name: str) -> URIRef:
        return super().term(quote(name))


class SafeGraph(Graph):
    """Graph that doesn't add None 'objects'."""

    def add(self, triple: tuple[Node, URIRef, Node | Literal]) -> None:
        if all(triple):
            super().add(triple)


class NoneLiteral(Literal):
    """Class that represents the `Literal` of a None value."""

    def __bool__(self):
        return False

    def __len__(self):
        return 0


class SafeLiteral(Literal):
    """Literal that returns a NoneLiteral if the value is None"""

    def __new__(cls, value, *args, **kwargs):
        if value is None:
            return NoneLiteral(value, *args)
        return super().__new__(cls, value, *args, **kwargs)


class AnyURI(SafeLiteral):
    """A `Literal` of type `XSD.anyURI`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.anyURI)


class Boolean(SafeLiteral):
    """A `Literal` of type `XSD.boolean`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.boolean)


class DateTime(SafeLiteral):
    """A `Literal` of type `XSD.dateTime`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.dateTime)


class Double(SafeLiteral):
    """A `Literal` of type `XSD.double`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.double)


class Float(SafeLiteral):
    """A `Literal` of type `XSD.float`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.float)


class Integer(SafeLiteral):
    """A `Literal` of type `XSD.integer`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.integer)


class String(SafeLiteral):
    """A `Literal` of type `XSD.string`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.string)


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
