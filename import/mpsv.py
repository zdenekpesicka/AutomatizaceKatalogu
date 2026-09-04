"""Transformace dat RPSS (MPSV): filtr senioru, rozpad na zarizeni, seskupeni podle mista."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

CILOVA_SKUPINA_SENIORI = "CilovaSkupinaOsoby/24"


def load_rpss(path: Path) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["polozky"]


def filter_senior_services(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Vrati jen sluzby s cilovou skupinou senori (CilovaSkupinaOsoby/24)."""
    out = []
    for it in items:
        skupiny = it.get("ciloveSkupiny") or []
        if any(cs["cilovaSkupina"]["id"] == CILOVA_SKUPINA_SENIORI for cs in skupiny):
            out.append(it)
    return out


def is_zarizeni_active(z: Dict[str, Any], today: str) -> bool:
    """Zarizeni je aktivni, pokud jiz zacalo poskytovat a jeste neskoncilo (poskytujeDo null nebo v budoucnu)."""
    od = z.get("poskytujeOd")
    do = z.get("poskytujeDo")
    if od and od > today:
        return False
    if do and do <= today:
        return False
    return True


def dedupe_zarizeni(zarizeni: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Zarizeni se v datech casto opakuje se stejnym nazvem a adresou (viz CLAUDE.md pripad Carvac).
    Deduplikace podle (nazev, kodAdresnihoMista, poskytujeOd, poskytujeDo)."""
    seen = set()
    out = []
    for z in zarizeni:
        adresa = z.get("adresa") or {}
        key = (z.get("nazev"), adresa.get("kodAdresnihoMista"), z.get("poskytujeOd"), z.get("poskytujeDo"))
        if key in seen:
            continue
        seen.add(key)
        out.append(z)
    return out


def active_zarizeni(service: Dict[str, Any], today: str) -> List[Dict[str, Any]]:
    zarizeni = service.get("zarizeni") or []
    zarizeni = [z for z in zarizeni if is_zarizeni_active(z, today)]
    return dedupe_zarizeni(zarizeni)


def contacts_for(entity: Dict[str, Any]) -> Dict[str, List[Dict[str, Optional[str]]]]:
    """Vytahne weby/emaily/telefony z objektu (sluzba nebo poskytovatel)."""
    return {
        "weby": [w["web"] for w in (entity.get("weby") or [])],
        "emaily": [e["email"] for e in (entity.get("emaily") or [])],
        "telefony": [t["telefon"] for t in (entity.get("telefony") or [])],
    }


def build_place_groups(services: List[Dict[str, Any]], today: str) -> Dict[Any, Dict[str, Any]]:
    """Seskupi aktivni zarizeni napric sluzbami podle kodAdresnihoMista (zaklad. jednotka je misto, ne registrace).

    Zarizeni bez kodAdresnihoMista jsou seskupena zvlast pod klic ('no_kod', portalId, nazev-zarizeni),
    protoze nemaji stabilni RUIAN identifikator - reseni podle sekce 3 CLAUDE.md, dorazuje v etape 3.
    """
    places: Dict[Any, Dict[str, Any]] = {}
    for service in services:
        for z in active_zarizeni(service, today):
            adresa = z.get("adresa") or {}
            kod = adresa.get("kodAdresnihoMista")
            place_key = kod if kod is not None else ("no_kod", service["portalId"], z.get("nazev"))
            place = places.setdefault(place_key, {
                "kodAdresnihoMista": kod,
                "adresa": adresa if adresa else None,
                "zarizeni_nazvy": set(),
                "sluzby": [],
            })
            place["zarizeni_nazvy"].add(z.get("nazev"))
            place["sluzby"].append({
                "portalId": service["portalId"],
                "id": service["id"],
                "identifikator": service.get("identifikator"),
                "druhSocialniSluzby": service["druhSocialniSluzby"]["id"],
                "nazevZarizeni": z.get("nazev"),
                "poskytovatelIco": (service.get("poskytovatel") or {}).get("ico"),
                "poskytovatelNazev": (service.get("poskytovatel") or {}).get("nazev"),
                "formy": [f["forma"]["id"] for f in (service.get("formy") or [])],
                # Kapacita zustava svazana s konkretni formou (oprava chyby nahlasene vyvojarem klienta,
                # puvodne se kapacity vsech forem sluzby sloucily do jednoho plocheho seznamu a ztratila
                # se informace, ktera kapacita patri ke ktere forme - viz mpsv-3443).
                "kapacityPodleFormy": [
                    {
                        "formaId": f["forma"]["id"],
                        "kapacity": [{"typ": k["typ"]["id"], "pocet": k["pocet"]} for k in (f.get("kapacity") or [])],
                    }
                    for f in (service.get("formy") or [])
                ],
                "datumPoskytovaniOd": service.get("datumPoskytovaniOd"),
                "datumPoskytovaniDo": service.get("datumPoskytovaniDo"),
                "kontaktySluzba": contacts_for(service),
                "kontaktyPoskytovatel": contacts_for(service.get("poskytovatel") or {}),
            })
    return places
