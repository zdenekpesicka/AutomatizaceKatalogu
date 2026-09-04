"""Etapa 3: souradnice z RUIAN (CUZK) pro zaznamy z MPSV, prevod S-JTSK do WGS84.

CLAUDE.md 2.3 - aktualizovano v etape 3, viz sekce 8:
- stahovaci stranka je za captchou, skutecny zdroj je ATOM sluzba CUZK
- soubor neni jeden celostatni CSV, ale ZIP s jednim CSV na obec
- prevod souradnic je EPSG:5513, ne EPSG:5514 jak puvodne uvadel dokument (overeno na 3 bodech)
"""
from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import Dict, Optional, Set, Tuple
from xml.etree import ElementTree as ET

from pyproj import Transformer
from pyproj.aoi import AreaOfInterest

ATOM_FEED_URL = "https://atom.cuzk.gov.cz/get.ashx?theme=RUIAN-CSV-ADR-ST"
ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}

CZ_LAT_RANGE = (48.0, 52.0)
CZ_LNG_RANGE = (12.0, 19.0)

# Vyber transformace musi byt pinovany, jinak neni vystup reprodukovatelny. PROJ nabizi pro
# EPSG:5513 -> EPSG:4326 ctyri operace a tri z nich maji shodnou presnost 1,0 m: "S-JTSK to
# WGS 84" (5) a (1) s oblasti platnosti Cesko a (4) s oblasti platnosti Slovensko. Bez zadaneho
# area_of_interest vybira PROJ z teto remizy libovolne a vyber se lisi mezi verzemi PROJ i mezi
# platformami. V historii repozitare se to uz stalo: commit e3a8406 pouzil operaci (5), nasledujici
# e2a5523 operaci (4), tedy slovenskou. Posunulo to 1 807 souradnic o az ~1,5 m a vyrobilo commit
# s 1 812 "zmenenymi" misty, aniz by se ve zdrojich cokoli zmenilo - porusuje to CLAUDE.md 5.3
# a znehodnocuje zmeny.json, podle ktereho druha strana rozhoduje, co presynchronizovat.
# Ohraniceni na CR vybere operaci (5), tedy tu ceskou. Zbytkovy rozdil na poslednich bitech mezi
# verzemi PROJ resi zaokrouhleni na vystupu, viz build_katalog.SOURADNICE_DESETINNYCH_MIST.
_CR_AOI = AreaOfInterest(
    west_lon_degree=12.09, south_lat_degree=48.55, east_lon_degree=18.86, north_lat_degree=51.06
)
_TRANSFORMER = Transformer.from_crs(
    "EPSG:5513", "EPSG:4326", always_xy=True, area_of_interest=_CR_AOI
)


def resolve_download_url(atom_xml: bytes) -> str:
    """Rozparsuje ATOM feed CUZK a vrati aktualni odkaz na ZIP s adresnimi misty CR."""
    root = ET.fromstring(atom_xml)
    entry = root.find("a:entry", ATOM_NS)
    id_el = entry.find("a:id", ATOM_NS)
    return id_el.text.strip()


def load_address_points(
    zip_path: Path, needed_kody: Optional[Set[int]] = None
) -> Dict[int, Tuple[float, float, Optional[str]]]:
    """Nacte {kodAdresnihoMista: (lat, lng, kodObce)} ze ZIPu (jeden CSV na obec uvnitr).
    "Kod obce" je primo sloupec v RUIAN CSV (index 1) - vyuziva se i pro sameho zdroje ZZ_RUIAN_kod
    u cistě UZIS mist bez MPSV protejsku, ktera vlastni kod obce v UZIS datech nemaji.

    Pokud je needed_kody zadano, nacitaji a prevadeji se jen tyto kody (radove rychlejsi
    nez prevod vsech ~3 mil. bodu v CR).
    """
    out: Dict[int, Tuple[float, float, Optional[str]]] = {}
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.endswith("_ADR.csv"):
                continue
            with zf.open(name) as raw:
                text = io.TextIOWrapper(raw, encoding="cp1250", newline="")
                reader = csv.reader(text, delimiter=";")
                next(reader, None)  # hlavicka
                for row in reader:
                    if len(row) < 18:
                        continue
                    try:
                        kod_adm = int(row[0])
                    except ValueError:
                        continue
                    if needed_kody is not None and kod_adm not in needed_kody:
                        continue
                    kod_obce = row[1] or None
                    try:
                        y_sjtsk = float(row[16])
                        x_sjtsk = float(row[17])
                    except ValueError:
                        continue
                    lon, lat = _TRANSFORMER.transform(x_sjtsk, y_sjtsk)
                    if not (
                        CZ_LAT_RANGE[0] <= lat <= CZ_LAT_RANGE[1]
                        and CZ_LNG_RANGE[0] <= lon <= CZ_LNG_RANGE[1]
                    ):
                        continue
                    out[kod_adm] = (lat, lon, kod_obce)
    return out
