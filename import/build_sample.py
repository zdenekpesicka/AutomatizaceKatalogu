"""Etapa 1b: sestavi ukazkovy data/katalog.json z 30-50 skutecnych zaznamu pro schvaleni schematu."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mpsv import load_rpss, filter_senior_services, build_place_groups  # noqa: E402
from ciselniky import load_all  # noqa: E402

ROOT = Path(__file__).parent.parent
CACHE = ROOT / "_cache"
TODAY = "2026-09-02"

with open(ROOT / "config" / "kategorie-mapovani.json", encoding="utf-8") as f:
    KAT_CFG = json.load(f)

DRUH_TO_KAT = {}
for entry in KAT_CFG["socialniSluzby"]:
    DRUH_TO_KAT[entry["druh"]] = entry["kategorie"]


def kategorie_pro_sluzbu(druh_id: str, formy: list[str]) -> set[str]:
    mapovani = DRUH_TO_KAT.get(druh_id)
    if not mapovani:
        return set()
    out = set()
    for forma in formy:
        out |= set(mapovani.get(forma, []))
    return out


def mpsv_sluzba_to_output(s: dict, typ_kapacity_nazvy: dict, druhy_nazvy: dict) -> dict:
    # Kapacita zustava svazana s formou, ktera ji ma (oprava feedbacku vyvojare - viz mpsv.py).
    formy_out = [
        {
            "forma": f["formaId"].split("/")[-1],
            "kapacitaRegistrovana": [
                {
                    "typ": k["typ"].split("/")[-1],
                    "typNazev": typ_kapacity_nazvy.get(k["typ"], "?"),
                    "pocet": k["pocet"],
                }
                for k in f["kapacity"]
            ],
        }
        for f in s["kapacityPodleFormy"]
    ]
    weby = s["kontaktySluzba"]["weby"] or s["kontaktyPoskytovatel"]["weby"]
    emaily = s["kontaktySluzba"]["emaily"] or s["kontaktyPoskytovatel"]["emaily"]
    telefony = s["kontaktySluzba"]["telefony"] or s["kontaktyPoskytovatel"]["telefony"]
    return {
        "id": f"mpsv-{s['portalId']}",
        "zdroj": "MPSV",
        "nazev": s["nazevZarizeni"],
        "poskytovatel": {
            "nazev": s["poskytovatelNazev"],
            "ico": s["poskytovatelIco"],
        },
        "druhSluzby": {"kod": s["druhSocialniSluzby"], "nazev": druhy_nazvy.get(s["druhSocialniSluzby"], "?")},
        "formy": formy_out,
        "datumPoskytovaniOd": s["datumPoskytovaniOd"],
        "datumPoskytovaniDo": s["datumPoskytovaniDo"],
        "kontakt": {"weby": weby, "emaily": emaily, "telefony": telefony},
    }


def uzis_sluzba_to_output(r: dict) -> dict:
    ico = r["poskytovatel_ICO"].zfill(8)
    weby = [r["poskytovatel_web"]] if r["poskytovatel_web"] else []
    emaily = [r["poskytovatel_email"]] if r["poskytovatel_email"] else []
    telefony = [r["poskytovatel_telefon"]] if r["poskytovatel_telefon"] else []
    obor = (r["ZZ_obor_pece"] or "").split(",")[0].strip() or None
    return {
        "id": f"uzis-{r['ZZ_ID']}",
        "zdroj": "UZIS",
        "nazev": r["ZZ_nazev"],
        "poskytovatel": {"nazev": r["poskytovatel_nazev"], "ico": ico},
        "druhSluzby": {"kod": r["ZZ_druh_kod"], "nazev": r["ZZ_druh_nazev"]},
        "oborPece": obor,
        "kontakt": {"weby": weby, "emaily": emaily, "telefony": telefony},
    }


def parse_uzis_gps(wkt: str) -> tuple[float, float] | None:
    """CLAUDE.md 3.1: prvni cislo je zemepisna sirka, druhe delka (obracene proti standardu WKT)."""
    if not wkt or not wkt.startswith("POINT("):
        return None
    inner = wkt[len("POINT("):-1]
    lat_str, lng_str = inner.split(" ")
    lat, lng = float(lat_str), float(lng_str)
    if not (48 <= lat <= 52 and 12 <= lng <= 19):
        return None
    return lat, lng


def main():
    items = load_rpss(CACHE / "rpss.json")
    senior = filter_senior_services(items)
    places = build_place_groups(senior, TODAY)
    ciselniky = load_all(CACHE)

    with open(CACHE / "typy-kapacity-socialni-sluzby.json", encoding="utf-8") as f:
        typ_kapacity_nazvy = {i["id"]: i["nazev"]["cs"] for i in json.load(f)["polozky"]}
    with open(CACHE / "druhy-socialni-sluzby.json", encoding="utf-8") as f:
        druhy_nazvy = {i["id"]: i["nazev"]["cs"] for i in json.load(f)["polozky"]}

    with open(CACHE / "vzorek_vyber.json", encoding="utf-8") as f:
        vybrane_klice = json.load(f)
    with open(CACHE / "vzorek_souradnice.json", encoding="utf-8") as f:
        souradnice_map = json.load(f)
    with open(CACHE / "uzis_vzorek.json", encoding="utf-8") as f:
        uzis_vzorek = json.load(f)

    def addr_text(adresa):
        if not adresa:
            return None
        obec_id = (adresa.get("obec") or {}).get("id")
        okres_id = (adresa.get("okres") or {}).get("id")
        kraj_id = (adresa.get("kraj") or {}).get("id")
        cast_id = (adresa.get("castObce") or {}).get("id")
        return {
            "ulice": (adresa.get("ulice") or {}).get("nazev"),
            "cisloDomovni": adresa.get("cisloDomovni"),
            "cisloOrientacni": adresa.get("cisloOrientacni"),
            "psc": adresa.get("psc"),
            "obec": ciselniky["obec"].get(obec_id),
            "castObce": ciselniky["cast_obce"].get(cast_id),
            "okres": ciselniky["okres"].get(okres_id),
            "kraj": ciselniky["kraj"].get(kraj_id),
        }

    mista_out = []
    for k_str in vybrane_klice:
        k = int(k_str)
        p = places[k]
        souradnice = souradnice_map.get(k_str)
        sluzby_out = [mpsv_sluzba_to_output(s, typ_kapacity_nazvy, druhy_nazvy) for s in p["sluzby"]]
        kategorie = set()
        for s in p["sluzby"]:
            kategorie |= kategorie_pro_sluzbu(s["druhSocialniSluzby"], s["formy"])
        mista_out.append({
            "id": f"misto-{k}",
            "kodAdresnihoMista": k,
            "adresa": addr_text(p["adresa"]),
            "souradnice": {"lat": souradnice["lat"], "lng": souradnice["lng"]} if souradnice else {"lat": None, "lng": None},
            "kategorie": sorted(kategorie),
            "poskytujeZdravotniPeci": False,
            "sluzby": sluzby_out,
        })

    # zvlastni pripad: domov Senevida Nepomuk dostane priznak poskytujeZdravotniPeci (parovani pres ICO,
    # ilustrativni pro schvaleni schematu - presne parovani ICO+RUIAN resi az etapa 2)
    for m in mista_out:
        if m["id"] == "misto-79121519":
            m["poskytujeZdravotniPeci"] = True

    # ryze UZIS mista (hospic, LDN, nemocnice nasledne pece, rehabilitacni ustav) - bez MPSV protejsku
    for skupina in ["hospic", "ldn", "nnp", "rehab"]:
        for r in uzis_vzorek[skupina]:
            coords = parse_uzis_gps(r["ZZ_GPS"])
            mista_out.append({
                "id": f"misto-uzis-{r['ZZ_misto_poskytovani_ID']}",
                "kodAdresnihoMista": int(r["ZZ_RUIAN_kod"]) if r["ZZ_RUIAN_kod"] else None,
                "adresa": {
                    "ulice": r["ZZ_ulice"] or None,
                    "cisloDomovni": None,
                    "cisloOrientacni": r["ZZ_cislo_domovni_orientacni"] or None,
                    "psc": r["ZZ_PSC"] or None,
                    "obec": r["ZZ_obec"] or None,
                    "castObce": None,
                    "okres": r["ZZ_okres_nazev"] or None,
                    "kraj": r["ZZ_kraj_nazev"] or None,
                },
                "souradnice": {"lat": coords[0], "lng": coords[1]} if coords else {"lat": None, "lng": None},
                "kategorie": ["zdravi"],
                "poskytujeZdravotniPeci": False,
                "sluzby": [uzis_sluzba_to_output(r)],
            })

    # zvlastni pripad: sluzba bez jakekoli adresy (aktivni zarizeni, adresa je v datech null) -
    # demonstruje zaznam bez souradnic a nahradni ID bez kodAdresnihoMista (dorazuje eseste v etape 3)
    with open(CACHE / "bez_adresy_priklad.json", encoding="utf-8") as f:
        bez_adresy = json.load(f)
    sluzba_bez_adresy = mpsv_sluzba_to_output(bez_adresy, typ_kapacity_nazvy, druhy_nazvy)
    mista_out.append({
        "id": f"misto-bezadresy-{bez_adresy['portalId']}",
        "kodAdresnihoMista": None,
        "adresa": None,
        "souradnice": {"lat": None, "lng": None},
        "kategorie": sorted(kategorie_pro_sluzbu(bez_adresy["druhSocialniSluzby"], bez_adresy["formy"])),
        "poskytujeZdravotniPeci": False,
        "sluzby": [sluzba_bez_adresy],
    })

    out = {"verzeSchematu": "1.0.0", "mista": mista_out}
    with open(ROOT / "data" / "katalog.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Zapsano {len(mista_out)} mist do data/katalog.json")


if __name__ == "__main__":
    main()
