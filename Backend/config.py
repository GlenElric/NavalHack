"""
Configuration module for the Maritime Situational Awareness system.
Loads environment variables and defines constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECTOR_STORE_DIR = os.path.join(DATA_DIR, "vector_store")
CONTACTS_DB_PATH = os.path.join(DATA_DIR, "contacts.json")
ALERTS_DB_PATH = os.path.join(DATA_DIR, "alerts.json")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")

# Ensure directories exist
for d in [DATA_DIR, VECTOR_STORE_DIR, RAW_DATA_DIR]:
    os.makedirs(d, exist_ok=True)

# Maritime Zones (from dataset)
MARITIME_ZONES = [
    {
        "name": "Restricted Area Alpha",
        "type": "Military Exercise Zone",
        "coordinates": [
            {"lat": 12.5, "lon": -70.2},
            {"lat": 12.5, "lon": -70.8},
            {"lat": 13.1, "lon": -70.8},
            {"lat": 13.1, "lon": -70.2}
        ]
    },
    {
        "name": "Protected Marine Reserve Beta",
        "type": "Environmental Protection Zone",
        "coordinates": [
            {"lat": 13.2, "lon": -71.0},
            {"lat": 13.2, "lon": -71.4},
            {"lat": 13.6, "lon": -71.4},
            {"lat": 13.6, "lon": -71.0}
        ]
    },
    {
        "name": "Fishing Regulation Zone Charlie",
        "type": "Fisheries Management",
        "coordinates": [
            {"lat": 12.7, "lon": -70.5},
            {"lat": 12.7, "lon": -71.0},
            {"lat": 13.0, "lon": -71.0},
            {"lat": 13.0, "lon": -70.5}
        ]
    },
    {
        "name": "Port Approach Zone Xavier",
        "type": "Vessel Traffic Service Zone",
        "coordinates": [
            {"lat": 13.4, "lon": -70.8},
            {"lat": 13.4, "lon": -71.2},
            {"lat": 13.7, "lon": -71.2},
            {"lat": 13.7, "lon": -70.8}
        ]
    },
    {
        "name": "Submarine Exercise Area Delta",
        "type": "Naval Training Zone",
        "coordinates": [
            {"lat": 12.3, "lon": -71.2},
            {"lat": 12.3, "lon": -71.6},
            {"lat": 12.7, "lon": -71.6},
            {"lat": 12.7, "lon": -71.2}
        ]
    },
    {
        "name": "Oil Exploration Block Echo",
        "type": "Resource Extraction Zone",
        "coordinates": [
            {"lat": 13.8, "lon": -70.4},
            {"lat": 13.8, "lon": -70.8},
            {"lat": 14.2, "lon": -70.8},
            {"lat": 14.2, "lon": -70.4}
        ]
    }
]

SHIPPING_LANES = [
    {
        "name": "Northern Approach to Port Xavier",
        "type": "Major Shipping Route",
        "coordinates": [
            {"lat": 13.5, "lon": -71.0},
            {"lat": 13.2, "lon": -70.5}
        ]
    },
    {
        "name": "Southern Trade Route",
        "type": "International Shipping Lane",
        "coordinates": [
            {"lat": 12.0, "lon": -70.0},
            {"lat": 12.5, "lon": -71.5}
        ]
    },
    {
        "name": "Coastal Ferry Route Alpha",
        "type": "Domestic Passenger Route",
        "coordinates": [
            {"lat": 13.0, "lon": -70.2},
            {"lat": 13.5, "lon": -70.3},
            {"lat": 14.0, "lon": -70.4}
        ]
    },
    {
        "name": "Oil Tanker Channel Bravo",
        "type": "Hazardous Cargo Route",
        "coordinates": [
            {"lat": 14.0, "lon": -70.5},
            {"lat": 13.5, "lon": -71.0}
        ]
    }
]

# Threat classification keywords
THREAT_KEYWORDS = {
    "high": [
        "hostile", "submarine periscope", "unidentified", "not responding",
        "mayday", "fire", "explosion", "hostile submarine", "attack",
        "piracy", "armed", "smuggling", "drug", "human trafficking",
        "missile", "weapons", "covert", "espionage", "intercept",
        "fighter", "scramble", "engagement", "torpedo", "detonation",
        "threat", "suspicious", "uncooperative", "warning shots"
    ],
    "medium": [
        "distress", "oil spill", "restricted zone", "no-fly zone",
        "storm warning", "debris", "hazardous", "violation",
        "illegal fishing", "unlit vessel", "unknown", "encrypted",
        "surveillance", "anomalous", "unauthorized"
    ],
    "low": [
        "routine", "maintenance", "weather", "research", "survey",
        "exercise", "training", "observation", "monitoring"
    ]
}

# Contact type classification
CONTACT_TYPES = {
    "submarine": ["submarine", "periscope", "underwater contact", "submersible", "ssn", "undersea"],
    "warship": ["patrol boat", "coast guard", "naval", "cutter", "destroyer", "frigate", "task force", "carrier"],
    "aircraft": ["aircraft", "aerial", "helicopter", "drone", "fighter", "air patrol", "flying"],
    "merchant": ["cargo", "tanker", "merchant vessel", "container ship", "freighter", "trader"],
    "fishing": ["fishing vessel", "trawler", "fishing boat"],
    "civilian": ["yacht", "cruise ship", "pleasure", "sailing"],
    "unknown": ["unidentified", "unknown", "suspicious vessel"]
}
