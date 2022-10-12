from contextlib import suppress

from rdflib import BNode, Graph, IdentifiedNode, URIRef
from rdflib.namespace._DC import DC
from rdflib.namespace._FOAF import FOAF
from rdflib.namespace._RDF import RDF
from rdflib.namespace._RDFS import RDFS
from rdflib.namespace._SDO import SDO

from helpers import (
    AnyURI,
    Boolean,
    DateTime,
    Double,
    Float,
    Integer,
    SafeGraph,
    SafeNamespace,
    String,
    default_to_BNode
)

PR = SafeNamespace("https://raw.githubusercontent.com/fdioguardi/pronto/main/ontology/pronto.owl")
SIOC = SafeNamespace("http://rdfs.org/sioc/ns#")
GR = SafeNamespace("http://purl.org/goodrelations/v1#")
REC = SafeNamespace("https://w3id.org/rec/core/")


def create_graph(row: dict) -> Graph:
    """Return a graph `g` with the info on `row`."""

    g: Graph = SafeGraph()

    listing = add_listing(g, row)
    agent, account = add_agent(g, row)
    real_estate = add_real_estate(g, row)

    g.add((listing, SIOC.has_creator, account))
    g.add((account, SIOC.creator_of, listing))

    g.add((listing, SIOC.about, real_estate))

    g.add((real_estate, PR.managed_by, agent))
    g.add((agent, PR.manages, real_estate))

    return g


def add_listing(g: Graph, row: dict) -> IdentifiedNode:
    """Add listing to the graph `g` and return the listing's `IdentifiedNode`."""

    @default_to_BNode
    def _create_listing():
        return PR[f"{row['site']}_{row['listing_id']}_listing"]

    listing: IdentifiedNode = _create_listing()
    g.add((listing, RDF.type, PR.RealEstateListing))

    g.add((listing, SIOC.link, AnyURI(row.get("url"))))
    g.add((listing, GR.name, String(row.get("title"))))
    g.add((listing, GR.description, String(row.get("description"))))

    ###

    buisness_func = GR.Sell if row["transaction"] == "Venta" else GR.LeaseOut
    g.add((listing, GR.hasBuisnessFunction, buisness_func))

    ###

    site: IdentifiedNode = PR[row["site"]]
    g.add((listing, SIOC.has_space, site))
    g.add((site, SIOC.space_of, listing))

    ###

    g.add((listing, SIOC.read_at, DateTime(row.get("date_extracted"))))
    g.add((listing, DC.date, DateTime(row.get("date_published"))))
    g.add((listing, SIOC.id, String(row.get("listing_id"))))

    ###

    if row.get("price"):
        price: IdentifiedNode = add_price(g, row["price"], row["currency"], "BASE")
        g.add((listing, GR.hasPriceSpecification, price))

    if row.get("maintenance_fee"):
        expenses: IdentifiedNode = add_price(
            g,
            row.get("maintenance_fee", ""),
            row.get("maintenance_fee_currency", ""),
            "MAINTENANCE FEE",
        )

        g.add((listing, GR.hasPriceSpecification, expenses))

    ###

    return listing


def add_price(g: Graph, value: float, currency: str, p_type: str) -> IdentifiedNode:
    """Add price to the graph `g` and return the price's `IdentifiedNode`."""

    @default_to_BNode
    def _create_price():
        return PR[f"{value}_{currency}_{p_type}"]

    price: IdentifiedNode = _create_price()
    g.add((price, RDF.type, GR.UnitPriceSpecification))
    g.add((price, GR.hasCurrencyValue, Float(price)))
    g.add((price, GR.hasCurrency, String(currency)))
    g.add((price, GR.priceType, String(p_type)))

    return price


def add_agent(g: Graph, row: dict) -> tuple[IdentifiedNode, IdentifiedNode]:
    """
    Add real estate agent to the graph `g` and return a tuple with the
    `IdentifiedNode`s of the agent and its user account.
    """

    @default_to_BNode
    def _create_agent():
        return PR[row["advertiser_name"]]

    @default_to_BNode
    def _create_account():
        return PR[f"{row['site']}_{row['advertiser_id']}"]

    agent: IdentifiedNode = _create_agent()
    account: IdentifiedNode = _create_account()

    g.add((agent, RDF.type, FOAF.Agent))
    g.add((account, RDF.type, SIOC.UserAccount))

    g.add((account, SIOC.id, String(row["advertiser_id"])))
    g.add((account, SIOC.name, String(row["advertiser_name"])))
    g.add((agent, SIOC.account, account))
    g.add((account, SIOC.account_of, agent))

    return agent, account


def add_real_estate(g: Graph, row: dict) -> IdentifiedNode:
    """
    Add real estate to the graph `g` and return the real estate's
    `IdentifiedNode`.
    """

    real_estate: IdentifiedNode = PR[f"{row['site']}_{row['listing_id']}_real_estate"]
    space: IdentifiedNode = PR[f"{row['site']}_{row['listing_id']}_space"]

    g.add((real_estate, RDF.type, REC.RealEstate))
    g.add((space, RDF.type, REC.Space))

    g.add((real_estate, REC.includes, space))
    g.add((space, SDO.address, String(row["address"])))
    g.add((space, SDO.latitude, Double(row["latitude"])))
    g.add((space, SDO.longitude, Double(row["longitude"])))

    g.add((space, SDO.yearBuilt, Integer(row["year_built"])))

    g.add((space, PR.is_brand_new, Boolean(row["is_new_property"])))
    g.add((space, PR.is_finished, Boolean(row["is_finished"])))
    g.add((space, PR.is_studio_apartment, Boolean(row["is_studio_apartment"])))
    g.add((space, PR.luminosity, String(row["luminosity"])))
    g.add((space, PR.orientation, String(row["orientation"])))
    g.add((space, PR.disposition, String(row["disposition"])))
    g.add((space, PR.property_type, String(row["property_type"])))

    # add features
    for feature, value in row["features"].items():
        f: IdentifiedNode = PR[feature]
        g.add((f, RDF.type, PR.Feature))
        g.add((space, PR.has_feature, f))
        g.add((f, RDFS.label, String(feature)))
        g.add((f, PR.has_value, String(value)))

    # add surfaces
    for s in ["total", "covered", "uncovered", "land"]:
        with suppress(KeyError):
            g.add((space, PR.hasSizeSpecification, add_surface(g, row, s)))

    # add amount of rooms
    g.add((space, PR.has_amoun_of_rooms, Integer(row["room_amnt"])))
    rooms: dict[str, URIRef] = {
        "bath": REC.Bathroom,
        "garage": REC.Garage,
        "bed": REC.Bedroom,
        "toilette": REC.Toilet,
    }
    for room, room_class in rooms.items():
        add_room(g, space, row, room, room_class)

    # add regions
    neighborhood: IdentifiedNode = PR[
        f"{row['province']}_{row['district']}_{row['neighborhood']}"
    ]
    district: IdentifiedNode = PR[f"{row['province']}_{row['district']}"]
    province: IdentifiedNode = PR[f"{row['province']}"]

    g.add((neighborhood, RDF.type, REC.Region))
    g.add((district, RDF.type, REC.Region))
    g.add((province, RDF.type, REC.Region))

    g.add((neighborhood, RDFS.label, String(row["neighborhood"])))
    g.add((district, RDFS.label, String(row["district"])))
    g.add((province, RDFS.label, String(row["province"])))

    g.add((space, REC.located_in, neighborhood))
    g.add((neighborhood, REC.located_in, district))
    g.add((district, REC.located_in, province))

    g.add((neighborhood, REC.location_of, space))
    g.add((district, REC.location_of, neighborhood))
    g.add((province, REC.location_of, district))

    return real_estate


def add_surface(g: Graph, row: dict, s_type: str) -> IdentifiedNode:
    """Add surface to the graph `g` and return the surface's `IdentifiedNode`."""

    value = row[f"{s_type}_surface"] or row[f"reconstructed_{s_type}_surface"]
    unit = row[f"{s_type}_surface_unit"] or row[f"reconstructed_{s_type}_surface_unit"]

    surface: IdentifiedNode = PR[f"{value}_{unit}_{s_type}"]

    g.add((surface, RDF.type, PR.SizeSpecification))
    g.add((surface, PR.has_surface_value, Float(value)))
    g.add((surface, GR.has_unit_of_measurement, String(value)))
    g.add((surface, PR.surface_type, String(s_type)))

    return surface


def add_room(g: Graph, space: IdentifiedNode, row: dict, room: str, room_class: IdentifiedNode) -> None:
    """Add rooms to the graph `g`."""

    amnt = row[f"{room}_amnt"]
    if not amnt:
        return

    def _create_room():
        fragment = getattr(space, "fragment", None)
        if not fragment: return BNode()
        return PR[f"{fragment}_{room}_{i}"]

    for i in amnt:
        r: IdentifiedNode = _create_room()
        g.add((r, RDF.type, room_class))
        g.add((space, PR.has_part, r))
