aktionen_mapping = {
    "Fahrrad fahren": {
        "name": "Fahrrad fahren",
        "klimapunkte": 0.21,
        "mengeBeschreibung": "gefahrene Kilometer",
        "anmerkung": "statt Auto",
        "date": True
    },
    "ÖPNV nutzen": {
        "name": "ÖPNV nutzen",
        "klimapunkte": 0.11,
        "mengeBeschreibung": "gefahrene Kilometer",
        "anmerkung": "statt Auto",
        "date": True
    },
    "Festseife verwenden": {
        "name": "Festseife verwenden",
        "klimapunkte": 2.0,
        "date": False
    },
    "Mehrwegbecher verwenden": {
        "name": "Mehrwegbecher verwenden",
        "klimapunkte": 0.5,
        "anmerkung": "statt Einwegbecher",
        "date": False
    }
}

for aktion in aktionen_mapping:
    print(aktionen_mapping[aktion]["name"])
    print(aktionen_mapping[aktion]["klimapunkte"])
    print(aktionen_mapping[aktion].get("mengeBeschreibung", None))
    print(aktionen_mapping[aktion].get("anmerkung", None))
    print(aktionen_mapping[aktion]["date"])
    print("-----")