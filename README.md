# Planer potovanja

Flask aplikacija iz Excel podatkov sestavi stroškovni model potovanja. Uporabnik izbere število dni, število oseb, mesec, preference, prehrano, način poti do destinacije, lokalni prevoz in proračun.

## Zagon

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m travel_planner.importer data\raw\travel_data.xlsx
python app.py
```

Aplikacija se odpre na `http://127.0.0.1:5000`.

Če uporabljaš drug Python ukaz, ga zamenjaj v prvem in zadnjem ukazu.

## Podatkovni model

- `countries`: države
- `travel_options`: letalo iz Ljubljane, letalo iz Zagreba, cestni prevoz, vlak, avtobus
- `lodging_rates`: cena prenočišča glede na število oseb
- `local_transport_costs`: javni prevoz, taxi, najem avta, kolo in peš ocena
- `activity_costs`: kulturne in naravne aktivnosti
- `food_costs`: restavracije, fast food in trgovine
- `trip_requests` in `trip_recommendations`: shranjeni izračuni

## Opomba modela

Nočitve so izračunane kot `število dni - 1`, najmanj ena noč. Stroški hrane, aktivnosti in lokalnega prevoza se množijo s številom dni. Letalske, vlakovne in avtobusne karte se množijo s številom oseb, cestni prevoz pa se šteje kot skupinski strošek.
