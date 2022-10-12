from collections.abc import Callable
from urllib.parse import quote

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace._XSD import XSD


class SafeNamespace(Namespace):
    """Namespace that builds URIs with urllib.parse.quote()"""

    def term(self, name: str) -> URIRef:
        return super().term(quote(name))


class NoneLiteral(Literal):
    """Class that represents a None value as a Literal."""

    def __bool__(self):
        return False

    def __len__(self):
        return 0


class SafeGraph(Graph):
    """Graph that doesn't add None values."""

    def add(self, triple: tuple[URIRef | BNode, URIRef, URIRef | Literal]) -> None:
        if not triple[2]:
            return
        super().add(triple)


class SafeLiteral(Literal):
    """Literal that returns a NoneLiteral if the value is None"""

    def __new__(cls, value, datatype=None, lang=None, normalize=True):
        if value is None:
            return NoneLiteral(value, datatype, lang, normalize)
        return super().__new__(cls, value, datatype, lang, normalize)


class AnyURI(Literal):
    """A `Literal` of type `XSD.anyURI`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.anyURI)


class Boolean(Literal):
    """A `Literal` of type `XSD.boolean`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.boolean)


class DateTime(Literal):
    """A `Literal` of type `XSD.dateTime`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.dateTime)


class Double(Literal):
    """A `Literal` of type `XSD.double`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.double)


class Float(Literal):
    """A `Literal` of type `XSD.float`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.float)


class Integer(Literal):
    """A `Literal` of type `XSD.integer`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.integer)


class String(Literal):
    """A `Literal` of type `XSD.string`."""

    def __new__(cls, value):
        return super().__new__(cls, value, datatype=XSD.string)

def default_to_BNode(func):
    """
    Decorator that returns a BNode if the URI creation fails by a
    KeyError.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return BNode()
    return wrapper
