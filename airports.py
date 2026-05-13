"""
Airport registry for continental US, Canada, Mexico, Puerto Rico, and Caribbean.

Supports lookup by:
  - IATA code        : "JFK"
  - Metro group      : "NYC"  → ["JFK", "LGA", "EWR"]
  - Region name      : "caribbean" → all Caribbean airports
  - City name        : "new york"  → ["JFK", "LGA", "EWR"]

Usage:
    from airports import resolve, label, list_airports
    codes = resolve("NYC")          # ["JFK", "LGA", "EWR"]
    codes = resolve("caribbean")    # [...25 airports...]
    codes = resolve("Chicago")      # ["ORD", "MDW"]
    codes = resolve("SJU")          # ["SJU"]
    print(label("JFK"))             # "New York (JFK)"
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Airport:
    iata: str
    name: str
    city: str
    subdivision: str   # state / province / territory
    country: str       # ISO 3166-1 alpha-2
    region: str        # internal grouping key
    is_international: bool


# ---------------------------------------------------------------------------
# Airport registry
# ---------------------------------------------------------------------------

AIRPORTS: Dict[str, Airport] = {

    # ── Continental US — Northeast ──────────────────────────────────────
    "BOS": Airport("BOS", "Logan International",          "Boston",            "MA", "US", "northeast", True),
    "JFK": Airport("JFK", "John F. Kennedy International","New York",           "NY", "US", "northeast", True),
    "LGA": Airport("LGA", "LaGuardia",                    "New York",           "NY", "US", "northeast", False),
    "EWR": Airport("EWR", "Newark Liberty International", "Newark",             "NJ", "US", "northeast", True),
    "HPN": Airport("HPN", "Westchester County",           "White Plains",       "NY", "US", "northeast", False),
    "PVD": Airport("PVD", "T.F. Green",                   "Providence",         "RI", "US", "northeast", False),
    "MHT": Airport("MHT", "Manchester-Boston Regional",   "Manchester",         "NH", "US", "northeast", False),
    "BDL": Airport("BDL", "Bradley International",        "Hartford",           "CT", "US", "northeast", True),
    "ALB": Airport("ALB", "Albany International",         "Albany",             "NY", "US", "northeast", False),
    "BUF": Airport("BUF", "Buffalo Niagara International","Buffalo",            "NY", "US", "northeast", True),
    "ROC": Airport("ROC", "Greater Rochester International","Rochester",         "NY", "US", "northeast", False),
    "SYR": Airport("SYR", "Hancock International",        "Syracuse",           "NY", "US", "northeast", False),
    "PHL": Airport("PHL", "Philadelphia International",   "Philadelphia",       "PA", "US", "northeast", True),
    "PIT": Airport("PIT", "Pittsburgh International",     "Pittsburgh",         "PA", "US", "northeast", True),
    "IAD": Airport("IAD", "Dulles International",         "Washington",         "DC", "US", "northeast", True),
    "DCA": Airport("DCA", "Reagan National",              "Washington",         "DC", "US", "northeast", False),
    "BWI": Airport("BWI", "BWI Marshall",                 "Baltimore",          "MD", "US", "northeast", True),
    "RIC": Airport("RIC", "Richmond International",       "Richmond",           "VA", "US", "northeast", False),
    "ORF": Airport("ORF", "Norfolk International",        "Norfolk",            "VA", "US", "northeast", False),
    "AVP": Airport("AVP", "Wilkes-Barre/Scranton",        "Scranton",           "PA", "US", "northeast", False),

    # ── Continental US — Southeast ──────────────────────────────────────
    "ATL": Airport("ATL", "Hartsfield-Jackson",           "Atlanta",            "GA", "US", "southeast", True),
    "CLT": Airport("CLT", "Charlotte Douglas International","Charlotte",         "NC", "US", "southeast", True),
    "RDU": Airport("RDU", "Raleigh-Durham International", "Raleigh",            "NC", "US", "southeast", True),
    "GSP": Airport("GSP", "Greenville-Spartanburg",       "Greenville",         "SC", "US", "southeast", False),
    "CHS": Airport("CHS", "Charleston International",     "Charleston",         "SC", "US", "southeast", True),
    "SAV": Airport("SAV", "Savannah/Hilton Head",         "Savannah",           "GA", "US", "southeast", True),
    "JAX": Airport("JAX", "Jacksonville International",   "Jacksonville",       "FL", "US", "southeast", True),
    "MIA": Airport("MIA", "Miami International",          "Miami",              "FL", "US", "southeast", True),
    "FLL": Airport("FLL", "Fort Lauderdale-Hollywood",    "Fort Lauderdale",    "FL", "US", "southeast", True),
    "PBI": Airport("PBI", "Palm Beach International",     "West Palm Beach",    "FL", "US", "southeast", True),
    "MCO": Airport("MCO", "Orlando International",        "Orlando",            "FL", "US", "southeast", True),
    "TPA": Airport("TPA", "Tampa International",          "Tampa",              "FL", "US", "southeast", True),
    "RSW": Airport("RSW", "Southwest Florida International","Fort Myers",        "FL", "US", "southeast", True),
    "SRQ": Airport("SRQ", "Sarasota-Bradenton",           "Sarasota",           "FL", "US", "southeast", False),
    "PIE": Airport("PIE", "St. Pete-Clearwater International","St. Petersburg",  "FL", "US", "southeast", False),
    "EYW": Airport("EYW", "Key West International",       "Key West",           "FL", "US", "southeast", False),
    "PNS": Airport("PNS", "Pensacola International",      "Pensacola",          "FL", "US", "southeast", False),
    "MOB": Airport("MOB", "Mobile Regional",              "Mobile",             "AL", "US", "southeast", False),
    "BHM": Airport("BHM", "Birmingham-Shuttlesworth",     "Birmingham",         "AL", "US", "southeast", True),
    "MSY": Airport("MSY", "Louis Armstrong New Orleans",  "New Orleans",        "LA", "US", "southeast", True),
    "BTR": Airport("BTR", "Baton Rouge Metropolitan",     "Baton Rouge",        "LA", "US", "southeast", False),
    "MEM": Airport("MEM", "Memphis International",        "Memphis",            "TN", "US", "southeast", True),
    "BNA": Airport("BNA", "Nashville International",      "Nashville",          "TN", "US", "southeast", True),
    "SDF": Airport("SDF", "Louisville Muhammad Ali",      "Louisville",         "KY", "US", "southeast", True),
    "LEX": Airport("LEX", "Blue Grass",                   "Lexington",          "KY", "US", "southeast", False),

    # ── Continental US — Midwest ────────────────────────────────────────
    "ORD": Airport("ORD", "O'Hare International",         "Chicago",            "IL", "US", "midwest", True),
    "MDW": Airport("MDW", "Midway International",         "Chicago",            "IL", "US", "midwest", False),
    "MKE": Airport("MKE", "Mitchell International",       "Milwaukee",          "WI", "US", "midwest", True),
    "MSN": Airport("MSN", "Dane County Regional",         "Madison",            "WI", "US", "midwest", False),
    "GRR": Airport("GRR", "Gerald R. Ford International", "Grand Rapids",       "MI", "US", "midwest", False),
    "DTW": Airport("DTW", "Detroit Metropolitan",         "Detroit",            "MI", "US", "midwest", True),
    "FNT": Airport("FNT", "Bishop International",         "Flint",              "MI", "US", "midwest", False),
    "CLE": Airport("CLE", "Hopkins International",        "Cleveland",          "OH", "US", "midwest", True),
    "CAK": Airport("CAK", "Akron-Canton",                 "Akron",              "OH", "US", "midwest", False),
    "CMH": Airport("CMH", "John Glenn Columbus",          "Columbus",           "OH", "US", "midwest", True),
    "DAY": Airport("DAY", "Dayton International",         "Dayton",             "OH", "US", "midwest", False),
    "CVG": Airport("CVG", "Cincinnati/Northern Kentucky", "Cincinnati",         "OH", "US", "midwest", True),
    "IND": Airport("IND", "Indianapolis International",  "Indianapolis",        "IN", "US", "midwest", True),
    "SBN": Airport("SBN", "South Bend International",    "South Bend",          "IN", "US", "midwest", False),
    "MSP": Airport("MSP", "Minneapolis-Saint Paul",       "Minneapolis",        "MN", "US", "midwest", True),
    "DSM": Airport("DSM", "Des Moines International",     "Des Moines",         "IA", "US", "midwest", False),
    "CID": Airport("CID", "Eastern Iowa",                 "Cedar Rapids",       "IA", "US", "midwest", False),
    "STL": Airport("STL", "Lambert-St. Louis International","St. Louis",        "MO", "US", "midwest", True),
    "MCI": Airport("MCI", "Kansas City International",    "Kansas City",        "MO", "US", "midwest", True),
    "OMA": Airport("OMA", "Eppley Airfield",              "Omaha",              "NE", "US", "midwest", False),
    "LNK": Airport("LNK", "Lincoln Airport",              "Lincoln",            "NE", "US", "midwest", False),
    "ICT": Airport("ICT", "Wichita Dwight D. Eisenhower", "Wichita",            "KS", "US", "midwest", False),

    # ── Continental US — Southwest ──────────────────────────────────────
    "DFW": Airport("DFW", "Dallas/Fort Worth International","Dallas",           "TX", "US", "southwest", True),
    "DAL": Airport("DAL", "Dallas Love Field",             "Dallas",            "TX", "US", "southwest", False),
    "IAH": Airport("IAH", "George Bush Intercontinental", "Houston",            "TX", "US", "southwest", True),
    "HOU": Airport("HOU", "William P. Hobby",             "Houston",            "TX", "US", "southwest", False),
    "AUS": Airport("AUS", "Austin-Bergstrom International","Austin",            "TX", "US", "southwest", True),
    "SAT": Airport("SAT", "San Antonio International",    "San Antonio",        "TX", "US", "southwest", True),
    "ELP": Airport("ELP", "El Paso International",        "El Paso",            "TX", "US", "southwest", True),
    "LBB": Airport("LBB", "Lubbock Preston Smith",        "Lubbock",            "TX", "US", "southwest", False),
    "AMA": Airport("AMA", "Rick Husband Amarillo",        "Amarillo",           "TX", "US", "southwest", False),
    "MAF": Airport("MAF", "Midland International",        "Midland",            "TX", "US", "southwest", False),
    "CRP": Airport("CRP", "Corpus Christi International", "Corpus Christi",     "TX", "US", "southwest", False),
    "MFE": Airport("MFE", "McAllen Miller International", "McAllen",            "TX", "US", "southwest", False),
    "TUL": Airport("TUL", "Tulsa International",          "Tulsa",              "OK", "US", "southwest", False),
    "OKC": Airport("OKC", "Will Rogers World",            "Oklahoma City",      "OK", "US", "southwest", False),
    "ABQ": Airport("ABQ", "Albuquerque International Sunport","Albuquerque",    "NM", "US", "southwest", True),
    "PHX": Airport("PHX", "Phoenix Sky Harbor International","Phoenix",         "AZ", "US", "southwest", True),
    "TUS": Airport("TUS", "Tucson International",         "Tucson",             "AZ", "US", "southwest", True),
    "YUM": Airport("YUM", "Yuma International",           "Yuma",               "AZ", "US", "southwest", False),

    # ── Continental US — West ───────────────────────────────────────────
    "LAX": Airport("LAX", "Los Angeles International",    "Los Angeles",        "CA", "US", "west", True),
    "BUR": Airport("BUR", "Hollywood Burbank",            "Burbank",            "CA", "US", "west", False),
    "LGB": Airport("LGB", "Long Beach",                   "Long Beach",         "CA", "US", "west", False),
    "SNA": Airport("SNA", "John Wayne",                   "Orange County",      "CA", "US", "west", True),
    "ONT": Airport("ONT", "Ontario International",        "Ontario",            "CA", "US", "west", False),
    "PSP": Airport("PSP", "Palm Springs International",   "Palm Springs",       "CA", "US", "west", False),
    "SAN": Airport("SAN", "San Diego International",      "San Diego",          "CA", "US", "west", True),
    "SFO": Airport("SFO", "San Francisco International",  "San Francisco",      "CA", "US", "west", True),
    "OAK": Airport("OAK", "Oakland International",        "Oakland",            "CA", "US", "west", True),
    "SJC": Airport("SJC", "Norman Y. Mineta San Jose",    "San Jose",           "CA", "US", "west", True),
    "SMF": Airport("SMF", "Sacramento International",     "Sacramento",         "CA", "US", "west", True),
    "FAT": Airport("FAT", "Fresno Yosemite International","Fresno",             "CA", "US", "west", False),
    "SBA": Airport("SBA", "Santa Barbara Municipal",      "Santa Barbara",      "CA", "US", "west", False),
    "LAS": Airport("LAS", "Harry Reid International",     "Las Vegas",          "NV", "US", "west", True),
    "RNO": Airport("RNO", "Reno-Tahoe International",     "Reno",               "NV", "US", "west", True),
    "SEA": Airport("SEA", "Seattle-Tacoma International", "Seattle",            "WA", "US", "west", True),
    "PDX": Airport("PDX", "Portland International",       "Portland",           "OR", "US", "west", True),
    "EUG": Airport("EUG", "Eugene Airport",               "Eugene",             "OR", "US", "west", False),
    "MFR": Airport("MFR", "Rogue Valley International",   "Medford",            "OR", "US", "west", False),
    "BOI": Airport("BOI", "Boise Airport",                "Boise",              "ID", "US", "west", True),
    "GEG": Airport("GEG", "Spokane International",        "Spokane",            "WA", "US", "west", False),
    "SLC": Airport("SLC", "Salt Lake City International", "Salt Lake City",     "UT", "US", "west", True),
    "DEN": Airport("DEN", "Denver International",         "Denver",             "CO", "US", "west", True),
    "COS": Airport("COS", "Colorado Springs",             "Colorado Springs",   "CO", "US", "west", False),
    "GJT": Airport("GJT", "Grand Junction Regional",      "Grand Junction",     "CO", "US", "west", False),
    "BZN": Airport("BZN", "Bozeman Yellowstone International","Bozeman",        "MT", "US", "west", False),
    "MSO": Airport("MSO", "Missoula Montana",             "Missoula",           "MT", "US", "west", False),
    "BIL": Airport("BIL", "Billings Logan International", "Billings",           "MT", "US", "west", False),
    "FCA": Airport("FCA", "Glacier Park International",   "Kalispell",          "MT", "US", "west", False),
    "JAC": Airport("JAC", "Jackson Hole",                 "Jackson",            "WY", "US", "west", False),

    # ── Canada ──────────────────────────────────────────────────────────
    "YYZ": Airport("YYZ", "Toronto Pearson International","Toronto",            "ON", "CA", "canada", True),
    "YTZ": Airport("YTZ", "Billy Bishop Toronto City",    "Toronto",            "ON", "CA", "canada", False),
    "YHM": Airport("YHM", "John C. Munro Hamilton",       "Hamilton",           "ON", "CA", "canada", False),
    "YOW": Airport("YOW", "Ottawa Macdonald-Cartier",     "Ottawa",             "ON", "CA", "canada", True),
    "YUL": Airport("YUL", "Montreal-Trudeau International","Montreal",          "QC", "CA", "canada", True),
    "YQB": Airport("YQB", "Quebec City Jean Lesage",      "Quebec City",        "QC", "CA", "canada", True),
    "YHZ": Airport("YHZ", "Halifax Stanfield International","Halifax",          "NS", "CA", "canada", True),
    "YYT": Airport("YYT", "St. John's International",     "St. John's",         "NL", "CA", "canada", True),
    "YWG": Airport("YWG", "Winnipeg James Armstrong Richardson","Winnipeg",     "MB", "CA", "canada", True),
    "YQR": Airport("YQR", "Regina International",         "Regina",             "SK", "CA", "canada", False),
    "YXE": Airport("YXE", "Saskatoon John G. Diefenbaker","Saskatoon",          "SK", "CA", "canada", False),
    "YYC": Airport("YYC", "Calgary International",        "Calgary",            "AB", "CA", "canada", True),
    "YEG": Airport("YEG", "Edmonton International",       "Edmonton",           "AB", "CA", "canada", True),
    "YVR": Airport("YVR", "Vancouver International",      "Vancouver",          "BC", "CA", "canada", True),
    "YYJ": Airport("YYJ", "Victoria International",       "Victoria",           "BC", "CA", "canada", False),
    "YLW": Airport("YLW", "Kelowna International",        "Kelowna",            "BC", "CA", "canada", False),

    # ── Mexico ──────────────────────────────────────────────────────────
    "MEX": Airport("MEX", "Benito Juarez International",  "Mexico City",        "",   "MX", "mexico", True),
    "CUN": Airport("CUN", "Cancun International",         "Cancun",             "",   "MX", "mexico", True),
    "GDL": Airport("GDL", "Miguel Hidal go International","Guadalajara",        "",   "MX", "mexico", True),
    "MTY": Airport("MTY", "Monterrey International",      "Monterrey",          "",   "MX", "mexico", True),
    "TIJ": Airport("TIJ", "General Abelardo L. Rodriguez","Tijuana",            "",   "MX", "mexico", True),
    "MZT": Airport("MZT", "Rafael Buelna International",  "Mazatlan",           "",   "MX", "mexico", True),
    "PVR": Airport("PVR", "Licenciado Gustavo Diaz Ordaz","Puerto Vallarta",    "",   "MX", "mexico", True),
    "SJD": Airport("SJD", "Los Cabos International",      "Los Cabos",          "",   "MX", "mexico", True),
    "HMO": Airport("HMO", "General Ignacio Pesqueira Garcia","Hermosillo",      "",   "MX", "mexico", True),
    "BJX": Airport("BJX", "Del Bajio International",      "Leon/Guanajuato",    "",   "MX", "mexico", True),
    "QRO": Airport("QRO", "Queretaro Intercontinental",   "Queretaro",          "",   "MX", "mexico", False),
    "MID": Airport("MID", "Manuel Crescencio Rejon",      "Merida",             "",   "MX", "mexico", False),
    "OAX": Airport("OAX", "Xoxocotlan International",     "Oaxaca",             "",   "MX", "mexico", False),
    "VER": Airport("VER", "General Heriberto Jara",       "Veracruz",           "",   "MX", "mexico", False),
    "ZIH": Airport("ZIH", "Ixtapa-Zihuatanejo International","Zihuatanejo",     "",   "MX", "mexico", False),
    "HUX": Airport("HUX", "Bahias de Huatulco International","Huatulco",        "",   "MX", "mexico", False),
    "CZM": Airport("CZM", "Cozumel International",        "Cozumel",            "",   "MX", "mexico", False),
    "TAM": Airport("TAM", "General Francisco Javier Mina","Tampico",            "",   "MX", "mexico", False),
    "PBC": Airport("PBC", "Huejotsingo International",    "Puebla",             "",   "MX", "mexico", False),
    "VSA": Airport("VSA", "Carlos Rovirosa Perez",        "Villahermosa",       "",   "MX", "mexico", False),

    # ── Puerto Rico ─────────────────────────────────────────────────────
    "SJU": Airport("SJU", "Luis Munoz Marin International","San Juan",          "PR", "US", "puerto_rico", True),
    "BQN": Airport("BQN", "Rafael Hernandez",             "Aguadilla",          "PR", "US", "puerto_rico", False),
    "MAZ": Airport("MAZ", "Eugenio Maria de Hostos",      "Mayaguez",           "PR", "US", "puerto_rico", False),
    "PSE": Airport("PSE", "Mercedita",                    "Ponce",              "PR", "US", "puerto_rico", False),
    "VQS": Airport("VQS", "Antonio Rivera Rodriguez",     "Vieques",            "PR", "US", "puerto_rico", False),
    "CPX": Airport("CPX", "Benjamin Rivera Noriega",      "Culebra",            "PR", "US", "puerto_rico", False),

    # ── Caribbean — Bahamas ─────────────────────────────────────────────
    "NAS": Airport("NAS", "Lynden Pindling International","Nassau",             "",   "BS", "caribbean", True),
    "FPO": Airport("FPO", "Grand Bahama International",   "Freeport",           "",   "BS", "caribbean", False),
    "MHH": Airport("MHH", "Marsh Harbour",                "Marsh Harbour",      "",   "BS", "caribbean", False),
    "GHB": Airport("GHB", "Governor's Harbour",           "Governor's Harbour", "",   "BS", "caribbean", False),
    "ELH": Airport("ELH", "North Eleuthera",              "North Eleuthera",    "",   "BS", "caribbean", False),

    # ── Caribbean — Jamaica ─────────────────────────────────────────────
    "MBJ": Airport("MBJ", "Sangster International",       "Montego Bay",        "",   "JM", "caribbean", True),
    "KIN": Airport("KIN", "Norman Manley International",  "Kingston",           "",   "JM", "caribbean", True),

    # ── Caribbean — Cayman Islands ──────────────────────────────────────
    "GCM": Airport("GCM", "Owen Roberts International",   "Grand Cayman",       "",   "KY", "caribbean", True),
    "CYB": Airport("CYB", "Charles Kirkconnell",          "Cayman Brac",        "",   "KY", "caribbean", False),

    # ── Caribbean — Cuba ────────────────────────────────────────────────
    "HAV": Airport("HAV", "Jose Marti International",     "Havana",             "",   "CU", "caribbean", True),
    "VRA": Airport("VRA", "Juan Gualberto Gomez",         "Varadero",           "",   "CU", "caribbean", True),
    "HOG": Airport("HOG", "Frank Pais International",     "Holguin",            "",   "CU", "caribbean", False),
    "SCU": Airport("SCU", "Antonio Maceo International",  "Santiago de Cuba",   "",   "CU", "caribbean", False),

    # ── Caribbean — Dominican Republic ──────────────────────────────────
    "SDQ": Airport("SDQ", "Las Americas International",   "Santo Domingo",      "",   "DO", "caribbean", True),
    "PUJ": Airport("PUJ", "Punta Cana International",     "Punta Cana",         "",   "DO", "caribbean", True),
    "STI": Airport("STI", "Cibao International",          "Santiago",           "",   "DO", "caribbean", False),
    "LRM": Airport("LRM", "Casa de Campo International",  "La Romana",          "",   "DO", "caribbean", False),
    "AZS": Airport("AZS", "El Catey International",       "Samana",             "",   "DO", "caribbean", False),

    # ── Caribbean — Haiti ───────────────────────────────────────────────
    "PAP": Airport("PAP", "Toussaint Louverture International","Port-au-Prince","",   "HT", "caribbean", True),
    "CAP": Airport("CAP", "Hugo Chavez International",    "Cap-Haitien",        "",   "HT", "caribbean", False),

    # ── Caribbean — US Virgin Islands ───────────────────────────────────
    "STT": Airport("STT", "Cyril E. King",                "St. Thomas",         "VI", "US", "caribbean", True),
    "STX": Airport("STX", "Henry E. Rohlsen",             "St. Croix",          "VI", "US", "caribbean", False),

    # ── Caribbean — Lesser Antilles ─────────────────────────────────────
    "SXM": Airport("SXM", "Princess Juliana International","Philipsburg",       "",   "SX", "caribbean", True),
    "AXA": Airport("AXA", "Clayton J. Lloyd",             "The Valley",         "",   "AI", "caribbean", False),
    "ANU": Airport("ANU", "V.C. Bird International",      "St. John's",         "",   "AG", "caribbean", True),
    "SKB": Airport("SKB", "Robert L. Bradshaw International","Basseterre",      "",   "KN", "caribbean", False),
    "NEV": Airport("NEV", "Vance W. Amory",               "Charlestown",        "",   "KN", "caribbean", False),
    "EIS": Airport("EIS", "Terrance B. Lettsome",         "Road Town",          "",   "VG", "caribbean", False),
    "DOM": Airport("DOM", "Canefield",                    "Roseau",             "",   "DM", "caribbean", False),
    "DCF": Airport("DCF", "Douglas-Charles",              "Marigot",            "",   "DM", "caribbean", False),
    "PTP": Airport("PTP", "Pointe-a-Pitre International", "Pointe-a-Pitre",     "",   "GP", "caribbean", True),
    "FDF": Airport("FDF", "Aime Cesaire International",   "Fort-de-France",     "",   "MQ", "caribbean", True),
    "SLU": Airport("SLU", "George F.L. Charles",          "Castries",           "",   "LC", "caribbean", False),
    "UVF": Airport("UVF", "Hewanorra International",      "Vieux Fort",         "",   "LC", "caribbean", True),
    "SVD": Airport("SVD", "Argyle International",         "Kingstown",          "",   "VC", "caribbean", False),
    "BGI": Airport("BGI", "Grantley Adams International", "Bridgetown",         "",   "BB", "caribbean", True),
    "GND": Airport("GND", "Maurice Bishop International", "St. George's",       "",   "GD", "caribbean", True),
    "POS": Airport("POS", "Piarco International",         "Port of Spain",      "",   "TT", "caribbean", True),
    "TAB": Airport("TAB", "ANR Robinson International",   "Scarborough",        "",   "TT", "caribbean", False),
    "AUA": Airport("AUA", "Queen Beatrix International",  "Oranjestad",         "",   "AW", "caribbean", True),
    "CUR": Airport("CUR", "Hato International",           "Willemstad",         "",   "CW", "caribbean", True),
    "BON": Airport("BON", "Flamingo International",       "Kralendijk",         "",   "BQ", "caribbean", False),
}


# ---------------------------------------------------------------------------
# Metro group shortcuts (short code → list of IATA codes)
# ---------------------------------------------------------------------------

METRO_GROUPS: Dict[str, List[str]] = {
    "NYC": ["JFK", "LGA", "EWR"],
    "CHI": ["ORD", "MDW"],
    "LA":  ["LAX", "BUR", "LGB", "SNA"],
    "SF":  ["SFO", "OAK", "SJC"],
    "DC":  ["IAD", "DCA", "BWI"],
    "DAL": ["DFW", "DAL"],
    "HOU": ["IAH", "HOU"],
    "MIA": ["MIA", "FLL", "PBI"],
    "ORL": ["MCO"],
    "TOR": ["YYZ", "YTZ"],
    "MTL": ["YUL"],
    "VAN": ["YVR", "YYJ"],
}

# ---------------------------------------------------------------------------
# Named region groups (region name → list of IATA codes)
# ---------------------------------------------------------------------------

REGION_GROUPS: Dict[str, List[str]] = {
    "northeast":  [k for k, v in AIRPORTS.items() if v.region == "northeast"],
    "southeast":  [k for k, v in AIRPORTS.items() if v.region == "southeast"],
    "midwest":    [k for k, v in AIRPORTS.items() if v.region == "midwest"],
    "southwest":  [k for k, v in AIRPORTS.items() if v.region == "southwest"],
    "west":       [k for k, v in AIRPORTS.items() if v.region == "west"],
    "canada":     [k for k, v in AIRPORTS.items() if v.region == "canada"],
    "mexico":     [k for k, v in AIRPORTS.items() if v.region == "mexico"],
    "puerto_rico": [k for k, v in AIRPORTS.items() if v.region == "puerto_rico"],
    "caribbean":  [k for k, v in AIRPORTS.items() if v.region == "caribbean"],
    "us":         [k for k, v in AIRPORTS.items() if v.country == "US" and v.region not in ("puerto_rico",)],
    "international": [k for k, v in AIRPORTS.items() if v.is_international],
}

# ---------------------------------------------------------------------------
# City name index (lowercase city → list of IATA codes)
# ---------------------------------------------------------------------------

_CITY_INDEX: Dict[str, List[str]] = {}
for _iata, _ap in AIRPORTS.items():
    _key = _ap.city.lower()
    _CITY_INDEX.setdefault(_key, []).append(_iata)

# Manual aliases for common city references with multiple airports
_CITY_INDEX.update({
    "new york":       ["JFK", "LGA", "EWR"],
    "new york city":  ["JFK", "LGA", "EWR"],
    "chicago":        ["ORD", "MDW"],
    "los angeles":    ["LAX", "BUR", "LGB", "SNA"],
    "san francisco":  ["SFO", "OAK", "SJC"],
    "washington":     ["IAD", "DCA", "BWI"],
    "washington dc":  ["IAD", "DCA", "BWI"],
    "dallas":         ["DFW", "DAL"],
    "houston":        ["IAH", "HOU"],
    "miami":          ["MIA", "FLL", "PBI"],
    "orlando":        ["MCO"],
    "toronto":        ["YYZ", "YTZ"],
    "montreal":       ["YUL"],
    "vancouver":      ["YVR", "YYJ"],
    "cancun":         ["CUN"],
    "mexico city":    ["MEX"],
    "puerto vallarta":["PVR"],
    "los cabos":      ["SJD"],
    "san juan":       ["SJU"],
    "nassau":         ["NAS"],
    "montego bay":    ["MBJ"],
    "punta cana":     ["PUJ"],
    "grand cayman":   ["GCM"],
    "aruba":          ["AUA"],
    "barbados":       ["BGI"],
    "st thomas":      ["STT"],
    "saint thomas":   ["STT"],
})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve(query: str) -> List[str]:
    """
    Resolve a user query string to a list of IATA airport codes.

    Lookup order:
      1. Exact IATA code (case-insensitive)
      2. Metro group alias (NYC, CHI, LA, DC, …)
      3. Region name (caribbean, canada, mexico, northeast, …)
      4. City name (case-insensitive, partial match not supported)

    Raises ValueError with suggestions if nothing matches.
    """
    q = query.strip()
    qu = q.upper()
    ql = q.lower()

    # 1. Exact IATA code
    if qu in AIRPORTS:
        return [qu]

    # 2. Metro group
    if qu in METRO_GROUPS:
        return METRO_GROUPS[qu]

    # 3. Region name
    if ql in REGION_GROUPS:
        return REGION_GROUPS[ql]

    # 4. City name
    if ql in _CITY_INDEX:
        return _CITY_INDEX[ql]

    # Nothing matched — build a helpful error
    suggestions = _suggest(q)
    msg = f"Unknown airport, city, or region: '{query}'."
    if suggestions:
        msg += f" Did you mean: {', '.join(suggestions)}?"
    else:
        msg += " Use --list-airports to see all options."
    raise ValueError(msg)


def label(iata: str) -> str:
    """Return 'City (IATA)' for display, e.g. 'New York (JFK)'."""
    ap = AIRPORTS.get(iata.upper())
    if not ap:
        return iata
    return f"{ap.city} ({ap.iata})"


def region_label(codes: List[str]) -> str:
    """
    Return a compact human-readable label for a list of airport codes.
    - Single code   → 'New York (JFK)'
    - Metro group   → 'New York (JFK/LGA/EWR)'
    - 4+ codes      → first city + '+ N more airports'
    """
    if not codes:
        return "(none)"
    if len(codes) == 1:
        return label(codes[0])

    # Check if it matches a known metro group name
    for name, airports in METRO_GROUPS.items():
        if sorted(airports) == sorted(codes):
            cities = list(dict.fromkeys(
                AIRPORTS[c].city for c in codes if c in AIRPORTS
            ))
            return f"{'/'.join(cities)} ({'/'.join(codes)})"

    if len(codes) <= 3:
        cities = list(dict.fromkeys(
            AIRPORTS[c].city for c in codes if c in AIRPORTS
        ))
        return f"{'/'.join(cities)} ({'/'.join(codes)})"

    first = AIRPORTS.get(codes[0])
    first_city = first.city if first else codes[0]
    return f"{first_city} + {len(codes) - 1} more airports ({len(codes)} total)"


def list_airports() -> str:
    """Return a formatted multi-line string of all airports for --list-airports."""
    region_order = [
        ("northeast",   "Continental US — Northeast"),
        ("southeast",   "Continental US — Southeast"),
        ("midwest",     "Continental US — Midwest"),
        ("southwest",   "Continental US — Southwest"),
        ("west",        "Continental US — West"),
        ("canada",      "Canada"),
        ("mexico",      "Mexico"),
        ("puerto_rico", "Puerto Rico"),
        ("caribbean",   "Caribbean"),
    ]
    lines = ["Available Airports", "=" * 60]
    for region_key, region_title in region_order:
        lines.append(f"\n{region_title}")
        lines.append("-" * 40)
        for iata, ap in AIRPORTS.items():
            if ap.region != region_key:
                continue
            intl = "✈" if ap.is_international else " "
            sub = f", {ap.subdivision}" if ap.subdivision else ""
            lines.append(f"  {intl} {iata:<5} {ap.city}{sub:<28}  {ap.name}")

    lines += [
        "",
        "Metro Area Codes",
        "-" * 40,
    ]
    for code, airports in METRO_GROUPS.items():
        lines.append(f"  {code:<5} → {', '.join(airports)}")

    lines += [
        "",
        "Region Names",
        "-" * 40,
        "  " + ", ".join(REGION_GROUPS.keys()),
        "",
        "Examples",
        "-" * 40,
        "  python run.py --from ORD --to NYC  --depart 2026-06-15 --return 2026-06-20",
        "  python run.py --from ORD --to caribbean --depart 2026-06-15 --return 2026-06-22",
        "  python run.py --from DFW --to CUN --depart 2026-07-04",
        "",
    ]
    return "\n".join(lines)


def _suggest(query: str) -> List[str]:
    """Return up to 5 close matches for an unrecognized query."""
    q = query.lower()
    matches = []
    for iata, ap in AIRPORTS.items():
        if (q in iata.lower() or q in ap.city.lower() or
                q in ap.name.lower()):
            matches.append(iata)
    for alias in list(METRO_GROUPS) + list(REGION_GROUPS):
        if q in alias.lower():
            matches.append(alias)
    return matches[:5]
