"""Characterized Flowinvoice demo rules, source commit fb2d18568d2eaf64574d131ceae51a936b9aac02.

Local authorized extraction; rights status UNKNOWN, see NOTICE and provenance.
Rates, parties and labels are a historical synthetic training profile, not legal findings.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from random import Random
from typing import Any

PROJECT_START = datetime(2025, 1, 1)

PROJECT_END = datetime(2027, 12, 31)

INVOICE_DATE_RANGE_START = datetime(2025, 1, 15)

INVOICE_DATE_RANGE_END = datetime(2026, 1, 30)

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
    {
        "name": "Johnson IT Services Ltd.",
        "vat_id": "GB123456789",
        "country": "GB",
        "city": "Cambridge",
        "category": "software",
    },
    {
        "name": "Smith Office Supplies Ltd.",
        "vat_id": "GB987654321",
        "country": "GB",
        "city": "Manchester",
        "category": "equipment",
    },
    {
        "name": "Williams Consulting Group",
        "vat_id": "GB456789123",
        "country": "GB",
        "city": "London",
        "category": "consulting",
    },
    {
        "name": "Taylor Engineering Solutions",
        "vat_id": "GB321654987",
        "country": "GB",
        "city": "Birmingham",
        "category": "hardware",
    },
    {
        "name": "Brown & Associates Legal",
        "vat_id": "GB147258369",
        "country": "GB",
        "city": "Leeds",
        "category": "consulting",
    },
    {
        "name": "Davies Technical Services",
        "vat_id": "GB963852741",
        "country": "GB",
        "city": "Bristol",
        "category": "installation",
    },
    {
        "name": "Wilson Software Systems",
        "vat_id": "GB852963741",
        "country": "GB",
        "city": "Edinburgh",
        "category": "software",
    },
    {
        "name": "Evans Data Analytics Ltd.",
        "vat_id": "GB741852963",
        "country": "GB",
        "city": "Glasgow",
        "category": "software",
    },
    {
        "name": "Thomas Hardware Distribution",
        "vat_id": "GB369258147",
        "country": "GB",
        "city": "Cardiff",
        "category": "hardware",
    },
    {
        "name": "Roberts IT Infrastructure",
        "vat_id": "GB258147369",
        "country": "GB",
        "city": "Newcastle",
        "category": "hardware",
    },
    {
        "name": "Clarke Publishing Services",
        "vat_id": "GB147369258",
        "country": "GB",
        "city": "Oxford",
        "category": "publications",
    },
    {
        "name": "Hall Conference Management",
        "vat_id": "GB369147258",
        "country": "GB",
        "city": "Brighton",
        "category": "conference",
    },
    {
        "name": "Green Energy Consulting",
        "vat_id": "GB258369147",
        "country": "GB",
        "city": "Southampton",
        "category": "consulting",
    },
    {
        "name": "King Laboratory Supplies",
        "vat_id": "GB159357486",
        "country": "GB",
        "city": "Liverpool",
        "category": "consumables",
    },
    {
        "name": "Wright Training Academy",
        "vat_id": "GB486357159",
        "country": "GB",
        "city": "Sheffield",
        "category": "training",
    },
    {
        "name": "Baker Project Services",
        "vat_id": "GB357159486",
        "country": "GB",
        "city": "Nottingham",
        "category": "consulting",
    },
    {
        "name": "Adams Web Development",
        "vat_id": "GB159486357",
        "country": "GB",
        "city": "Leicester",
        "category": "website",
    },
    {
        "name": "Mitchell Research Ltd.",
        "vat_id": "GB486159357",
        "country": "GB",
        "city": "Reading",
        "category": "subcontracting",
    },
    {
        "name": "Campbell Electronics",
        "vat_id": "GB357486159",
        "country": "GB",
        "city": "Aberdeen",
        "category": "hardware",
    },
    {
        "name": "Phillips Certification Body",
        "vat_id": "GB951753864",
        "country": "GB",
        "city": "Coventry",
        "category": "certification",
    },
    # German Companies
    {
        "name": "Müller Technologie GmbH",
        "vat_id": "DE123456789",
        "country": "DE",
        "city": "Munich",
        "category": "hardware",
    },
    {
        "name": "Schmidt Software AG",
        "vat_id": "DE987654321",
        "country": "DE",
        "city": "Berlin",
        "category": "software",
    },
    {
        "name": "Weber Consulting GmbH",
        "vat_id": "DE456789123",
        "country": "DE",
        "city": "Hamburg",
        "category": "consulting",
    },
    {
        "name": "Fischer Engineering GmbH",
        "vat_id": "DE321654987",
        "country": "DE",
        "city": "Frankfurt",
        "category": "installation",
    },
    {
        "name": "Meyer Büroausstattung",
        "vat_id": "DE147258369",
        "country": "DE",
        "city": "Cologne",
        "category": "equipment",
    },
    {
        "name": "Wagner Elektronik GmbH",
        "vat_id": "DE963852741",
        "country": "DE",
        "city": "Stuttgart",
        "category": "hardware",
    },
    {
        "name": "Becker IT Services",
        "vat_id": "DE852963741",
        "country": "DE",
        "city": "Düsseldorf",
        "category": "software",
    },
    {
        "name": "Hoffmann Data Systems",
        "vat_id": "DE741852963",
        "country": "DE",
        "city": "Leipzig",
        "category": "software",
    },
    {
        "name": "Schulz Laborgeräte GmbH",
        "vat_id": "DE369258147",
        "country": "DE",
        "city": "Dresden",
        "category": "consumables",
    },
    {
        "name": "Koch Weiterbildung GmbH",
        "vat_id": "DE258147369",
        "country": "DE",
        "city": "Hanover",
        "category": "training",
    },
    {
        "name": "Bauer Construction GmbH",
        "vat_id": "DE147369258",
        "country": "DE",
        "city": "Nuremberg",
        "category": "construction",
    },
    {
        "name": "Richter Zertifizierung",
        "vat_id": "DE369147258",
        "country": "DE",
        "city": "Bremen",
        "category": "certification",
    },
    {
        "name": "Klein & Partner Consulting",
        "vat_id": "DE258369147",
        "country": "DE",
        "city": "Essen",
        "category": "consulting",
    },
    {
        "name": "Wolf Medientechnik",
        "vat_id": "DE159357486",
        "country": "DE",
        "city": "Dortmund",
        "category": "equipment",
    },
    {
        "name": "Neumann Digital Solutions",
        "vat_id": "DE486357159",
        "country": "DE",
        "city": "Bonn",
        "category": "software",
    },
    # French Companies
    {
        "name": "Dupont Technologies SARL",
        "vat_id": "FR12345678901",
        "country": "FR",
        "city": "Paris",
        "category": "software",
    },
    {
        "name": "Martin Consulting SAS",
        "vat_id": "FR98765432101",
        "country": "FR",
        "city": "Lyon",
        "category": "consulting",
    },
    {
        "name": "Bernard Équipements SA",
        "vat_id": "FR45678912301",
        "country": "FR",
        "city": "Marseille",
        "category": "equipment",
    },
    {
        "name": "Petit Engineering SARL",
        "vat_id": "FR32165498701",
        "country": "FR",
        "city": "Toulouse",
        "category": "installation",
    },
    {
        "name": "Robert IT Services SAS",
        "vat_id": "FR14725836901",
        "country": "FR",
        "city": "Nice",
        "category": "software",
    },
    {
        "name": "Richard Laboratoire SARL",
        "vat_id": "FR96385274101",
        "country": "FR",
        "city": "Nantes",
        "category": "consumables",
    },
    {
        "name": "Durand Formation SA",
        "vat_id": "FR85296374101",
        "country": "FR",
        "city": "Strasbourg",
        "category": "training",
    },
    {
        "name": "Moreau Web Design",
        "vat_id": "FR74185296301",
        "country": "FR",
        "city": "Bordeaux",
        "category": "website",
    },
    {
        "name": "Laurent Publications SARL",
        "vat_id": "FR36925814701",
        "country": "FR",
        "city": "Lille",
        "category": "publications",
    },
    {
        "name": "Simon Construction SAS",
        "vat_id": "FR25814736901",
        "country": "FR",
        "city": "Rennes",
        "category": "construction",
    },
    # Dutch Companies
    {
        "name": "Amsterdam Digital BV",
        "vat_id": "NL123456789B01",
        "country": "NL",
        "city": "Amsterdam",
        "category": "software",
    },
    {
        "name": "Rotterdam Tech Solutions",
        "vat_id": "NL987654321B01",
        "country": "NL",
        "city": "Rotterdam",
        "category": "hardware",
    },
    {
        "name": "Utrecht Consulting BV",
        "vat_id": "NL456789123B01",
        "country": "NL",
        "city": "Utrecht",
        "category": "consulting",
    },
    {
        "name": "Den Haag IT Services",
        "vat_id": "NL321654987B01",
        "country": "NL",
        "city": "The Hague",
        "category": "software",
    },
    {
        "name": "Eindhoven Electronics BV",
        "vat_id": "NL147258369B01",
        "country": "NL",
        "city": "Eindhoven",
        "category": "hardware",
    },
    {
        "name": "Groningen Research BV",
        "vat_id": "NL963852741B01",
        "country": "NL",
        "city": "Groningen",
        "category": "subcontracting",
    },
    {
        "name": "Maastricht Training BV",
        "vat_id": "NL852963741B01",
        "country": "NL",
        "city": "Maastricht",
        "category": "training",
    },
    {
        "name": "Tilburg Data Systems",
        "vat_id": "NL741852963B01",
        "country": "NL",
        "city": "Tilburg",
        "category": "software",
    },
    # Belgian Companies
    {
        "name": "Brussels Innovation SPRL",
        "vat_id": "BE0123456789",
        "country": "BE",
        "city": "Brussels",
        "category": "consulting",
    },
    {
        "name": "Antwerp Tech Solutions",
        "vat_id": "BE0987654321",
        "country": "BE",
        "city": "Antwerp",
        "category": "hardware",
    },
    {
        "name": "Ghent Software BVBA",
        "vat_id": "BE0456789123",
        "country": "BE",
        "city": "Ghent",
        "category": "software",
    },
    {
        "name": "Liège Engineering SA",
        "vat_id": "BE0321654987",
        "country": "BE",
        "city": "Liège",
        "category": "installation",
    },
    {
        "name": "Leuven Research Services",
        "vat_id": "BE0147258369",
        "country": "BE",
        "city": "Leuven",
        "category": "subcontracting",
    },
    {
        "name": "Bruges Conference Center",
        "vat_id": "BE0963852741",
        "country": "BE",
        "city": "Bruges",
        "category": "conference",
    },
    # Swedish Companies
    {
        "name": "Nordic Tech Solutions AB",
        "vat_id": "SE556677889901",
        "country": "SE",
        "city": "Stockholm",
        "category": "software",
    },
    {
        "name": "Göteborg Engineering AB",
        "vat_id": "SE556688990011",
        "country": "SE",
        "city": "Gothenburg",
        "category": "hardware",
    },
    {
        "name": "Malmö IT Services AB",
        "vat_id": "SE556699001122",
        "country": "SE",
        "city": "Malmö",
        "category": "software",
    },
    {
        "name": "Uppsala Research AB",
        "vat_id": "SE556600112233",
        "country": "SE",
        "city": "Uppsala",
        "category": "subcontracting",
    },
    {
        "name": "Linköping Consulting AB",
        "vat_id": "SE556611223344",
        "country": "SE",
        "city": "Linköping",
        "category": "consulting",
    },
    # Italian Companies
    {
        "name": "Milano Tecnologia SRL",
        "vat_id": "IT12345678901",
        "country": "IT",
        "city": "Milan",
        "category": "hardware",
    },
    {
        "name": "Roma Consulting SPA",
        "vat_id": "IT98765432101",
        "country": "IT",
        "city": "Rome",
        "category": "consulting",
    },
    {
        "name": "Torino Software SRL",
        "vat_id": "IT45678912301",
        "country": "IT",
        "city": "Turin",
        "category": "software",
    },
    {
        "name": "Firenze Design Studio",
        "vat_id": "IT32165498701",
        "country": "IT",
        "city": "Florence",
        "category": "website",
    },
    {
        "name": "Bologna Formazione SRL",
        "vat_id": "IT14725836901",
        "country": "IT",
        "city": "Bologna",
        "category": "training",
    },
    {
        "name": "Napoli Engineering SPA",
        "vat_id": "IT96385274101",
        "country": "IT",
        "city": "Naples",
        "category": "installation",
    },
    # Spanish Companies
    {
        "name": "Madrid Tecnología SL",
        "vat_id": "ESA12345678",
        "country": "ES",
        "city": "Madrid",
        "category": "software",
    },
    {
        "name": "Barcelona Consulting SL",
        "vat_id": "ESB98765432",
        "country": "ES",
        "city": "Barcelona",
        "category": "consulting",
    },
    {
        "name": "Valencia IT Services",
        "vat_id": "ESA45678912",
        "country": "ES",
        "city": "Valencia",
        "category": "software",
    },
    {
        "name": "Sevilla Hardware SL",
        "vat_id": "ESB32165498",
        "country": "ES",
        "city": "Seville",
        "category": "hardware",
    },
    {
        "name": "Bilbao Engineering SA",
        "vat_id": "ESA14725836",
        "country": "ES",
        "city": "Bilbao",
        "category": "installation",
    },
    # Austrian Companies
    {
        "name": "Wien Technologie GmbH",
        "vat_id": "ATU12345678",
        "country": "AT",
        "city": "Vienna",
        "category": "hardware",
    },
    {
        "name": "Graz Software GmbH",
        "vat_id": "ATU98765432",
        "country": "AT",
        "city": "Graz",
        "category": "software",
    },
    {
        "name": "Salzburg Consulting",
        "vat_id": "ATU45678912",
        "country": "AT",
        "city": "Salzburg",
        "category": "consulting",
    },
    {
        "name": "Linz Engineering GmbH",
        "vat_id": "ATU32165498",
        "country": "AT",
        "city": "Linz",
        "category": "installation",
    },
    {
        "name": "Innsbruck Training GmbH",
        "vat_id": "ATU14725836",
        "country": "AT",
        "city": "Innsbruck",
        "category": "training",
    },
    # Polish Companies
    {
        "name": "Warsaw Tech Solutions",
        "vat_id": "PL1234567890",
        "country": "PL",
        "city": "Warsaw",
        "category": "software",
    },
    {
        "name": "Krakow IT Services",
        "vat_id": "PL9876543210",
        "country": "PL",
        "city": "Krakow",
        "category": "software",
    },
    {
        "name": "Gdansk Engineering",
        "vat_id": "PL4567891230",
        "country": "PL",
        "city": "Gdansk",
        "category": "hardware",
    },
    {
        "name": "Wroclaw Consulting",
        "vat_id": "PL3216549870",
        "country": "PL",
        "city": "Wroclaw",
        "category": "consulting",
    },
    {
        "name": "Poznan Training Center",
        "vat_id": "PL1472583690",
        "country": "PL",
        "city": "Poznan",
        "category": "training",
    },
    # Irish Companies
    {
        "name": "Dublin Software Ltd.",
        "vat_id": "IE1234567WA",
        "country": "IE",
        "city": "Dublin",
        "category": "software",
    },
    {
        "name": "Cork Tech Solutions",
        "vat_id": "IE9876543WB",
        "country": "IE",
        "city": "Cork",
        "category": "hardware",
    },
    {
        "name": "Galway Consulting Ltd.",
        "vat_id": "IE4567891WC",
        "country": "IE",
        "city": "Galway",
        "category": "consulting",
    },
    {
        "name": "Limerick IT Services",
        "vat_id": "IE3216549WD",
        "country": "IE",
        "city": "Limerick",
        "category": "software",
    },
    # Portuguese Companies
    {
        "name": "Lisboa Tecnologia Lda",
        "vat_id": "PT123456789",
        "country": "PT",
        "city": "Lisbon",
        "category": "software",
    },
    {
        "name": "Porto Consulting Lda",
        "vat_id": "PT987654321",
        "country": "PT",
        "city": "Porto",
        "category": "consulting",
    },
    {
        "name": "Coimbra Engineering Lda",
        "vat_id": "PT456789123",
        "country": "PT",
        "city": "Coimbra",
        "category": "installation",
    },
    # Danish Companies
    {
        "name": "Copenhagen Tech ApS",
        "vat_id": "DK12345678",
        "country": "DK",
        "city": "Copenhagen",
        "category": "software",
    },
    {
        "name": "Aarhus IT Solutions",
        "vat_id": "DK98765432",
        "country": "DK",
        "city": "Aarhus",
        "category": "hardware",
    },
    {
        "name": "Odense Consulting ApS",
        "vat_id": "DK45678912",
        "country": "DK",
        "city": "Odense",
        "category": "consulting",
    },
    # Finnish Companies
    {
        "name": "Helsinki Software Oy",
        "vat_id": "FI12345678",
        "country": "FI",
        "city": "Helsinki",
        "category": "software",
    },
    {
        "name": "Tampere Tech Oy",
        "vat_id": "FI98765432",
        "country": "FI",
        "city": "Tampere",
        "category": "hardware",
    },
    {
        "name": "Turku Consulting Oy",
        "vat_id": "FI45678912",
        "country": "FI",
        "city": "Turku",
        "category": "consulting",
    },
    # Czech Companies
    {
        "name": "Praha Software s.r.o.",
        "vat_id": "CZ12345678",
        "country": "CZ",
        "city": "Prague",
        "category": "software",
    },
    {
        "name": "Brno Tech Solutions",
        "vat_id": "CZ98765432",
        "country": "CZ",
        "city": "Brno",
        "category": "hardware",
    },
    {
        "name": "Ostrava Engineering",
        "vat_id": "CZ45678912",
        "country": "CZ",
        "city": "Ostrava",
        "category": "installation",
    },
    # Greek Companies
    {
        "name": "Athens Tech Solutions",
        "vat_id": "EL123456789",
        "country": "GR",
        "city": "Athens",
        "category": "software",
    },
    {
        "name": "Thessaloniki Consulting",
        "vat_id": "EL987654321",
        "country": "GR",
        "city": "Thessaloniki",
        "category": "consulting",
    },
    # Hungarian Companies
    {
        "name": "Budapest Software Kft",
        "vat_id": "HU12345678",
        "country": "HU",
        "city": "Budapest",
        "category": "software",
    },
    {
        "name": "Debrecen IT Services",
        "vat_id": "HU98765432",
        "country": "HU",
        "city": "Debrecen",
        "category": "hardware",
    },
    # Romanian Companies
    {
        "name": "Bucharest Tech SRL",
        "vat_id": "RO12345678",
        "country": "RO",
        "city": "Bucharest",
        "category": "software",
    },
    {
        "name": "Cluj IT Solutions",
        "vat_id": "RO98765432",
        "country": "RO",
        "city": "Cluj-Napoca",
        "category": "software",
    },
    # Additional diverse suppliers
    {
        "name": "Luxembourg Consulting SARL",
        "vat_id": "LU12345678",
        "country": "LU",
        "city": "Luxembourg",
        "category": "consulting",
    },
    {
        "name": "Cyprus Tech Ltd",
        "vat_id": "CY12345678X",
        "country": "CY",
        "city": "Nicosia",
        "category": "software",
    },
    {
        "name": "Malta IT Services",
        "vat_id": "MT12345678",
        "country": "MT",
        "city": "Valletta",
        "category": "software",
    },
    {
        "name": "Slovenia Engineering d.o.o.",
        "vat_id": "SI12345678",
        "country": "SI",
        "city": "Ljubljana",
        "category": "installation",
    },
    {
        "name": "Slovakia Software s.r.o.",
        "vat_id": "SK1234567890",
        "country": "SK",
        "city": "Bratislava",
        "category": "software",
    },
    {
        "name": "Estonia Digital OÜ",
        "vat_id": "EE123456789",
        "country": "EE",
        "city": "Tallinn",
        "category": "software",
    },
    {
        "name": "Latvia Tech SIA",
        "vat_id": "LV12345678901",
        "country": "LV",
        "city": "Riga",
        "category": "hardware",
    },
    {
        "name": "Lithuania Consulting UAB",
        "vat_id": "LT123456789012",
        "country": "LT",
        "city": "Vilnius",
        "category": "consulting",
    },
    {
        "name": "Croatia Engineering d.o.o.",
        "vat_id": "HR12345678901",
        "country": "HR",
        "city": "Zagreb",
        "category": "installation",
    },
    {
        "name": "Bulgaria Software EOOD",
        "vat_id": "BG123456789",
        "country": "BG",
        "city": "Sofia",
        "category": "software",
    },
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


def generate_invoice_number(index: int, supplier: dict[str, Any], *, rng: Random) -> str:
    """Generate a realistic invoice number."""
    prefix_map = {
        "GB": ["INV", "SI", "IV"],
        "DE": ["RE", "RG", "INV"],
        "FR": ["FA", "FC", "INV"],
        "NL": ["F", "INV", "FN"],
        "BE": ["F", "INV", "FB"],
        "SE": ["F", "INV", "FS"],
        "IT": ["FT", "FA", "INV"],
        "ES": ["FA", "FC", "INV"],
        "AT": ["RE", "AR", "INV"],
        "PL": ["FV", "FA", "INV"],
    }

    prefixes = prefix_map.get(supplier["country"], ["INV"])
    prefix = rng.choice(prefixes)
    year = rng.choice(["2025", "2026"])
    number = str(index).zfill(4)

    return f"{prefix}-{year}-{number}"


def generate_invoice_date(
    temporal_problem: bool = False, *, rng: Random
) -> tuple[datetime, datetime]:
    """Generate invoice date and supply date."""
    if temporal_problem:
        # Before project start
        invoice_date = datetime(2024, 11, 15)
        supply_date = datetime(2024, 11, 1)
    else:
        # Within valid range
        days_range = (INVOICE_DATE_RANGE_END - INVOICE_DATE_RANGE_START).days
        invoice_date = INVOICE_DATE_RANGE_START + timedelta(days=rng.randint(0, days_range))
        supply_date = invoice_date - timedelta(days=rng.randint(1, 14))

    return invoice_date, supply_date


def generate_line_items(
    category: str, target_amount: float, *, rng: Random
) -> list[dict[str, Any]]:
    """Generate realistic line items for an invoice."""
    templates = SERVICE_TEMPLATES.get(category, SERVICE_TEMPLATES["consulting"])
    items = []
    remaining = target_amount

    while remaining > 100:
        template = rng.choice(templates)
        description_template, min_price, max_price = template

        # Generate description with placeholders filled
        description = description_template.format(
            product=rng.choice(PRODUCTS),
            model=rng.choice(MODELS),
            event=rng.choice(EVENTS),
            destination=rng.choice(DESTINATIONS),
            qty=rng.randint(2, 10),
            hours=rng.randint(10, 80),
            days=rng.randint(1, 5),
        )

        unit_price = round(rng.uniform(min_price, min(max_price, remaining)), 2)
        quantity = 1 if unit_price > 1000 else rng.randint(1, 5)
        amount = round(unit_price * quantity, 2)

        if amount > remaining * 1.2:
            amount = round(remaining * rng.uniform(0.3, 0.9), 2)
            quantity = 1
            unit_price = amount

        items.append(
            {
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
            }
        )

        remaining -= amount

        if len(items) >= 5 or remaining < 200:
            break

    return items


def get_vat_rate(country: str) -> float:
    """Get VAT rate by country."""
    vat_rates = {
        "GB": 0.20,
        "DE": 0.19,
        "FR": 0.20,
        "NL": 0.21,
        "BE": 0.21,
        "SE": 0.25,
        "IT": 0.22,
        "ES": 0.21,
        "AT": 0.20,
        "PL": 0.23,
        "IE": 0.23,
        "PT": 0.23,
        "DK": 0.25,
        "FI": 0.24,
        "CZ": 0.21,
        "GR": 0.24,
        "HU": 0.27,
        "RO": 0.19,
        "LU": 0.17,
        "CY": 0.19,
        "MT": 0.18,
        "SI": 0.22,
        "SK": 0.20,
        "EE": 0.22,
        "LV": 0.21,
        "LT": 0.21,
        "HR": 0.25,
        "BG": 0.20,
        "RU": 0.00,  # No VAT for Russian supplier
    }
    return vat_rates.get(country, 0.20)


def get_currency(country: str) -> str:
    """Get currency by country."""
    currencies = {
        "GB": "GBP",
        "SE": "SEK",
        "DK": "DKK",
        "PL": "PLN",
        "CZ": "CZK",
        "HU": "HUF",
        "RO": "RON",
        "BG": "BGN",
        "RU": "EUR",  # Use EUR for clarity
    }
    return currencies.get(country, "EUR")


def generate_invoice(
    index: int, supplier: dict[str, Any], problem_type: str | None = None, *, rng: Random
) -> dict[str, Any]:
    """Generate a complete invoice record."""

    # Determine dates
    temporal_problem = problem_type == "temporal"
    invoice_date, supply_date = generate_invoice_date(temporal_problem, rng=rng)

    # Determine work package
    wp_key = rng.choice(list(WORK_PACKAGES.keys()))
    work_package = WORK_PACKAGES[wp_key]

    # Override category for subject relevance problem
    category = supplier.get("category", "consulting")
    if problem_type == "subject_relevance":
        category = "catering"

    # Generate amounts
    base_amount = round(rng.uniform(500, 25000), 2)
    if problem_type == "sanctions":
        base_amount = 6450.00
    elif problem_type == "ted_concentration":
        base_amount = 24000.00
    elif problem_type == "duplicate":
        base_amount = 9840.00
    elif problem_type == "invalid_vat":
        base_amount = 1320.00
    elif problem_type == "subject_relevance":
        base_amount = 3600.00
    elif problem_type == "temporal":
        base_amount = 15625.00

    vat_rate = get_vat_rate(supplier["country"])
    if problem_type == "sanctions":
        vat_rate = 0.0  # Russian supplier, no VAT

    line_items = generate_line_items(category, base_amount, rng=rng)
    subtotal = sum(item["amount"] for item in line_items)
    vat_amount = round(subtotal * vat_rate, 2)
    total = round(subtotal + vat_amount, 2)

    currency = get_currency(supplier["country"])

    # Generate invoice number
    invoice_number = generate_invoice_number(index, supplier, rng=rng)

    # Build invoice record
    invoice = {
        "id": f"DOC-{str(index).zfill(5)}",
        "invoice_number": invoice_number,
        "invoice_date": invoice_date.strftime("%Y-%m-%d"),
        "supply_date": supply_date.strftime("%Y-%m-%d"),
        "due_date": (invoice_date + timedelta(days=30)).strftime("%Y-%m-%d"),
        "supplier": {
            "name": supplier["name"],
            "vat_id": supplier.get("vat_id", ""),
            "country": supplier["country"],
            "city": supplier.get("city", ""),
            "address": supplier.get(
                "address", f"{rng.randint(1, 200)} Business Street, {supplier.get('city', 'City')}"
            ),
        },
        "beneficiary": {
            "name": "European Green Technology Institute",
            "vat_id": "BE0123456789",
            "country": "BE",
            "city": "Brussels",
            "address": "42 Innovation Boulevard, 1000 Brussels",
        },
        "line_items": line_items,
        "amounts": {
            "subtotal": subtotal,
            "vat_rate": vat_rate,
            "vat_amount": vat_amount,
            "total": total,
            "currency": currency,
        },
        "project": {
            "work_package": wp_key,
            "work_package_name": work_package["name"],
            "category": category,
        },
        "metadata": {
            "problem_type": problem_type,
            "is_problematic": problem_type is not None,
        },
    }

    return invoice
