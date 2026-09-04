"""Aktualizovana ukazka pro vyvojare klienta po opravach z feedbacku (viz CLAUDE.md sekce 8).

Na rozdil od puvodni etapy 1b (build_sample.py, ktery stavel vzorek primo ze surovych MPSV/UZIS dat
pred existenci produkcniho behu) tento skript vybira reprezentativni podmnozinu z uz hotoveho,
schematem overeneho data/katalog.json - je tak zarucene bajtove konzistentni s produkcnim vystupem,
zadna zvlastni logika navic. Vybirame konkretni okrajove pripady, ktere byly bud v puvodni ukazce,
nebo je vyvojar explicitne zminil ve feedbacku.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


def has_service_without_web(m: dict) -> bool:
    return any(not s["kontakt"]["weby"] for s in m["sluzby"])


def has_multi_forma_kapacita(m: dict) -> bool:
    return any(
        s["zdroj"] == "MPSV" and len(s.get("formy") or []) > 1
        for s in m["sluzby"]
    )


def is_tisnova_pece(m: dict) -> bool:
    return any(s.get("druhSluzby", {}).get("kod") == "DruhSocialniSluzby/5" for s in m["sluzby"])


def main() -> None:
    data = json.load(open(ROOT / "data" / "katalog.json", encoding="utf-8"))
    mista = {m["id"]: m for m in data["mista"]}

    vybrane_ids: list[str] = []

    # Pevne vybrane, pojmenovane okrajove pripady (musi byt ve vzorku, at uz existuji nebo ne).
    pevne = [
        "misto-79121519",   # poskytujeZdravotniPeci: true (viz dokumentace)
        "misto-25965727",   # sloucene napric zdroji podle adresy (MPSV+UZIS, ruzne ICO) - novy fix
    ]
    for pid in pevne:
        if pid in mista:
            vybrane_ids.append(pid)

    # multi-forma kapacita (oprava bodu 7 z feedbacku)
    for m in data["mista"]:
        if m["id"] not in vybrane_ids and has_multi_forma_kapacita(m):
            vybrane_ids.append(m["id"])
            break

    # sluzba bez webu
    for m in data["mista"]:
        if m["id"] not in vybrane_ids and has_service_without_web(m):
            vybrane_ids.append(m["id"])
            break

    # cistě UZIS misto
    for m in data["mista"]:
        if m["id"] not in vybrane_ids and m["id"].startswith("misto-uzis-") and not m["id"].startswith("misto-uzis-bezadresy"):
            vybrane_ids.append(m["id"])
            break

    # tisnova pece
    for m in data["mista"]:
        if m["id"] not in vybrane_ids and is_tisnova_pece(m):
            vybrane_ids.append(m["id"])
            break

    # bez souradnic - preferujeme misto s kodAdresnihoMista, kde RUIAN bod chybi/neni sparovany
    # (viz CLAUDE.md sekce 8, 68/2226 pripadu), je to zajimavejsi edge case nez proste misto bez adresy
    for m in data["mista"]:
        if m["id"] not in vybrane_ids and m["souradnice"]["lat"] is None and m["kodAdresnihoMista"] is not None:
            vybrane_ids.append(m["id"])
            break
    else:
        for m in data["mista"]:
            if m["id"] not in vybrane_ids and m["souradnice"]["lat"] is None:
                vybrane_ids.append(m["id"])
                break

    # bez kodAdresnihoMista (MPSV bez adresy)
    for m in data["mista"]:
        if m["id"] not in vybrane_ids and m["id"].startswith("misto-bezadresy-"):
            vybrane_ids.append(m["id"])
            break

    # prazdna kategorie
    for m in data["mista"]:
        if m["id"] not in vybrane_ids and not m["kategorie"]:
            vybrane_ids.append(m["id"])
            break

    # poskytovatel s vice pobockami (stejne ICO na >=2 mistech)
    ico_mista: dict[str, set[str]] = {}
    for m in data["mista"]:
        for s in m["sluzby"]:
            ico_mista.setdefault(s["poskytovatel"]["ico"], set()).add(m["id"])
    for ico, ids in ico_mista.items():
        if len(ids) >= 2:
            noved = [i for i in ids if i not in vybrane_ids]
            if len(noved) >= 2:
                vybrane_ids.extend(noved[:2])
                break

    # doplneni do ~35 zaznamu rovnomerne napric kategoriemi, at ukazka pokryje domovy/terenni/bezpeci/zdravi
    kategorie_cile = ["domovy", "terenni", "bezpeci", "zdravi"]
    for kat in kategorie_cile:
        count = sum(1 for i in vybrane_ids if kat in mista[i]["kategorie"])
        for m in data["mista"]:
            if len(vybrane_ids) >= 35:
                break
            if count >= 3:
                break
            if kat in m["kategorie"] and m["id"] not in vybrane_ids:
                vybrane_ids.append(m["id"])
                count += 1

    # doplneni nahodnym vyberem do min. 30
    for m in data["mista"]:
        if len(vybrane_ids) >= 32:
            break
        if m["id"] not in vybrane_ids:
            vybrane_ids.append(m["id"])

    vybrana_mista = [mista[i] for i in vybrane_ids]
    out = {"verzeSchematu": data["verzeSchematu"], "mista": vybrana_mista}

    out_path = ROOT / "data" / "ukazka.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Zapsano {len(vybrana_mista)} mist do {out_path}")
    print("Vybrana ID:", vybrane_ids)


if __name__ == "__main__":
    main()
