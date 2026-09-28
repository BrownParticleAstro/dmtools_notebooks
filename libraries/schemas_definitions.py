## Description: This file contains the schemas for the node operations
##              for the DMTools application. The schemas are used to validate
##              the data that is passed to the node operations functions.

##              Schema validation should only happen when a node is created or updated
from datetime import datetime, timezone
from quart import session


def get_iso_now() -> str:
    """Return current UTC time as ISO8601 string with milliseconds and 'Z' suffix, e.g. '2021-01-01T00:00:00.000Z'."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def get_default_record(node_type):

    print("get_default_record -- node_type >>>", node_type)
    now_iso = get_iso_now()

    get_default_record = {"id": -1, "type": node_type,"created": now_iso, "updated": now_iso}
    
    return get_default_record

def get_default_properties(node_type):

    print("get_default_properties-- node_type >>>", node_type)
    now_iso = get_iso_now()

    default_properties = create_default_json(node_type)
    
    return  default_properties

async def make_default_display_data():
    now_iso = get_iso_now()

    plot_properties_default = create_default_json('Plot')
    display_properties_default = create_default_json('Display')
    data_properties_default = create_default_json('Data')

    default_data_dict = {
        "record": {
            "id": -1,
            "type": "Data",
            "created": now_iso,
            "updated": now_iso
        },
        "properties": data_properties_default
    }

    default_display_dict = {
        "record": {
            "id": -1,
            "type": "Display",
            "created": now_iso,
            "updated": now_iso
        },
        "properties": display_properties_default,
        "data": [default_data_dict]
    }

    result_dict = {
        "plot_node": {
            "record": {
                "id": -1,
                "type": "Plot",
                "created": now_iso,
                "updated": now_iso
            },
            "properties": plot_properties_default
        },
        "display_data": [default_display_dict]
    }

    return result_dict



def get_node_schema(node_type):
    print("get_node_schema -- node_type >>>", node_type)
    if node_type == "Data":
        return fn_data_schema()
    elif node_type == "Display":
        return fn_display_schema()
    elif node_type == "Plot":
        return fn_plot_schema()
    else:
        return None


def fn_data_schema():

    valid_years_list = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
    2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
    2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029]

    valid_experiments_list = [
                        "CDMS I (SUF)", "CDMS II (Soudan)", "SuperCDMS", "LUX", "XENON10", "XENON100", "XENON1T", "ZEPLIN I", "ZEPLIN II", "ZEPLIN III", "ZEPLIN IV", "COSME", "CUORICINO", "DAMA", "KIMS DMRC", "ELEGANT V", "Edelweiss", "GEDEON", "Genius", "Genino", "Heidelberg", "IGEX", "KIMS", "MIBETA", "Modane NaI", "NAIAD", "PICASSO", "ROSEBUD", "SIMPLE", "Saclay", "SuperK", "TOKYO", "UKDMC", "WARP", "Theory", "Heidelberg-Moscow", "Cuore", "DAMA Xe", "TEXONO", "XMASS", "IceCube", "DMTPC", "DEAP CLEAN", "DAMA/LIBRA", "CoGeNT", "COUPP", "LUX-ZEPLIN", "Fermi", "DarkSide", "DAMIC", "EURECA", "DEAP-3600", "PICO", "PandaX", "LHC", "DRIFT", "GAMBIT", "CDEX-10", "NEWS-G", "XENONnT", "CRESST"
                    ]

    binary_list = [0,1]

    spin_dependency_list = ["All", "SD", "SI"]

    result_type_list = ["Th", "Proj", "Exp"]

    # Define the schema for `properties`
    data_schema = {
        "type": "object",
        "properties": {
            "raw": {
                "type": "string",
                "default": "[[['0','0'],['0','1'],['1','1'],['1','0'],['0','0']]]"
            },
            "open": {
                "type": "integer",
                "enum": binary_list,
                "default": 0
            },
            "year": {
                "type": "integer",
                "enum": valid_years_list,
                "default": 2000
            },
            "label": {
                "type": "string",
                "default": "label"
            },
            "public": {
                "type": "integer",
                "enum": binary_list,
                "default": 0
            },
            "rating": {
                "type": "integer",
                "default": 0
            },
            "values": {
                "type": "array",
                "default": [[['0','0'],['0','1'],['1','1'],['1','0'],['0','0']]]
            },
            "xUnits": {
                "type": "string",
                "default": "GeV/c^2"
            },
            "yUnits": {
                "type": "string",
                "default": "cm2"
            },
            "comment": {
                "type": "string",
                "default": "comment"
            },
            "dateEnd": {
                "type": [
                    "string",
                    "null"
                ],
                "default": None
            },
            "official": {
                "type": "integer",
                "enum": binary_list,
                "default": 0
            },
            "xRescale": {
                "type": "string",
                "default": "1"
            },
            "yRescale": {
                "type": "string",
                "default": "1"
            },
            "dateStart": {
                "type": [
                    "string",
                    "null"
                ],
                "default": None
            },
            "reference": {
                "type": "string",
                "default": "reference"
            },
            "experiment": {
                "type": "string",
                "enum": valid_experiments_list,
                "default": "Experiment"
            },
            "resultType": {
                "type": "string",
                "enum": result_type_list,
                "default": "Th"
            },
            "greatestHit": {
                "type": "integer",
                "enum": binary_list,
                "default": 0
            },
            "label_short": {
                "type": "string",
                "default": "label"
            },
            "dateOfficial": {
                "type": [
                    "string",
                    "null"
                ],
                "default": None
            },
            "defaultColor": {
                "type": "string",
                "default": "black"
            },
            "defaultStyle": {
                "type": "string",
                "default": "line"
            },
            "spinDependency": {
                "type": "string",
                "enum": spin_dependency_list,
                "default": "SD"
            },
            "measurementType": {
                "type": "string",
                "default": "Unknown"
            },
            "dateAnnouncement": {
                "type": [
                    "string",
                    "null"
                ],
                "default": None
            },
            "hepUrl": {
                "type": "string",
                "format": "uri",    # optional, but recommended for URLs
                "default": "https://www.hepdata.net/record/show/hepdata.123456"
            }
        },
        "required": ["raw",
                    "open",
                    "year",
                    "label",
                    "public",
                    "xUnits",
                    "yUnits",
                    "comment",
                    "official",
                    "xRescale",
                    "yRescale",
                    "reference",
                    "experiment",
                    "resultType",
                    "spinDependency",
                    "measurementType",
                    "dateAnnouncement"
                ],
        "additionalProperties": False
    }


    return data_schema

def fn_display_schema():

    color_list = ["k", "r", "g", "b", "y", "m", "c", "w"]
    style_list = ["line", "dashed", "dotted", "dashdot"]

    CLEAN_STYLE_OPTIONS = ["dotted","fill","dash","line",\
                            "point","cross","circle","plus","asterisk","pentagon","hexagon",\
                            "triangle","triangle-up","triangle-down",\
                            "triangle-left","triangle-right"]
    CLEAN_COLOR_OPTIONS = ["red","black","green","blue","cyan","grey","magenta","yellow","white"]

    all_color_options = color_list + CLEAN_COLOR_OPTIONS
    all_style_options = style_list + CLEAN_STYLE_OPTIONS

    display_schema = {
        "type": "object",
        "properties": {
            "color": {"type": "string", "enum": all_color_options , 
                      "description": "Color code (e.g., k=black, r=red, g=green, etc.)",
                      "default": "black"},
            "style": {"type": "string", "enum": all_style_options ,
                      "description": "Line style options",
                      "default": "line"}
        },
        "required": ["color", "style"],
        "additionalProperties": False
    }

    return display_schema

def fn_plot_schema():
   
    plot_schema = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "Name of the plot",
            "default": "Default Plot"
        },
        "plotType": {
            "type": "string",
            "description": "Plot Type",
            "default": "Cross Section vs WIMP Mass",
            "enum": [
                "Cross Section vs WIMP Mass",
                "Cross Section / Mass [in GeV] vs Mass[GeV]",
            ]
        },
        "xMax": {
            "type": "string",
            "description": "Maximum X value (numeric string)",
            "default": "100"
        },
        "xMin": {
            "type": "string",
            "description": "Minimum X value (numeric string)",
            "default": "0"
        },
        "yMax": {
            "type": "string",
            "description": "Maximum Y value (numeric string)",
            "default": "100"
        },
        "yMin": {
            "type": "string",
            "description": "Minimum Y value (numeric string)",
            "default": "0"
        },
        "xUnits": {
            "type": "string",
            "description": "Units for the X-axis",
            "default": "keV/c^2",
            "enum": [
                "eV/c^2",
                "keV/c^2",
                "MeV/c^2",
                "GeV/c^2",
                "TeV/c^2"
            ]
        },
        "yUnits": {
            "type": "string",
            "description": "Units for the Y-axis",
            "default": "cm^2",
        }
    },
    "required": ["name", "xMax", "xMin", "yMax", "yMin", "xUnits", "yUnits"],
    "additionalProperties": False
}
   
    return plot_schema


def create_default_json(node_type):
    node_type_schema = get_node_schema(node_type)
    # print("node_type_schema >>",node_type_schema)
    """Apply default values from schema if missing in data."""
    default_json_data = {}
    for key, prop in node_type_schema.get("properties", {}).items():
        default_json_data[key] = prop["default"]
    
    return default_json_data

def get_cross_section_dictionary():
    cross_section_units = {
        "square centimeter": {
            "symbol": "cm²",
            "in_barns": None,
            "in_cm2": 1,
            "si_prefix": None
        },
        "barn": {
            "symbol": "b",
            "in_barns": 1,
            "in_cm2": 1e-24,
            "si_prefix": None
        },
        "decibarn": {
            "symbol": "db",
            "in_barns": 1e-1,
            "in_cm2": 1e-25,
            "si_prefix": "deci"
        },
        "centibarn": {
            "symbol": "cb",
            "in_barns": 1e-2,
            "in_cm2": 1e-26,
            "si_prefix": "centi"
        },
        "millibarn": {
            "symbol": "mb",
            "in_barns": 1e-3,
            "in_cm2": 1e-27,
            "si_prefix": "milli"
        },
        "microbarn": {
            "symbol": "μb",
            "in_barns": 1e-6,
            "in_cm2": 1e-30,
            "si_prefix": "micro"
        },
        "nanobarn": {
            "symbol": "nb",
            "in_barns": 1e-9,
            "in_cm2": 1e-33,
            "si_prefix": "nano"
        },
        "picobarn": {
            "symbol": "pb",
            "in_barns": 1e-12,
            "in_cm2": 1e-36,
            "si_prefix": "pico"
        },
        "femtobarn": {
            "symbol": "fb",
            "in_barns": 1e-15,
            "in_cm2": 1e-39,
            "si_prefix": "femto"
        },
        "attobarn": {
            "symbol": "ab",
            "in_barns": 1e-18,
            "in_cm2": 1e-42,
            "si_prefix": "atto"
        },
        "zeptobarn": {
            "symbol": "zb",
            "in_barns": 1e-21,
            "in_cm2": 1e-45,
            "si_prefix": "zepto"
        },
        "yoctobarn": {
            "symbol": "yb",
            "in_barns": 1e-24,
            "in_cm2": 1e-48,
            "si_prefix": "yocto"
        }
    }
    return cross_section_units