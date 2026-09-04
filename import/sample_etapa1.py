"""Etapa 1: prototyp na vzorku 200 sluzeb. Vypise souhrn a ulozi vzorek pro rucni kontrolu."""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mpsv import load_rpss, filter_senior_services, build_place_groups  # noqa: E402
from ciselniky import load_all  # noqa: E402

CACHE = Path(__file__).parent.parent / "_cache"
TODAY = "2026-09-02"


def main():
    items = load_rpss(CACHE / "rpss.json")
    senior = filter_senior_services(items)
    print(f"Senior sluzeb celkem: {len(senior)}")

    random.seed(42)
    sample = random.sample(senior, 200)

    places = build_place_groups(sample, TODAY)
    print(f"Vzorek 200 sluzeb -> {len(places)} mist")

    ciselniky = load_all(CACHE)

    # serializace pro rucni kontrolu (mnozina -> seznam)
    out = []
    for key, place in places.items():
        p = dict(place)
        p["zarizeni_nazvy"] = sorted(place["zarizeni_nazvy"])
        p["klic"] = str(key)
        out.append(p)

    with open(CACHE / "vzorek_mista.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # 10 nahodnych mist pro rucni kontrolu
    random.seed(7)
    checklist = random.sample(out, 10)
    print("\n=== 10 nahodnych mist pro rucni kontrolu proti webu poskytovatele ===")
    for p in checklist:
        adresa = p["adresa"] or {}
        obec_id = (adresa.get("obec") or {}).get("id") if adresa else None
        obec_nazev = ciselniky["obec"].get(obec_id, "?") if obec_id else "(bez adresy)"
        ulice = (adresa.get("ulice") or {}).get("nazev") if adresa else None
        cd = adresa.get("cisloDomovni") if adresa else None
        print(f"- {', '.join(p['zarizeni_nazvy'])}")
        print(f"  adresa: {ulice or ''} {cd or ''}, {obec_nazev}, PSC {adresa.get('psc') if adresa else '?'}")
        for s in p["sluzby"]:
            print(f"  sluzba: {s['poskytovatelNazev']} (ICO {s['poskytovatelIco']}), "
                  f"weby={s['kontaktySluzba']['weby'] or s['kontaktyPoskytovatel']['weby']}, "
                  f"tel={s['kontaktySluzba']['telefony'] or s['kontaktyPoskytovatel']['telefony']}")


if __name__ == "__main__":
    main()
