"""Banques de données 100% fictives pour la génération synthétique Phase 1.

Aucun nom de personne, d'entreprise ou de lieu réel n'est utilisé. Les noms de
sociétés sont construits par combinaison déterministe de racines + suffixes
génériques pour éviter toute collision avec une marque existante.
"""

CORPORATE_EMAIL_DOMAIN = "genai-enterprise-lab.example"

FIRST_NAMES: list[str] = [
    "Alice", "Baptiste", "Camille", "David", "Elena", "Farid", "Giulia", "Hugo",
    "Ines", "Jonas", "Karim", "Lucia", "Mateo", "Nora", "Oscar", "Priya",
    "Quentin", "Rana", "Sofia", "Theo", "Uma", "Victor", "Wei", "Xenia",
    "Yanis", "Zoe", "Adam", "Bianca", "Cedric", "Dana", "Emile", "Fatou",
    "Gabriel", "Hana", "Ismael", "Julie", "Kenji", "Leila", "Marco", "Nadia",
    "Olivier", "Paula", "Quang", "Romy", "Samuel", "Tara", "Ulysse", "Valentina",
    "Wassim", "Yara", "Aaron", "Bea", "Cyril", "Dalia", "Erwan", "Fiona",
    "Gustav", "Helena", "Idris", "Jana",
]

LAST_NAMES: list[str] = [
    "Moreau", "Bernard", "Rossi", "Nilsson", "Haddad", "Kowalski", "Dubois",
    "Fischer", "Okafor", "Petit", "Garnier", "Novak", "Leroy", "Andersen",
    "Costa", "Meyer", "Benali", "Lambert", "Schmidt", "Roux", "Lindqvist",
    "Fontaine", "Weber", "Kaya", "Girard", "Bianchi", "Nguyen", "Martins",
    "Dupont", "Karlsson", "Faure", "Hoffmann", "Robin", "Moreno", "Simon",
    "Berger", "Chevalier", "Lund", "Henry", "Marchetti", "Blanc", "Aydin",
    "Fabre", "Richter", "Perrin", "Larsen", "Masson", "Conti", "Barbier",
    "Eriksson", "Renard", "Keller", "Dumont", "Novotny", "Gauthier", "Wagner",
    "Royer", "Silva", "Brun", "Almeida",
]

LOCATIONS: list[str] = [
    "Paris, FR", "Lyon, FR", "Lille, FR", "Nantes, FR", "Bruxelles, BE",
    "Geneve, CH", "Remote - EU",
]

INDUSTRIES: list[str] = [
    "Banking & Insurance", "Retail & E-commerce", "Manufacturing", "Energy & Utilities",
    "Healthcare & Life Sciences", "Public Sector", "Telecom", "Transport & Logistics",
    "Media & Entertainment", "Professional Services",
]

COUNTRIES: list[str] = ["FR", "BE", "CH", "LU", "DE", "NL", "ES", "IT"]

COMPANY_ROOTS: list[str] = [
    "Nova", "Axion", "Vertex", "Meridian", "Solace", "Opaline", "Cobalt", "Arboria",
    "Lumen", "Cresta", "Northgate", "Ondine", "Kestrel", "Halcyon", "Verdant",
    "Aurea", "Brightline", "Cedarwood", "Driftwood", "Everline", "Falkor", "Granite",
    "Hearthstone", "Ironbridge", "Jasper", "Kelvin", "Larkspur", "Millbrook",
    "Nordheim", "Orchard", "Pinegate", "Quillfeather", "Rivendale", "Silverline",
    "Tanglewood", "Umberfield", "Vellum", "Westhaven", "Yewgate", "Zenith",
]

COMPANY_SUFFIXES: list[str] = [
    "Group", "Solutions", "Partners", "Dynamics", "Systems", "Holding",
    "Industries", "Technologies", "Consulting", "Labs",
]

PROJECT_THEMES: list[str] = [
    "Data Platform", "Cloud Migration", "Analytics Program", "AI Assistant",
    "Governance Program", "Reporting Modernization", "Knowledge Base",
    "Integration Program", "Security Uplift", "Automation Program",
]

PARTNER_NAME_TOKENS: list[str] = [
    "Bridge", "Alliance", "Nexus", "Link", "Circuit", "Compass", "Horizon",
    "Pathway", "Union", "Relay",
]

SUPPLIER_NAME_TOKENS: list[str] = [
    "Supply", "Services", "Logistics", "Facilities", "Procurement", "Assets",
    "Networks", "Resources", "Operations", "Provision",
]
