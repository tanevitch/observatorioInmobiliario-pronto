"""Module to convert dictionaries to RDF graphs."""

import ast
from contextlib import suppress
from datetime import datetime
import pandas as pd
import dateutil.parser as dateparser
from rdflib import BNode, Graph, URIRef
from rdflib.namespace import DC, FOAF, RDF, RDFS, SDO

from . import Node
from .faker.faker import Faker
from .incrementals.incrementals import Incremental
from .null_objects.factory import Boolean, DateTime, Double, Float, Integer, String
from .null_objects.null_objects import NoneNode
from .null_objects.safe_objects import SafeGraph, SafeNamespace
from .wrappers.wrappers import default_to_incremental, default_to_NoneNode

IO = SafeNamespace("http://www.semanticweb.org/luciana/ontologies/2024/8/inmontology#")
PR = SafeNamespace("https://raw.githubusercontent.com/fdioguardi/pronto/main/ontology/pronto.owl#")
SIOC = SafeNamespace("http://rdfs.org/sioc/ns#")
GR = SafeNamespace("http://purl.org/goodrelations/v1#")
REC = SafeNamespace("https://w3id.org/rec#")
TIME = SafeNamespace("http://www.w3.org/2006/time#")
BRICK = SafeNamespace("https://brickschema.org/schema/Brick#")


def create_graph_from_chunk(df: pd.DataFrame, graph, destination, format) -> Graph:
    """
    Writes a partial graph `g` with the info of a chunk of rows.

    Args:
        df (pd.DataFrame): a Pandas Dataframe with the info to add to `g`.
    """
    for i in range(len(df)):
        graph += create_graph(df.iloc[i].to_dict())
    graph.serialize(destination, format=format)


def create_graph(row: dict) -> Graph:
    """
    Return a graph `g` with the info on `row`.

    Args:
        row (dict): Dictionary with the info to add.
    """

    row = {k: v for k, v in row.items() if v != ""}
    row = Faker.anonymize(row)

    g: Graph = SafeGraph()

    listing = add_listing(g, row)
    agent, account = add_agent(g, row)
    real_estate = add_real_estate(g, row)

    g.add((listing, SIOC.has_creator, account))
    g.add((account, SIOC.creator_of, listing))
    g.add((listing, FOAF.maker, agent))
    g.add((agent, FOAF.made, listing))

    g.add((listing, SIOC.about, real_estate))

    return g


def add_listing(g: Graph, row: dict) -> Node:
    """Add listing to the graph `g` and return the listing's `Node`."""

    @default_to_incremental(PR, Incremental.LISTING)
    def _create_listing():
        return IO[f"listing_{row['site']}_{row['listing_id']}"]

    listing: Node = _create_listing()
    g.add((listing, RDF.type, PR.RealEstateListing))

    if row.get("url"):
        g.add((listing, SIOC.link, URIRef(row["url"])))
    g.add((listing, RDFS.label, String(row.get("title"))))
    g.add((listing, IO.descripcion, String(row.get("description")))) 

    ###

    if row.get("transaction"):
        buisness_func = (
            GR.Sell if row["transaction"].lower() == "venta" else GR.LeaseOut
        )
        g.add((listing, GR.hasBusinessFunction, buisness_func))

    site: Node = PR[row["site"]]
    g.add((site, RDF.type, SIOC.Site))
    g.add((listing, SIOC.has_space, site)) #TODO: cambiar has_space
    g.add((site, SIOC.space_of, listing)) #TODO: cambiar space_of

    g.add((listing, SIOC.id, String(row.get("listing_id"))))

    if row.get("date_extracted"):
        date = dateparser.parse(row["date_extracted"])
        g.add((listing, SIOC.read_at, DateTime(date)))

    if row.get("date_published"):
        date = dateparser.parse(row["date_published"])
        g.add((listing, DC.date, DateTime(date)))
        

    if row.get("price") and row.get("currency"):
        price: Node = add_price(g, row["price"], row["currency"], "BASE", dateparser.parse(row["date_extracted"]))
        g.add((listing, IO.hasFeature, price))

    if row.get("maintenance_fee") and row.get("maintenance_fee_currency"):
        expenses: Node = add_price(
            g,
            row.get("maintenance_fee", ""),
            row.get("maintenance_fee_currency", ""),
            "MAINTENANCE FEE",
            dateparser.parse(row["date_extracted"])
        )

        g.add((listing, IO.hasFeature, expenses))

    ###

    return listing


def add_price(g: Graph, value: float, currency: str, p_type: str, date: datetime|None) -> Node:
    """Add price to the graph `g` and return the price's `Node`."""

    priceValue: Node = BNode()
    featurePrice: Node = BNode()
    temporalFeaturePrice: Node = BNode()
    dateNode: Node = BNode()
    
    g.add((priceValue, RDF.type, GR.UnitPriceSpecification))
    g.add((priceValue, GR.hasCurrency, String(currency)))
    g.add((priceValue, GR.hasCurrencyValue, Float(value)))
    g.add((priceValue, GR.priceType, String(p_type)))

    g.add((temporalFeaturePrice, RDF.type, IO.TemporalValue))
    g.add((temporalFeaturePrice, IO.hasScraperValue, priceValue))

    g.add((dateNode, RDF.type, TIME.Instant))
    g.add((dateNode, TIME.inXSDDateTimeStamp, DateTime(date)))
    g.add((temporalFeaturePrice, IO.hasScraperTime, dateNode))

    g.add((featurePrice, RDF.type, IO.Precio))
    g.add((featurePrice, IO.hasDetail, temporalFeaturePrice))

    return featurePrice



def add_agent(g: Graph, row: dict) -> tuple[Node, Node]:
    """
    Add real estate agent to the graph `g` and return a tuple with the
    `Node`s of the agent and its user account.
    """

    @default_to_NoneNode
    def _create_agent():
        return IO[f"agent_{row['advertiser_name']}"]

    @default_to_NoneNode
    def _create_account():
        return IO[f"account_{row['site']}_{row['advertiser_id']}"]

    agent: Node = _create_agent()
    account: Node = _create_account()

    g.add((agent, RDF.type, FOAF.Agent))
    g.add((account, RDF.type, SIOC.UserAccount))

    g.add((account, SIOC.id, String(row.get("advertiser_id"))))
    g.add((account, SIOC.name, String(row.get("advertiser_name"))))
    g.add((agent, FOAF.account, account))
    g.add((account, SIOC.account_of, agent))

    return agent, account


def add_real_estate(g: Graph, row: dict) -> Node:
    """
    Add real estate to the graph `g` and return the real estate's
    `Node`.
    """   

    @default_to_incremental(PR, Incremental.REAL_ESTATE)
    def _create_real_estate():
        return IO[f"real_estate_{row['site']}_{row['listing_id']}"]

    @default_to_incremental(PR, Incremental.SPACE)
    def _create_space(s_type: str):
        return IO[f"space_{s_type}_{row['site']}_{row['listing_id']}"]

    real_estate: Node = _create_real_estate()
    land: Node = _create_space("land")  
    building: Node = _create_space("building")  
    
    g.add((real_estate, RDF.type, IO[str(row.get("property_type")).capitalize()])) #subclase de RealEstate
    if not (IO[str(row.get("property_type")).capitalize()], RDFS.subClassOf, REC.RealEstate) in g:
        g.add((IO[str(row.get("property_type")).capitalize()], RDFS.subClassOf, REC.RealEstate))

    g.add((land, RDF.type, REC.Site))
    g.add((building, RDF.type, REC.Building))

    #-----
    point: Node = BNode()
    g.add((point, RDF.type, REC.Point))
    g.add((land, REC.geometry, point)) ##tiene uno que se llama point también, no sé
    g.add((point, REC.coordinates, String(f"[{row.get('latitude')},{row.get('longitude')}]")))
    #-----


    district: Node = _create_district(row["district"], row["province"])
    province: Node = _create_province(row["province"])
    
    barrio= None
    if row.get("neighborhood"):
        barrio= str(row["neighborhood"])
    elif row.get("barrio"):
        barrio= str(row["barrio"])
    
    neighborhood =None
    if barrio:
        neighborhood : Node = _create_neighborhood(province, district, barrio)
        g.add((neighborhood, RDF.type, IO.Neighborhood))
        g.add((neighborhood, RDFS.label, String(barrio)))
        g.add((neighborhood, REC.locatedIn, district))

    g.add((district, RDF.type, IO.City))
    g.add((district, RDFS.label, String(row.get("district"))))
    
    g.add((province, RDF.type, IO.Province))
    g.add((province, RDFS.label, String(row.get("province"))))

    if row.get("address"):
        add_address(g, real_estate, IO.hasScraperValue, IO.hasScraperTime, row.get("address"), neighborhood, district, province, dateparser.parse(row.get("date_extracted")))

    elif row.get("direccion"):
        add_address(g, real_estate, IO.hasAVEValue, IO.hasAVETime, row.get("direccion"), neighborhood, district, province, dateparser.parse('2024-12-06'))


        

    
    g.add((real_estate, REC.includes, land))
    g.add((real_estate, REC.includes, building))
    g.add((land, BRICK.hasPart, building))


    # g.add((real_estate, REC.locatedIn, district))
    # g.add((real_estate, REC.locatedIn, province))
    

    g.add((district, REC.locatedIn, province))
    #---

    # if row.get("year_built"):
    #     g.add((space, SDO.yearBuilt, Integer(int(float(row.get("year_built", 0))))))

    # property_mapping = {
    #     "is_new_property": PR.is_brand_new,
    #     "is_finished": PR.is_finished,
    #     "is_studio_apartment": PR.is_studio_apartment,
    # }

    # for name, p in property_mapping.items():
    #     g.add((space, p, Boolean(None if row.get(name) == "" else row.get(name))))

    # g.add((space, PR.luminosity, String(row.get("luminosity"))))
    # g.add((space, PR.orientation, String(row.get("orientation"))))
    # g.add((space, PR.disposition, String(row.get("disposition"))))

    # add features to LAND
    for s in ["esquina", "pileta", "loteo_ph",  "indiviso", "irregular"]:
        with suppress(KeyError):
            if row[s] == "True":
                value = row[s] == "True"
            else:
                value = row[s]

            if value:
                add_feature(g, land, s, value, dateparser.parse('2024-12-06'))
    
    #add features to BUILDING
    for s in ["es_monetizable", "a_demoler"]:
        with suppress(KeyError):
            if row[s] == "True":
                value = row[s] == "True"
            else:
                value = row[s]

            if value:
                add_feature(g, building, s, value, dateparser.parse('2024-12-06'))

    #add features to REAL ESTATE
    for s in ["es_multioferta", "preventa", "posesion"]:
        with suppress(KeyError):
            if row[s] == "True":
                value = row[s] == "True"
            else:
                value = row[s]

            if value:
                add_feature(g, real_estate, s, value, dateparser.parse('2024-12-06'))

        

    # features: dict = ast.literal_eval(row.get("features") or "{}")
    # for feature, value in features.items():
    #     add_feature(g, real_estate, feature, value, dateparser.parse(row.get("date_extracted")))
    
    # add surfaces
    for s in ["total", "covered", "uncovered", "land"]:
        with suppress(KeyError):
            value = row[f"{s}_surface"] or row[f"reconstructed_{s}_surface"]
            unit = row[f"{s}_surface_unit"] or row[f"reconstructed_{s}_surface_unit"]

            if value and unit:
                add_surface(g, land, value, unit, s)

    # add amount of rooms
    g.add((building, PR.has_number_of_rooms, Integer(row.get("room_amnt"))))
    rooms: dict[str, Node] = {
        "bath": REC.Bathroom,
        "garage": REC.Garage,
        "bed": REC.Bedroom,
        "toilette": REC.Toilet,
    }
    for room, room_class in rooms.items():
        add_room(g, building, row, room, room_class)
   
    return real_estate

@default_to_NoneNode
def _create_district(province:str, district:str):
    province =province.replace(" ", "_")
    district= district.replace(" ", "_")
    if (district == "Bs.As._Costa_Atlántica"):
        print(IO[f"district_{province}_{district}"].encode())
    return IO[f"district_{province}_{district}"]

@default_to_NoneNode
def _create_province(province:str):
    province= province.replace(" ", "_")
    return IO[f"province_{province}"]

@default_to_NoneNode
def _create_neighborhood(province:URIRef, district:URIRef, neighborhood:str):
    neighborhood= neighborhood.replace(" ", "_")
    
    return IO[
        f"neiborhood_{province.fragment}_{district.fragment}_{neighborhood}"
    ]


def add_address(g: Graph, real_estate: Node, hasValue: URIRef, hasTime:URIRef,address: str, neighborhood: URIRef|None, district: Node, province: Node, date: datetime | None) -> Node:
    """Add address to the graph g and return the address's Node."""
    addressValue: Node = BNode()
    featureAddress: Node = create_feature(real_estate, "address")
    temporalFeatureAddress: Node = BNode() # no seria bNode¿?
    dateNode: Node = BNode()

    
    g.add((addressValue, RDF.type, IO.PostalAddress))
    g.add((addressValue, IO.address, String(address)))
    if neighborhood:
        g.add((addressValue, IO.neighborhood, neighborhood))
    g.add((addressValue, IO.city, district))
    g.add((addressValue, IO.province, province))


    g.add((temporalFeatureAddress, RDF.type, IO.TemporalValue))
    g.add((temporalFeatureAddress, hasValue, addressValue))

    g.add((dateNode, RDF.type, TIME.Instant))
    g.add((dateNode, TIME.inXSDDateTimeStamp, DateTime(date)))
    g.add((temporalFeatureAddress, hasTime, dateNode))

    g.add((featureAddress, RDF.type, IO.Direccion))
    g.add((featureAddress, IO.hasDetail, temporalFeatureAddress))

    g.add((real_estate, IO.hasFeature, featureAddress))

    return addressValue


def create_feature(subject: Node, feature: str) -> Node:
    return IO[f"feature_{feature}_{subject.fragment}"]


def add_feature(g: Graph, space: Node, featureName :str, value, date: datetime|None) -> Node: 
    featureValue: Node = BNode()
    feature: Node = create_feature(space, featureName)
    temporalFeature: Node = BNode() # no seria bNode¿?
    dateNode: Node = BNode() 
    
    g.add((featureValue, RDF.type, RDFS.Literal)) # ⸘Literal‽
    if (type(value)==int):
        g.add((featureValue, RDFS.label, Integer(value)))
    if (type(value)==float):
        g.add((featureValue, RDFS.label, Double(value)))
    if (type(value)==str):
        g.add((featureValue, RDFS.label, String(value)))
    if (type(value)==bool):
        g.add((featureValue, RDFS.label, Boolean(value)))
    
    g.add((temporalFeature, RDF.type, IO.TemporalValue))
    g.add((temporalFeature, IO.hasAVEValue, featureValue))

    g.add((dateNode, RDF.type, TIME.Instant))
    g.add((dateNode, TIME.inXSDDateTimeStamp, DateTime(date)))
    g.add((temporalFeature, IO.hasAVETime, dateNode))
    
    g.add((feature, RDF.type, IO[featureName.capitalize()]))
    g.add((feature, IO.hasDetail, temporalFeature))

    if not (IO[featureName.capitalize()], RDFS.subClassOf, IO.Feature) in g:
        g.add((IO[featureName.capitalize()], RDFS.subClassOf, IO.Feature))


    g.add((space, IO.hasFeature, feature))

    return featureValue

def add_surface(g: Graph, space: Node, value: float, unit: str, s_type: str) -> Node:
    """Add surface to the graph g and return the surface's Node."""
    surfaceValue: Node = BNode()
    featureSurface: Node = create_feature(space, s_type)
    temporalFeatureSurface: Node = BNode() # no seria bNode¿?

    g.add((surfaceValue, RDF.type, PR.SizeSpecification))
    g.add((surfaceValue, GR.hasValue, Float(value)))
    g.add((surfaceValue, GR.hasUnitOfMeasurement, String(unit)))
    g.add((surfaceValue, PR.size_type, String(s_type)))
    
    g.add((temporalFeatureSurface, RDF.type, IO.TemporalValue))
    g.add((temporalFeatureSurface, IO.hasScraperValue, surfaceValue))
    
    g.add((featureSurface, RDF.type, IO.Superficie))
    g.add((featureSurface, IO.hasDetail, temporalFeatureSurface))

    g.add((space, IO.hasFeature, featureSurface))

    return surfaceValue

def add_room(g: Graph, space: Node, row: dict, room: str, room_class: Node) -> None:
    """Add rooms to the graph `g`."""

    amnt = row.get(f"{room}_amnt")
    if not amnt:
        return

    if not amnt.isdigit():
        return
    amnt = int(amnt)

    def _create_room() -> Node:
        fragment = getattr(space, "fragment", None)
        if not fragment:
            return BNode()
        return IO[f"{fragment}_{room}_{i}"]

    for i in range(amnt):
        r: Node = _create_room()
        g.add((r, RDF.type, room_class))
        g.add((space, BRICK.hasPart, r))
