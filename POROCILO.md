# Poročilo projekta: Aplikacija za izbiro potovanja na podlagi matematičnega modela

## 1. Uvod

V projektu je bila izdelana spletna aplikacija za priporočanje potovanj. Namen aplikacije je uporabniku pomagati pri izbiri destinacije glede na vnesene podatke, kot so število dni potovanja, število oseb, mesec potovanja, način prehrane, način prevoza, preference aktivnosti in razpoložljiv proračun.

Glavni cilj projekta ni bil samo prikaz podatkov, ampak izdelava matematičnega modela, ki na podlagi realnih vhodnih podatkov izračuna skupni strošek posamezne destinacije in nato izbere najprimernejše možnosti. Aplikacija uporabniku prikaže tri najboljše destinacije glede na kriterijsko funkcijo.

Projekt je izdelan kot spletna aplikacija v ogrodju Flask. Podatki so shranjeni v relacijski SQLite bazi, ki je bila ustvarjena iz vhodne Excel datoteke.

## 2. Vhodni podatki

Podatki za model so bili pripravljeni v Excel datoteki in nato uvoženi v SQLite bazo. V bazi so shranjeni podatki o:

- državah oziroma destinacijah,
- stroških poti do destinacije,
- cenah prenočišč,
- lokalnem prevozu na destinaciji,
- stroških aktivnosti,
- stroških prehrane.

Uporabnik pri uporabi aplikacije vnese:

- število dni potovanja,
- število oseb,
- mesec potovanja,
- tip aktivnosti,
- način prehrane,
- način poti do destinacije,
- način lokalnega prevoza,
- proračun.

Ti podatki predstavljajo vhodne parametre matematičnega modela.

## 3. Izračun skupnega stroška

Za vsako destinacijo se najprej izračuna skupni ocenjeni strošek potovanja. Vsaka destinacija predstavlja eno alternativo, ki jo model ovrednoti.

Skupni strošek destinacije označimo z:

```text
C_i = T_i + N_i + H_i + A_i + L_i
```

Kjer je:

```text
C_i = skupni strošek potovanja za destinacijo i
T_i = strošek poti do destinacije
N_i = strošek prenočišč
H_i = strošek prehrane
A_i = strošek aktivnosti
L_i = strošek lokalnega prevoza
```

### 3.1 Strošek poti do destinacije

Strošek poti do destinacije je odvisen od izbranega načina potovanja. Model lahko upošteva letalo iz Ljubljane, letalo iz Zagreba, vlak, avtobus ali cestni prevoz.

Pri cenah, ki so podane na osebo, se strošek pomnoži s številom oseb:

```text
T_i = cena_poti_i · število_oseb
```

Pri skupinskem strošku, na primer pri cestnem prevozu, se strošek upošteva kot skupni strošek:

```text
T_i = cena_skupinskega_prevoza_i
```

### 3.2 Strošek prenočišč

Število nočitev se izračuna iz števila dni:

```text
število_nočitev = število_dni - 1
```

Ker mora imeti tudi enodnevno potovanje vsaj osnovno vrednost v modelu, je uporabljena spodnja meja ena nočitev:

```text
število_nočitev = max(število_dni - 1, 1)
```

Strošek prenočišč je:

```text
N_i = cena_nočitve_i(število_oseb) · število_nočitev
```

### 3.3 Strošek prehrane

Strošek prehrane je odvisen od uporabnikove izbire. Uporabnik lahko izbere restavracije, hitro prehrano, trgovine ali mešano prehrano.

Za mešano prehrano je uporabljena utežena kombinacija:

```text
cena_prehrane_i = 0.40 · restavracije_i
                + 0.35 · hitra_prehrana_i
                + 0.25 · trgovine_i
```

Skupni strošek prehrane je:

```text
H_i = cena_prehrane_i · število_oseb · število_dni
```

### 3.4 Strošek aktivnosti

Aktivnosti so razdeljene na kulturne in naravne aktivnosti. Če uporabnik izbere kulturne aktivnosti, model uporabi ceno kulturnih aktivnosti. Če izbere naravne aktivnosti, uporabi ceno naravnih aktivnosti. Pri uravnoteženi izbiri se vzame povprečje obeh:

```text
cena_aktivnosti_i = (kulturne_aktivnosti_i + naravne_aktivnosti_i) / 2
```

Skupni strošek aktivnosti je:

```text
A_i = cena_aktivnosti_i · število_oseb · število_dni
```

### 3.5 Strošek lokalnega prevoza

Lokalni prevoz je odvisen od uporabnikove izbire. Model lahko upošteva javni prevoz, kolo, najem avtomobila, taxi ali hojo. Če uporabnik izbere najcenejši lokalni prevoz, model izbere najcenejšo razpoložljivo možnost.

Splošna oblika izračuna je:

```text
L_i = cena_lokalnega_prevoza_i · število_dni
```

Pri oblikah prevoza, ki se plačajo na osebo, se upošteva tudi število oseb:

```text
L_i = cena_lokalnega_prevoza_i · število_oseb · število_dni
```

## 4. Kriterijska funkcija

Po izračunu skupnega stroška model ne izbere nujno najcenejše destinacije, ampak destinacijo, ki je najbolj primerna glede na uporabnikov proračun. To je pomembno, ker uporabnik ne želi nujno najcenejšega potovanja, ampak potovanje, ki se čim bolje ujema z njegovim proračunom.

Proračun označimo z:

```text
B = uporabnikov proračun
```

Za vsako destinacijo izračunamo odstopanje od proračuna. Pri tem ločimo dve vrsti odstopanja:

```text
d_i^+ = max(0, C_i - B)
d_i^- = max(0, B - C_i)
```

Kjer je:

```text
d_i^+ = prekoračitev proračuna
d_i^- = neporabljen del proračuna
```

Prekoračitev proračuna je manj zaželena kot to, da je destinacija nekoliko pod proračunom. Zato model prekoračitev kaznuje močneje. Uporabljena je asimetrična kriterijska funkcija:

```text
K_proračun,i = (2 · d_i^+ + d_i^-) / B
```

To pomeni:

- če je destinacija čez proračun, se odstopanje pomnoži z 2,
- če je destinacija pod proračunom, se odstopanje upošteva z utežjo 1.

S tem model daje prednost destinacijam, ki so blizu proračunu, vendar bolj kaznuje tiste, ki proračun presežejo.

## 5. Večkriterijska nadgradnja modela

Da model ne upošteva samo skupnega stroška, ampak tudi strukturo stroškov, je bila dodana večkriterijska ocena. Skupna kriterijska vrednost je:

```text
Z_i = 0.80 · K_proračun,i + 0.20 · K_struktura,i
```

Kjer je:

```text
Z_i = končna kriterijska vrednost destinacije i
K_proračun,i = kriterij ujemanja s proračunom
K_struktura,i = kriterij strukture stroškov
```

Proračun ima največjo težo, saj je glavni cilj uporabnika ostati čim bližje razpoložljivemu znesku. Struktura stroškov ima manjšo težo, vendar pomaga pri ločevanju destinacij, ki imajo podoben skupni strošek.

Strukturni kriterij je sestavljen iz normaliziranih stroškovnih komponent:

```text
K_struktura,i =
0.05 · T'_i +
0.05 · N'_i +
0.04 · H'_i +
0.04 · A'_i +
0.02 · L'_i
```

Kjer so:

```text
T'_i = normaliziran strošek poti
N'_i = normaliziran strošek prenočišč
H'_i = normaliziran strošek prehrane
A'_i = normaliziran strošek aktivnosti
L'_i = normaliziran strošek lokalnega prevoza
```

Normalizacija je potrebna zato, ker so posamezne komponente v različnih velikostnih razredih. Na primer strošek poti je lahko bistveno večji od stroška lokalnega prevoza. Uporabljena je min-max normalizacija:

```text
x'_i = (x_i - min(x)) / (max(x) - min(x))
```

S tem se vse komponente pretvorijo na primerljivo lestvico od 0 do 1.

## 6. Izbira najboljših destinacij

Za vsako destinacijo se izračuna končna kriterijska vrednost:

```text
Z_i
```

Nato se destinacije razvrstijo naraščajoče po tej vrednosti:

```text
Z_1 ≤ Z_2 ≤ Z_3 ≤ ...
```

Najboljše destinacije so tiste z najmanjšo vrednostjo kriterijske funkcije. Aplikacija uporabniku prikaže prve tri destinacije:

```text
min Z_i
```

To pomeni, da prikazane destinacije niso nujno absolutno najcenejše, ampak so najboljše glede na uporabnikov proračun in strukturo stroškov.

## 7. Primer razlage rezultata

Če uporabnik vnese proračun 900 EUR, model za vsako destinacijo izračuna skupni strošek. Če je neka destinacija ocenjena na 891 EUR, potem je:

```text
C_i = 891
B = 900
d_i^+ = max(0, 891 - 900) = 0
d_i^- = max(0, 900 - 891) = 9
```

Proračunski kriterij je:

```text
K_proračun,i = (2 · 0 + 9) / 900 = 0.01
```

Ker je destinacija zelo blizu proračunu in ga ne preseže, dobi nizko kriterijsko vrednost. Takšna destinacija ima zato visoko možnost, da se uvrsti med priporočene možnosti.

Če bi bila druga destinacija 9 EUR čez proračun, bi bil izračun:

```text
d_i^+ = 9
d_i^- = 0
K_proračun,i = (2 · 9 + 0) / 900 = 0.02
```

Čeprav je odstopanje v obeh primerih 9 EUR, je destinacija nad proračunom kaznovana močneje. To je smiselno, ker je preseganje proračuna za uporabnika manj zaželeno.

## 8. Zakaj je to matematični model

Projekt predstavlja matematični model, ker vsebuje:

- množico alternativ, to so destinacije,
- vhodne parametre, ki jih določi uporabnik,
- podatkovne parametre iz baze,
- funkcijo za izračun skupnega stroška,
- kriterijsko funkcijo za ocenjevanje destinacij,
- uteži za večkriterijsko odločanje,
- algoritem za razvrščanje in izbiro najboljših rešitev.

Model ne deluje kot navaden seznam destinacij, ampak na podlagi podatkov izračuna vrednost kriterijske funkcije za vsako alternativo. Nato izbere tiste alternative, ki imajo najboljšo vrednost glede na zastavljeni cilj.

## 9. Tehnična izvedba

Aplikacija je izdelana v programskem jeziku Python z ogrodjem Flask. Podatki so shranjeni v SQLite bazi. Uporabniški vmesnik je izdelan v HTML predlogah s Tailwind CSS.

Glavni deli aplikacije so:

- `app.py`: glavna Flask aplikacija,
- `travel_planner/planner.py`: matematični model in izračun priporočil,
- `travel_planner/importer.py`: uvoz podatkov iz Excel datoteke,
- `data/travel_model.sqlite3`: SQLite baza,
- `templates`: HTML predloge za uporabniški vmesnik.

Uporabnik se lahko registrira, prijavi, vnese podatke za potovanje, izbere eno izmed predlaganih možnosti in nato vidi potrditveno stran z izbranim potovanjem ter skupno ceno.

## 10. Zaključek

V projektu je bil izdelan delujoč matematični model za priporočanje potovanj. Model za vsako destinacijo izračuna skupni strošek, nato pa uporabi večkriterijsko kriterijsko funkcijo, ki največji poudarek daje ujemanju s proračunom. Posebnost modela je, da prekoračitev proračuna kaznuje močneje kot neporabljen del proračuna.

Takšen pristop je primeren, ker uporabniku ne predlaga samo najcenejših destinacij, ampak tiste, ki se najbolje ujemajo z njegovimi finančnimi omejitvami. Model je zato uporaben za podporo odločanju pri izbiri potovanja.
