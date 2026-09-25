"""Synthetic catalogs of the characterized Flowinvoice demo profile.

Data part of ``docs/demo_data/generate_demo_invoices.py`` at source commit
fb2d18568d2eaf64574d131ceae51a936b9aac02, values, order and comments unchanged;
rules live in :mod:`auditcore_invoicegenerator._legacy`. Parties, identifiers and
labels are synthetic training data, not real records or findings.
"""

from __future__ import annotations


def _supplier(name: str, vat_id: str, country: str, city: str, category: str) -> dict[str, str]:
    """Supplier record with the source's key order."""
    return {"name": name, "vat_id": vat_id, "country": country, "city": city, "category": category}


WORK_PACKAGES = {
    "WP1": {"name": "Project Management", "categories": ["travel", "admin", "personnel"]},
    "WP2": {
        "name": "Research & Development",
        "categories": ["equipment", "software", "consumables", "subcontracting"],
    },
    "WP3": {
        "name": "Pilot Implementation",
        "categories": ["construction", "hardware", "installation", "certification"],
    },
    "WP4": {
        "name": "Dissemination",
        "categories": ["website", "publications", "conference", "training"],
    },
}

SUPPLIERS = [
    # UK Companies
    _supplier("Johnson IT Services Ltd.", "GB123456789", "GB", "Cambridge", "software"),
    _supplier("Smith Office Supplies Ltd.", "GB987654321", "GB", "Manchester", "equipment"),
    _supplier("Williams Consulting Group", "GB456789123", "GB", "London", "consulting"),
    _supplier("Taylor Engineering Solutions", "GB321654987", "GB", "Birmingham", "hardware"),
    _supplier("Brown & Associates Legal", "GB147258369", "GB", "Leeds", "consulting"),
    _supplier("Davies Technical Services", "GB963852741", "GB", "Bristol", "installation"),
    _supplier("Wilson Software Systems", "GB852963741", "GB", "Edinburgh", "software"),
    _supplier("Evans Data Analytics Ltd.", "GB741852963", "GB", "Glasgow", "software"),
    _supplier("Thomas Hardware Distribution", "GB369258147", "GB", "Cardiff", "hardware"),
    _supplier("Roberts IT Infrastructure", "GB258147369", "GB", "Newcastle", "hardware"),
    _supplier("Clarke Publishing Services", "GB147369258", "GB", "Oxford", "publications"),
    _supplier("Hall Conference Management", "GB369147258", "GB", "Brighton", "conference"),
    _supplier("Green Energy Consulting", "GB258369147", "GB", "Southampton", "consulting"),
    _supplier("King Laboratory Supplies", "GB159357486", "GB", "Liverpool", "consumables"),
    _supplier("Wright Training Academy", "GB486357159", "GB", "Sheffield", "training"),
    _supplier("Baker Project Services", "GB357159486", "GB", "Nottingham", "consulting"),
    _supplier("Adams Web Development", "GB159486357", "GB", "Leicester", "website"),
    _supplier("Mitchell Research Ltd.", "GB486159357", "GB", "Reading", "subcontracting"),
    _supplier("Campbell Electronics", "GB357486159", "GB", "Aberdeen", "hardware"),
    _supplier("Phillips Certification Body", "GB951753864", "GB", "Coventry", "certification"),
    # German Companies
    _supplier("Müller Technologie GmbH", "DE123456789", "DE", "Munich", "hardware"),
    _supplier("Schmidt Software AG", "DE987654321", "DE", "Berlin", "software"),
    _supplier("Weber Consulting GmbH", "DE456789123", "DE", "Hamburg", "consulting"),
    _supplier("Fischer Engineering GmbH", "DE321654987", "DE", "Frankfurt", "installation"),
    _supplier("Meyer Büroausstattung", "DE147258369", "DE", "Cologne", "equipment"),
    _supplier("Wagner Elektronik GmbH", "DE963852741", "DE", "Stuttgart", "hardware"),
    _supplier("Becker IT Services", "DE852963741", "DE", "Düsseldorf", "software"),
    _supplier("Hoffmann Data Systems", "DE741852963", "DE", "Leipzig", "software"),
    _supplier("Schulz Laborgeräte GmbH", "DE369258147", "DE", "Dresden", "consumables"),
    _supplier("Koch Weiterbildung GmbH", "DE258147369", "DE", "Hanover", "training"),
    _supplier("Bauer Construction GmbH", "DE147369258", "DE", "Nuremberg", "construction"),
    _supplier("Richter Zertifizierung", "DE369147258", "DE", "Bremen", "certification"),
    _supplier("Klein & Partner Consulting", "DE258369147", "DE", "Essen", "consulting"),
    _supplier("Wolf Medientechnik", "DE159357486", "DE", "Dortmund", "equipment"),
    _supplier("Neumann Digital Solutions", "DE486357159", "DE", "Bonn", "software"),
    # French Companies
    _supplier("Dupont Technologies SARL", "FR12345678901", "FR", "Paris", "software"),
    _supplier("Martin Consulting SAS", "FR98765432101", "FR", "Lyon", "consulting"),
    _supplier("Bernard Équipements SA", "FR45678912301", "FR", "Marseille", "equipment"),
    _supplier("Petit Engineering SARL", "FR32165498701", "FR", "Toulouse", "installation"),
    _supplier("Robert IT Services SAS", "FR14725836901", "FR", "Nice", "software"),
    _supplier("Richard Laboratoire SARL", "FR96385274101", "FR", "Nantes", "consumables"),
    _supplier("Durand Formation SA", "FR85296374101", "FR", "Strasbourg", "training"),
    _supplier("Moreau Web Design", "FR74185296301", "FR", "Bordeaux", "website"),
    _supplier("Laurent Publications SARL", "FR36925814701", "FR", "Lille", "publications"),
    _supplier("Simon Construction SAS", "FR25814736901", "FR", "Rennes", "construction"),
    # Dutch Companies
    _supplier("Amsterdam Digital BV", "NL123456789B01", "NL", "Amsterdam", "software"),
    _supplier("Rotterdam Tech Solutions", "NL987654321B01", "NL", "Rotterdam", "hardware"),
    _supplier("Utrecht Consulting BV", "NL456789123B01", "NL", "Utrecht", "consulting"),
    _supplier("Den Haag IT Services", "NL321654987B01", "NL", "The Hague", "software"),
    _supplier("Eindhoven Electronics BV", "NL147258369B01", "NL", "Eindhoven", "hardware"),
    _supplier("Groningen Research BV", "NL963852741B01", "NL", "Groningen", "subcontracting"),
    _supplier("Maastricht Training BV", "NL852963741B01", "NL", "Maastricht", "training"),
    _supplier("Tilburg Data Systems", "NL741852963B01", "NL", "Tilburg", "software"),
    # Belgian Companies
    _supplier("Brussels Innovation SPRL", "BE0123456789", "BE", "Brussels", "consulting"),
    _supplier("Antwerp Tech Solutions", "BE0987654321", "BE", "Antwerp", "hardware"),
    _supplier("Ghent Software BVBA", "BE0456789123", "BE", "Ghent", "software"),
    _supplier("Liège Engineering SA", "BE0321654987", "BE", "Liège", "installation"),
    _supplier("Leuven Research Services", "BE0147258369", "BE", "Leuven", "subcontracting"),
    _supplier("Bruges Conference Center", "BE0963852741", "BE", "Bruges", "conference"),
    # Swedish Companies
    _supplier("Nordic Tech Solutions AB", "SE556677889901", "SE", "Stockholm", "software"),
    _supplier("Göteborg Engineering AB", "SE556688990011", "SE", "Gothenburg", "hardware"),
    _supplier("Malmö IT Services AB", "SE556699001122", "SE", "Malmö", "software"),
    _supplier("Uppsala Research AB", "SE556600112233", "SE", "Uppsala", "subcontracting"),
    _supplier("Linköping Consulting AB", "SE556611223344", "SE", "Linköping", "consulting"),
    # Italian Companies
    _supplier("Milano Tecnologia SRL", "IT12345678901", "IT", "Milan", "hardware"),
    _supplier("Roma Consulting SPA", "IT98765432101", "IT", "Rome", "consulting"),
    _supplier("Torino Software SRL", "IT45678912301", "IT", "Turin", "software"),
    _supplier("Firenze Design Studio", "IT32165498701", "IT", "Florence", "website"),
    _supplier("Bologna Formazione SRL", "IT14725836901", "IT", "Bologna", "training"),
    _supplier("Napoli Engineering SPA", "IT96385274101", "IT", "Naples", "installation"),
    # Spanish Companies
    _supplier("Madrid Tecnología SL", "ESA12345678", "ES", "Madrid", "software"),
    _supplier("Barcelona Consulting SL", "ESB98765432", "ES", "Barcelona", "consulting"),
    _supplier("Valencia IT Services", "ESA45678912", "ES", "Valencia", "software"),
    _supplier("Sevilla Hardware SL", "ESB32165498", "ES", "Seville", "hardware"),
    _supplier("Bilbao Engineering SA", "ESA14725836", "ES", "Bilbao", "installation"),
    # Austrian Companies
    _supplier("Wien Technologie GmbH", "ATU12345678", "AT", "Vienna", "hardware"),
    _supplier("Graz Software GmbH", "ATU98765432", "AT", "Graz", "software"),
    _supplier("Salzburg Consulting", "ATU45678912", "AT", "Salzburg", "consulting"),
    _supplier("Linz Engineering GmbH", "ATU32165498", "AT", "Linz", "installation"),
    _supplier("Innsbruck Training GmbH", "ATU14725836", "AT", "Innsbruck", "training"),
    # Polish Companies
    _supplier("Warsaw Tech Solutions", "PL1234567890", "PL", "Warsaw", "software"),
    _supplier("Krakow IT Services", "PL9876543210", "PL", "Krakow", "software"),
    _supplier("Gdansk Engineering", "PL4567891230", "PL", "Gdansk", "hardware"),
    _supplier("Wroclaw Consulting", "PL3216549870", "PL", "Wroclaw", "consulting"),
    _supplier("Poznan Training Center", "PL1472583690", "PL", "Poznan", "training"),
    # Irish Companies
    _supplier("Dublin Software Ltd.", "IE1234567WA", "IE", "Dublin", "software"),
    _supplier("Cork Tech Solutions", "IE9876543WB", "IE", "Cork", "hardware"),
    _supplier("Galway Consulting Ltd.", "IE4567891WC", "IE", "Galway", "consulting"),
    _supplier("Limerick IT Services", "IE3216549WD", "IE", "Limerick", "software"),
    # Portuguese Companies
    _supplier("Lisboa Tecnologia Lda", "PT123456789", "PT", "Lisbon", "software"),
    _supplier("Porto Consulting Lda", "PT987654321", "PT", "Porto", "consulting"),
    _supplier("Coimbra Engineering Lda", "PT456789123", "PT", "Coimbra", "installation"),
    # Danish Companies
    _supplier("Copenhagen Tech ApS", "DK12345678", "DK", "Copenhagen", "software"),
    _supplier("Aarhus IT Solutions", "DK98765432", "DK", "Aarhus", "hardware"),
    _supplier("Odense Consulting ApS", "DK45678912", "DK", "Odense", "consulting"),
    # Finnish Companies
    _supplier("Helsinki Software Oy", "FI12345678", "FI", "Helsinki", "software"),
    _supplier("Tampere Tech Oy", "FI98765432", "FI", "Tampere", "hardware"),
    _supplier("Turku Consulting Oy", "FI45678912", "FI", "Turku", "consulting"),
    # Czech Companies
    _supplier("Praha Software s.r.o.", "CZ12345678", "CZ", "Prague", "software"),
    _supplier("Brno Tech Solutions", "CZ98765432", "CZ", "Brno", "hardware"),
    _supplier("Ostrava Engineering", "CZ45678912", "CZ", "Ostrava", "installation"),
    # Greek Companies
    _supplier("Athens Tech Solutions", "EL123456789", "GR", "Athens", "software"),
    _supplier("Thessaloniki Consulting", "EL987654321", "GR", "Thessaloniki", "consulting"),
    # Hungarian Companies
    _supplier("Budapest Software Kft", "HU12345678", "HU", "Budapest", "software"),
    _supplier("Debrecen IT Services", "HU98765432", "HU", "Debrecen", "hardware"),
    # Romanian Companies
    _supplier("Bucharest Tech SRL", "RO12345678", "RO", "Bucharest", "software"),
    _supplier("Cluj IT Solutions", "RO98765432", "RO", "Cluj-Napoca", "software"),
    # Additional diverse suppliers
    _supplier("Luxembourg Consulting SARL", "LU12345678", "LU", "Luxembourg", "consulting"),
    _supplier("Cyprus Tech Ltd", "CY12345678X", "CY", "Nicosia", "software"),
    _supplier("Malta IT Services", "MT12345678", "MT", "Valletta", "software"),
    _supplier("Slovenia Engineering d.o.o.", "SI12345678", "SI", "Ljubljana", "installation"),
    _supplier("Slovakia Software s.r.o.", "SK1234567890", "SK", "Bratislava", "software"),
    _supplier("Estonia Digital OÜ", "EE123456789", "EE", "Tallinn", "software"),
    _supplier("Latvia Tech SIA", "LV12345678901", "LV", "Riga", "hardware"),
    _supplier("Lithuania Consulting UAB", "LT123456789012", "LT", "Vilnius", "consulting"),
    _supplier("Croatia Engineering d.o.o.", "HR12345678901", "HR", "Zagreb", "installation"),
    _supplier("Bulgaria Software EOOD", "BG123456789", "BG", "Sofia", "software"),
]

PROBLEM_SUPPLIERS = {
    "sanctions": {
        "name": "Petrov Industrial Supply Ltd.",
        "vat_id": "",
        "country": "RU",
        "city": "Moscow",
        "category": "equipment",
        "address": "42 Lenina Street, Moscow 125009",
    },
    "ted_concentration": {
        "name": "Consulting Partners Europe Ltd.",
        "vat_id": "GB111222333",
        "country": "GB",
        "city": "London",
        "category": "consulting",
        "address": "200 Whitehall Place, London SW1A 2AW",
    },
    "duplicate": {
        "name": "Smith Office Supplies Ltd.",
        "vat_id": "GB987654321",
        "country": "GB",
        "city": "Manchester",
        "category": "equipment",
    },
    "invalid_vat": {
        "name": "QuickFix Technical Services Ltd.",
        "vat_id": "GB999888777",  # Invalid VAT
        "country": "GB",
        "city": "Birmingham",
        "category": "installation",
    },
    "subject_relevance": {
        "name": "Gourmet Catering Services Ltd.",
        "vat_id": "GB555666777",
        "country": "GB",
        "city": "London",
        "category": "catering",  # Not project-related
    },
    "temporal": {
        "name": "Nordic Tech Solutions AB",
        "vat_id": "SE556677889901",
        "country": "SE",
        "city": "Stockholm",
        "category": "consulting",
    },
}

SERVICE_TEMPLATES = {
    "software": [
        ("Annual Software License - {product}", 800, 5000),
        ("Software Development Services", 2000, 15000),
        ("Cloud Infrastructure Setup", 1500, 8000),
        ("Database Management System License", 1200, 6000),
        ("API Integration Services", 1000, 7000),
        ("Software Maintenance & Support", 500, 3000),
        ("Custom Software Module Development", 3000, 20000),
        ("Software Testing Services", 800, 4000),
    ],
    "hardware": [
        ("Server Hardware - {model}", 2000, 15000),
        ("Network Equipment", 500, 5000),
        ("Computer Workstations ({qty} units)", 1500, 12000),
        ("Storage System", 1000, 8000),
        ("Laboratory Equipment", 2000, 25000),
        ("Sensor Array Components", 800, 6000),
        ("Testing Equipment", 1500, 10000),
        ("Measurement Instruments", 1000, 7000),
    ],
    "consulting": [
        ("Strategic Consulting Services", 2000, 20000),
        ("Technical Advisory ({hours}h)", 1500, 15000),
        ("Project Management Consulting", 1000, 10000),
        ("Business Process Analysis", 800, 8000),
        ("Market Research & Analysis", 1500, 12000),
        ("Regulatory Compliance Consulting", 2000, 15000),
        ("Technology Assessment", 1200, 9000),
        ("Feasibility Study", 3000, 25000),
    ],
    "equipment": [
        ("Office Furniture Set", 500, 5000),
        ("Laboratory Supplies", 200, 2000),
        ("Presentation Equipment", 300, 3000),
        ("Safety Equipment", 400, 2500),
        ("Communication Equipment", 600, 4000),
        ("Monitoring Equipment", 800, 6000),
    ],
    "training": [
        ("Professional Training Workshop", 500, 5000),
        ("Technical Skills Training ({days} days)", 1000, 8000),
        ("Certification Course", 800, 4000),
        ("Online Training Platform Access", 300, 2000),
        ("Safety Training Program", 600, 3000),
        ("Leadership Development Training", 1500, 10000),
    ],
    "travel": [
        ("Conference Attendance - {event}", 500, 3000),
        ("Project Meeting Travel Expenses", 300, 2000),
        ("Site Visit Transportation", 200, 1500),
        ("International Travel - {destination}", 800, 4000),
    ],
    "publications": [
        ("Scientific Publication Services", 500, 3000),
        ("Technical Documentation", 800, 5000),
        ("Journal Article Processing Charges", 1000, 4000),
        ("Report Design & Printing", 400, 2500),
        ("Translation Services", 300, 2000),
    ],
    "conference": [
        ("Conference Organization Support", 2000, 15000),
        ("Event Venue Rental", 1000, 8000),
        ("Conference Materials & Equipment", 500, 4000),
        ("Virtual Event Platform", 800, 5000),
    ],
    "website": [
        ("Website Development", 2000, 15000),
        ("Web Hosting Services (Annual)", 200, 1500),
        ("Website Maintenance", 300, 2000),
        ("SEO & Analytics Services", 500, 4000),
        ("Content Management System", 1000, 6000),
    ],
    "installation": [
        ("Equipment Installation Services", 1000, 10000),
        ("System Integration", 2000, 15000),
        ("On-site Technical Support", 500, 5000),
        ("Commissioning Services", 1500, 12000),
    ],
    "certification": [
        ("Quality Certification Audit", 2000, 10000),
        ("Product Certification Services", 3000, 15000),
        ("Compliance Assessment", 1500, 8000),
        ("Safety Certification", 2000, 12000),
    ],
    "subcontracting": [
        ("Research Subcontract", 5000, 50000),
        ("Technical Analysis Services", 3000, 25000),
        ("Specialized Testing Services", 2000, 15000),
        ("Data Collection & Processing", 1500, 10000),
    ],
    "construction": [
        ("Pilot Facility Construction", 10000, 100000),
        ("Laboratory Renovation", 5000, 50000),
        ("Infrastructure Modifications", 3000, 30000),
    ],
    "consumables": [
        ("Laboratory Consumables", 200, 3000),
        ("Chemical Reagents", 300, 2500),
        ("Testing Materials", 150, 2000),
        ("Prototype Materials", 500, 5000),
    ],
    "admin": [
        ("Administrative Support Services", 500, 3000),
        ("Legal Advisory Services", 1000, 8000),
        ("Accounting Services", 600, 4000),
        ("Insurance Premium", 400, 3000),
    ],
    "personnel": [
        ("External Expert Consultation", 1000, 10000),
        ("Temporary Staff Services", 2000, 15000),
    ],
    "catering": [
        ("Executive Lunch Catering", 500, 3000),
        ("Premium Wine Selection", 200, 1500),
        ("Event Catering Services", 1000, 5000),
    ],
}

PRODUCTS = [
    "DataAnalyzer Pro",
    "CloudManager Suite",
    "SecureNet Platform",
    "ResearchHub",
    "LabTracker",
    "ProjectFlow",
]

MODELS = ["PowerEdge R750", "ProLiant DL380", "ThinkSystem SR650", "Precision 7920", "Z8 G4"]

EVENTS = [
    "GreenTech Summit 2025",
    "EU Innovation Forum",
    "Climate Tech Conference",
    "Horizon Europe Networking",
    "Sustainable Future Expo",
]

DESTINATIONS = ["Brussels", "Paris", "Berlin", "Amsterdam", "Vienna", "Stockholm"]
