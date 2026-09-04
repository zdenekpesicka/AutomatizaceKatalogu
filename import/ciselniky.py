"""Nacitani ciselniku MPSV (vecne i uzemni) a lookup id -> nazev."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

BASE_URL = "https://data.mpsv.cz/od/soubory/ciselniky/{name}.json"

# nazev souboru na data.mpsv.cz -> lokalni klic
FILES = {
    "druhy-socialni-sluzby": "druh_socialni_sluzby",
    "cilove-skupiny-osoby": "cilova_skupina_osoby",
    "formy-soc-sluzby": "forma_socialni_sluzby",
    "kraje": "kraj",
    "okresy": "okres",
    "obce": "obec",
    "casti-obci": "cast_obce",
    "typy-kapacity-socialni-sluzby": "typ_kapacity_socialni_sluzby",
    "vekove-skupiny-osoby": "vekova_skupina_osoby",
}


def load_ciselnik(path: Path) -> Dict[str, str]:
    """Nacte jeden ciselnik a vrati mapovani id -> nazev.cs."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for item in data["polozky"]:
        nazev = item.get("nazev")
        out[item["id"]] = nazev["cs"] if isinstance(nazev, dict) else nazev
    return out


def load_all(cache_dir: Path) -> Dict[str, Dict[str, str]]:
    """Nacte vsechny ciselniky z cache_dir podle FILES a vrati slovnik lokalni_klic -> {id: nazev}."""
    result = {}
    for filename, key in FILES.items():
        path = cache_dir / f"{filename}.json"
        result[key] = load_ciselnik(path)
    return result


def load_kody(cache_dir: Path) -> Dict[str, Dict[str, str]]:
    """Nacte oficialni uzemni kody (id -> kod) pro obec/okres/kraj z uz stahovanych uzemnich ciselniku
    MPSV. Pro obec CSU kod (napr. Praha 554782), pro okres LAU1 kod (napr. CZ0100), pro kraj NUTS3
    kod (napr. CZ010) - tento format se shoduje se sloupci ZZ_okres_kod/ZZ_kraj_kod v datech UZIS
    (overeno na vzorku), takze kody jsou stejneho tvaru napric obema zdroji. Obec v UZIS CSV vlastni
    kod nema, tam zustane null."""
    with open(cache_dir / "obce.json", encoding="utf-8") as f:
        obec = {item["id"]: item.get("kod") for item in json.load(f)["polozky"]}
    with open(cache_dir / "okresy.json", encoding="utf-8") as f:
        okres = {item["id"]: item.get("kodLau") for item in json.load(f)["polozky"]}
    with open(cache_dir / "kraje.json", encoding="utf-8") as f:
        kraj = {item["id"]: item.get("kodNuts3") for item in json.load(f)["polozky"]}
    return {"obec": obec, "okres": okres, "kraj": kraj}
