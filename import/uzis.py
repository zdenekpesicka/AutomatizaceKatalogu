"""Transformace dat NRPZS (UZIS): filtr relevantnich druhu, oprava souradnic, parovani s MPSV."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Container, Dict, Iterable, List, Optional, Tuple

# CLAUDE.md 2.2 - relevantni druhy zarizeni pro seniorsky katalog. Seznam zamerne NENI tady, ale
# v config/kategorie-mapovani.json (klice zdravotniSluzby.druhyZarizeni), aby existoval jen jednou:
# tyz seznam urcuje filtr relevance i zarazeni do kategorie a driv byl na obou mistech zvlast,
# takze config sliboval paku, kterou kod necetl. Viz CLAUDE.md 4.3 a filter_relevant nize.

# CLAUDE.md 3.4 - tento druh se nikdy neposila jako samostatny zaznam, jen jako priznak
DRUH_ZDRAVOTNI_PECE_V_USTAVU = "Zdravotní péče v ústavech sociální p."

# CLAUDE.md 3.5 - domaci pece bez kontaktu se vyrazuje, pobytova zarizeni ne
DRUHY_VYZADUJICI_KONTAKT = {"Domácí zdravotní péče"}

CZ_LAT_RANGE = (48.0, 52.0)
CZ_LNG_RANGE = (12.0, 19.0)


def load_nrpzs(path: Path) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_obor_pece(hodnota: Optional[str]) -> List[str]:
    """CLAUDE.md 3.3 - ZZ_obor_pece je vicehodnotove pole oddelene carkou, pred filtrovanim rozpadnout."""
    if not hodnota:
        return []
    return [o.strip() for o in hodnota.split(",") if o.strip()]


def is_hospic_like(row: Dict[str, Any]) -> bool:
    """CLAUDE.md 3.2 - hospic nelze filtrovat jen podle druhu zarizeni, kombinuje druh+obor+text nazvu.

    Zamerne se NEPOUZIVA ve filter_relevant. Overeno na realnych datech (zaznam v
    CLAUDE.md sekce 8): kdyby tato funkce rozsirovala filtr, pridalo by to cca 118 zaznamu s druhem
    typu "Nemocnice", "Fakultni nemocnice" nebo "Samostatna ordinace lekare specialisty" - tedy cele
    nemocnice a soukrome ordinace jen proto, ze maji oddeleni/obor paliativni mediciny. To by pro
    seniorsky katalog bylo spatne (nejde o domovy/hospice, ale o velke obecne instituce). Domaci
    hospice uz jsou pokryte pres druh "Domácí zdravotní péče" v configu. Funkce zustava jako
    zdokumentovany vysledek tohoto overeni, ne jako zapomenuty nedodelek."""
    if row["ZZ_druh_nazev"] == "Hospic":
        return True
    if "hospic" in (row.get("ZZ_nazev") or "").lower():
        return True
    obory = [o.lower() for o in split_obor_pece(row.get("ZZ_obor_pece"))]
    if any("paliativní medicína" in o for o in obory):
        return True
    return False


def parse_gps(wkt: Optional[str]) -> Optional[Tuple[float, float]]:
    """CLAUDE.md 3.1 - v UZIS je v WKT POINT() prvni cislo zemepisna sirka, druhe delka (obracene proti
    standardu). Vraci (lat, lng) po overeni proti bounding boxu CR, jinak None."""
    if not wkt or not wkt.startswith("POINT("):
        return None
    inner = wkt[len("POINT("):-1]
    try:
        lat_str, lng_str = inner.split(" ")
        lat, lng = float(lat_str), float(lng_str)
    except ValueError:
        return None
    if not (CZ_LAT_RANGE[0] <= lat <= CZ_LAT_RANGE[1] and CZ_LNG_RANGE[0] <= lng <= CZ_LNG_RANGE[1]):
        return None
    return lat, lng


def has_contact(row: Dict[str, Any]) -> bool:
    return bool(row.get("poskytovatel_web") or row.get("poskytovatel_email") or row.get("poskytovatel_telefon"))


def filter_relevant(
    rows: Iterable[Dict[str, Any]], relevantni_druhy: Container[str]
) -> List[Dict[str, Any]]:
    """CLAUDE.md 2.2 + 3.5: relevantni druhy, domaci pece jen s kontaktem, ostatni i bez.

    relevantni_druhy prichazi z configu (klice zdravotniSluzby.druhyZarizeni), ne z konstanty tady.
    """
    out = []
    for r in rows:
        if r["ZZ_druh_nazev"] not in relevantni_druhy:
            continue
        if r["ZZ_druh_nazev"] in DRUHY_VYZADUJICI_KONTAKT and not has_contact(r):
            continue
        out.append(r)
    return out


def split_zaznamy_a_priznaky(rows: Iterable[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """CLAUDE.md 3.4: 'Zdravotni pece v ustavech socialni pece' se neposila jako zaznam, jen jako priznak
    u existujiciho mista. Vraci (samostatne_zaznamy, priznaky_pro_existujici_mista)."""
    zaznamy, priznaky = [], []
    for r in rows:
        if r["ZZ_druh_nazev"] == DRUH_ZDRAVOTNI_PECE_V_USTAVU:
            priznaky.append(r)
        else:
            zaznamy.append(r)
    return zaznamy, priznaky


def build_mpsv_index(places: Dict[Any, Dict[str, Any]]) -> Dict[Tuple[str, str], Any]:
    """Index (ICO, kodAdresnihoMista-jako-text) -> klic mista, pro parovani s UZIS.
    Parovani vyhradne pres ICO + RUIAN kod, nikdy pres nazev (CLAUDE.md Etapa 2, bod 6)."""
    index = {}
    for misto_klic, misto in places.items():
        if not isinstance(misto_klic, int):
            continue
        for s in misto["sluzby"]:
            ico = s.get("poskytovatelIco")
            if ico:
                index[(ico, str(misto_klic))] = misto_klic
    return index


def match_uzis_row(row: Dict[str, Any], mpsv_index: Dict[Tuple[str, str], Any]) -> Optional[Any]:
    ico = row.get("poskytovatel_ICO")
    ruian = row.get("ZZ_RUIAN_kod")
    if not ico or not ruian:
        return None
    return mpsv_index.get((ico, ruian))
