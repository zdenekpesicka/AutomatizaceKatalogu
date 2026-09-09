"""Etapa 3/4: plny produkcni beh. Sestavi data/katalog.json, data/meta.json a data/zmeny.json
z celych dat MPSV + UZIS, se souradnicemi z RUIAN. Viz CLAUDE.md sekce 6, Etapa 3 a 4.

Etapa 4 pridala pojistky podle CLAUDE.md 5.2/5.3: validace zdroje, prah 5 %, zapis jen pri
skutecne zmene obsahu (porovnano hashem PRED zapisem, ne az git diffem po nem) a skutecny
diff pro zmeny.json misto "vzdy vse pridano"."""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).parent))

from mpsv import load_rpss, filter_senior_services, build_place_groups  # noqa: E402
from uzis import (  # noqa: E402
    load_nrpzs,
    filter_relevant,
    split_zaznamy_a_priznaky,
    parse_gps,
    split_obor_pece,
)
from ciselniky import load_all, load_kody  # noqa: E402
from ruian import load_address_points  # noqa: E402

ROOT = Path(__file__).parent.parent
CACHE = ROOT / "_cache"
DATA = ROOT / "data"
TODAY = datetime.date.today().isoformat()

PRAH_ZMENY = 0.05  # CLAUDE.md 5.2 bod 3 - vice nez 5 % zmena poctu mist = nepublikovat
PRAH_BEZ_SOURADNIC = 30  # narust mist bez souradnic o vic = nepublikovat, viz pojistka nize
PRAH_STARI_ZDROJU = 50  # dni; starsi snapshot = nepublikovat, viz zkontroluj_stari_zdroju()

# Verzi nesou vsechny tri vystupni soubory, proto stoji na jednom miste - driv byla vepsana
# trikrat zvlast a mohly se rozejit. CLAUDE.md 4.2: nekompatibilni zmena zvysuje major verzi.
# 1.1.0 pridalo nepovinne sluzby[].zarizeni, tedy aditivni zmenu, ktera stavajiciho ctenare
# schematu 1.0.0 nerozbije.
VERZE_SCHEMATU = "1.2.0"

# Presnost souradnic je vlastnost rozhrani, ne jednotlivych zdroju, proto se zaokrouhluje na
# jednom miste pro oba (RUIAN i UZIS) - jinak by vystup michal ruzne presna cisla podle toho,
# odkud misto pochazi. 7 desetinnych mist je ~1,1 cm zem. sirky, coz pojme cele rozliseni zdroju:
# RUIAN uvadi S-JTSK na 2 desetinna mista v metrech (1 cm), UZIS ma v ZZ_GPS az 12 cislic, ale
# sama transformace S-JTSK->WGS84 ma deklarovanou presnost 1 m. Dalsi cislice uz nejsou informace
# o poloze, ale artefakt binarni aritmetiky - a pri zmene verze pyproj/PROJ by delaly falesne
# diffy pres cely katalog (CLAUDE.md 5.3).
SOURADNICE_DESETINNYCH_MIST = 7


def souradnice_out(coords) -> dict:
    """Souradnice pro vystup. Pole je vzdy pritomne, lat/lng jsou null, kdyz je nelze urcit
    (CLAUDE.md 4.2 - nikdy vynechane pole)."""
    if not coords:
        return {"lat": None, "lng": None}
    return {
        "lat": round(coords[0], SOURADNICE_DESETINNYCH_MIST),
        "lng": round(coords[1], SOURADNICE_DESETINNYCH_MIST),
    }


def bezadresy_id(place_key) -> str:
    """ID pro MPSV misto bez kodAdresnihoMista, tedy bez stabilniho RUIAN identifikatoru.

    Musi nest cely seskupovaci klic z mpsv.build_place_groups, tj. ('no_kod', portalId, nazev).
    Drive se pouzival jen portalId, takze vsechna bezadresni zarizeni jedne sluzby dostala shodne
    ID - porusuje to CLAUDE.md 4.2 a fakticky to slucovalo ruzna mista do jednoho pinu (napr.
    portalId 6569, Dohled na dosah z.s.: Valasske Mezirici, Praha 6, Plzen a Ostrava pod jednim ID).

    Nazev je jediny rozlisovac, ktery je k dispozici - zarizeni v MPSV nema vlastni identifikator
    (id, portalId i identifikator jsou u vsech null, overeno v datech). Dusledek: kdyz MPSV nazev
    zarizeni prepise, ID se zmeni. To ale plati uz dnes, protoze podle nazvu se i seskupuje, takze
    se tim nic nezhorsuje. Hashuje se, aby ID zustalo kratke a bez diakritiky a mezer.
    """
    _, portal_id, nazev = place_key
    otisk = hashlib.sha1((nazev or "").encode("utf-8")).hexdigest()[:8]
    return f"misto-bezadresy-{portal_id}-{otisk}"


# Zdroje, u kterych se skutecne datum zjistit nepodarilo a dosadilo se dnesni. Plni
# nacti_datum_zdrojovych_dat(), cte zkontroluj_stari_zdroju() - dosazene datum je vzdy
# cerstve, takze by nad nim byla kontrola stari slepa.
NAHRADNI_DATA: set[str] = set()


def nacti_datum_zdrojovych_dat() -> dict:
    """CLAUDE.md 5.3 - datum zdrojovych dat, ne cas behu importu. Zjisteno stahni_zdroje.py
    z Last-Modified hlavicky zdrojovych souboru (MPSV/UZIS) a z nazvu souboru (RUIAN, mesicni
    snapshot), viz _cache/mpsv_meta.json a _cache/uzis_ruian_meta.json. Pokud meta soubory
    chybi (napr. rucni beh bez stahni_zdroje.py), spadneme zpet na dnesni datum a zdroj se
    zapise do NAHRADNI_DATA - v meta.json je to jen informativni udaj, ale kontrola stari
    zdroju na nej musi spadnout, jinak by prave ta porucha, kterou ma odhalit, kontrolu
    umlcela dosazenim vzdy cerstveho data."""
    out = {}
    for meta_soubor, klice in (
        (CACHE / "mpsv_meta.json", ("mpsv",)),
        (CACHE / "uzis_ruian_meta.json", ("uzis", "ruian")),
    ):
        if meta_soubor.exists():
            data = json.loads(meta_soubor.read_text(encoding="utf-8"))
            NAHRADNI_DATA.update(data.pop("nahradniDatum", []))
            out.update(data)
        else:
            print(
                f"VAROVANI: {meta_soubor} chybi, pouzivam dnesni datum pro {'/'.join(klice)}",
                file=sys.stderr,
            )
            NAHRADNI_DATA.update(klice)
            out.update({klic: TODAY for klic in klice})
    return out


DATUM_ZDROJOVYCH_DAT = nacti_datum_zdrojovych_dat()

with open(ROOT / "config" / "kategorie-mapovani.json", encoding="utf-8") as f:
    KAT_CFG = json.load(f)

DRUH_TO_KAT = {entry["druh"]: entry["kategorie"] for entry in KAT_CFG["socialniSluzby"]}

# UZIS: druh zarizeni -> kategorie. Klice slouzi zaroven jako filtr relevance (CLAUDE.md 2.2),
# aby seznam druhu existoval jen jednou. Driv byl natvrdo v uzis.RELEVANT_DRUHY a kategorie se
# pridelovala plosne kazdemu UZIS mistu bez ohledu na druh, takze seznam v configu byl mrtvy.
UZIS_DRUH_TO_KAT = KAT_CFG["zdravotniSluzby"]["druhyZarizeni"]
UZIS_RELEVANT_DRUHY = set(UZIS_DRUH_TO_KAT)


def kategorie_pro_sluzbu(druh_id: str, formy: list[str]) -> set[str]:
    mapovani = DRUH_TO_KAT.get(druh_id)
    if not mapovani:
        return set()
    out = set()
    for forma in formy:
        out |= set(mapovani.get(forma, []))
    return out


def kategorie_pro_uzis(druh_nazev: str) -> set[str]:
    return set(UZIS_DRUH_TO_KAT.get(druh_nazev, []))


def ruian_klic(row: dict) -> int | None:
    """Kod adresniho mista z UZIS radku jako int, nebo None kdyz chybi nebo neni cislo.
    Tentyz klic, pod kterym jsou vedena MPSV mista, takze jde primo pouzit pro adresni shodu."""
    ruian = row.get("ZZ_RUIAN_kod")
    if not ruian:
        return None
    try:
        return int(ruian)
    except ValueError:
        return None


def slouc_zarizeni_jedne_sluzby(sluzby: list[dict]) -> list[tuple[dict, list[str]]]:
    """Jedna registrace = jedna polozka v sluzby[], i kdyz pod ni MPSV vede na tomtez adresnim bode
    vic zarizeni.

    build_place_groups rozpada sluzbu na zarizeni, takze na jednom miste muze tataz registrace
    skoncit vickrat - napr. mpsv-2627 ve Vamberku jako "Pecovatelska sluzba" a "Stredisko osobni
    hygieny". Overeno na plnych datech: takovych nadbytecnych polozek je 13 a lisi se VYHRADNE
    nazvem zarizeni. Vsechna ostatni pole (poskytovatel, druh, formy, kapacita, kontakty, data
    poskytovani) jsou shodna, protoze jsou vlastnosti registrace, ne zarizeni.

    Nechat je oddelene znamena dvakrat vypsat tataz cisla, a to primo skodi: kapacita je v MPSV
    registrovana na sluzbu, ne na zarizeni. Na misto-27763331 (Domov Chrudim) jsou tri registrace
    s 20, 5 a 95 luzky, tedy 120, ale mpsv-7228 byla v poli dvakrat (jednou za 2. a jednou za
    3. nadzemni podlazi), takze secteni kapacit pres sluzby[] davalo 215.

    Slucuje se podle portalId, tedy podle identifikatoru registrace, nikdy podle nazvu - nazvy
    zarizeni jsou v MPSV nepresne a rozlisovacem byt nemohou (CLAUDE.md Etapa 2, bod 6).

    Vraci dvojice (prvni vyskyt registrace, nazvy vsech jejich zarizeni na tomto miste), v poradi
    ve kterem prisly ze zdroje.
    """
    poradi: dict = {}
    for s in sluzby:
        nazev = s["nazevZarizeni"]
        zaznam = poradi.get(s["portalId"])
        if zaznam is None:
            poradi[s["portalId"]] = (s, [nazev])
        # Porovnava se orezane, protoze koncova mezera neni odlisujici udaj, jen preklep v registru
        # (mpsv-311, "Domov pro seniory Bukov, prispevkova organizace" a totez s mezerou navic).
        # Do vystupu jde nazev vzdy v puvodnim tvaru, orez slouzi jen k rozhodnuti, jestli jde
        # o dalsi zarizeni - prepisovat udaj registru nechceme.
        elif (nazev or "").strip() not in [(n or "").strip() for n in zaznam[1]]:
            zaznam[1].append(nazev)
    return list(poradi.values())


def mpsv_sluzba_to_output(s: dict, zarizeni_nazvy: list[str], typ_kapacity_nazvy: dict, druhy_nazvy: dict) -> dict:
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
    out = {
        "id": f"mpsv-{s['portalId']}",
        "zdroj": "MPSV",
        "nazev": s["nazevZarizeni"],
    }
    # Pole je jen tam, kde skutecne nese informaci navic, tedy kdyz registrace zahrnuje na tomto
    # miste vic nez jedno zarizeni. Jinak by to byl u vsech ~3300 MPSV polozek jednoprvkovy seznam
    # opakujici "nazev".
    if len(zarizeni_nazvy) > 1:
        out["zarizeni"] = zarizeni_nazvy
    out.update(
        {
            "poskytovatel": {"nazev": s["poskytovatelNazev"], "ico": s["poskytovatelIco"]},
            "druhSluzby": {"kod": s["druhSocialniSluzby"], "nazev": druhy_nazvy.get(s["druhSocialniSluzby"], "?")},
            "formy": formy_out,
            "datumPoskytovaniOd": s["datumPoskytovaniOd"],
            "datumPoskytovaniDo": s["datumPoskytovaniDo"],
            "kontakt": {"weby": weby, "emaily": emaily, "telefony": telefony},
        }
    )
    return out


def uzis_sluzba_to_output(r: dict) -> dict:
    ico = r["poskytovatel_ICO"].zfill(8)
    weby = [r["poskytovatel_web"]] if r["poskytovatel_web"] else []
    emaily = [r["poskytovatel_email"]] if r["poskytovatel_email"] else []
    telefony = [r["poskytovatel_telefon"]] if r["poskytovatel_telefon"] else []
    # ZZ_obor_pece je vicehodnotove pole oddelene carkou (CLAUDE.md 3.3). Uplny seznam jde do
    # oboryPece; oborPece drzi prvni obor a zustava kvuli kompatibilite se schematem 1.0.0.
    obory = split_obor_pece(r["ZZ_obor_pece"])
    obor = obory[0] if obory else None
    return {
        "id": f"uzis-{r['ZZ_ID']}",
        "zdroj": "UZIS",
        "nazev": r["ZZ_nazev"],
        "poskytovatel": {"nazev": r["poskytovatel_nazev"], "ico": ico},
        "druhSluzby": {"kod": r["ZZ_druh_kod"], "nazev": r["ZZ_druh_nazev"]},
        "oborPece": obor,
        "oboryPece": obory,
        "kontakt": {"weby": weby, "emaily": emaily, "telefony": telefony},
    }


def mpsv_addr_text(adresa: dict | None, ciselniky: dict, kody: dict) -> dict | None:
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
        "kodObce": kody["obec"].get(obec_id),
        "castObce": ciselniky["cast_obce"].get(cast_id),
        "okres": ciselniky["okres"].get(okres_id),
        "kodOkresu": kody["okres"].get(okres_id),
        "kraj": ciselniky["kraj"].get(kraj_id),
        "kodKraje": kody["kraj"].get(kraj_id),
    }


def uzis_addr_text(row: dict) -> dict:
    return {
        "ulice": row["ZZ_ulice"] or None,
        "cisloDomovni": None,
        "cisloOrientacni": row["ZZ_cislo_domovni_orientacni"] or None,
        "psc": row["ZZ_PSC"] or None,
        "obec": row["ZZ_obec"] or None,
        "kodObce": None,  # ZZ_obec v UZIS CSV nema vlastni kod sloupec, jen nazev (na rozdil od okresu/kraje)
        "castObce": None,
        "okres": row["ZZ_okres_nazev"] or None,
        "kodOkresu": row["ZZ_okres_kod"] or None,
        "kraj": row["ZZ_kraj_nazev"] or None,
        "kodKraje": row["ZZ_kraj_kod"] or None,
    }


def validuj_zdroj_rpss() -> None:
    """CLAUDE.md 5.2 bod 1 - validace zdroje proti rpss.schema.json pri kazdem behu, driv nez
    se ze zdroje cokoli zpracuje. Pad zde znamena, ze MPSV zmenili format a je potreba se na
    to podivat rucne, ne pokracovat s daty, kterym uz nerozumime spravne."""
    with open(CACHE / "rpss.schema.json", encoding="utf-8") as f:
        schema = json.load(f)
    with open(CACHE / "rpss.json", encoding="utf-8") as f:
        data = json.load(f)
    jsonschema.validate(data, schema)


def referencni_pocet_bez_souradnic(stary_meta: dict | None) -> int | None:
    """Referencni hodnota pro prah na mista bez souradnic (PRAH_BEZ_SOURADNIC).

    Prednostne se cte `pocetMistBezSouradnic` z publikovaneho meta.json. To pole ale vzniklo
    az 9. 9. 2026 a meta.json se prepisuje jen pri zmene katalogu (CLAUDE.md 5.3), takze
    v publikovanych datech chybi tak dlouho, dokud nepribude prvni zmena obsahu - a prave
    v tom okne by pojistka mlcela. Referenci proto v takovem pripade spocitame primo
    z posledniho publikovaneho data/katalog.json, ktery je zdrojem te hodnoty tak jako tak.

    Vraci None jen pri uplne prvnim behu, kdy zadny publikovany katalog neexistuje a neni
    proti cemu porovnavat.
    """
    if stary_meta is not None and stary_meta.get("pocetMistBezSouradnic") is not None:
        return stary_meta["pocetMistBezSouradnic"]

    stary_katalog = DATA / "katalog.json"
    if not stary_katalog.exists():
        return None
    mista = json.loads(stary_katalog.read_text(encoding="utf-8"))["mista"]
    pocet = sum(1 for m in mista if m["souradnice"]["lat"] is None)
    print(f"  reference pro prah bez souradnic dopoctena z data/katalog.json: {pocet}")
    return pocet


def zkontroluj_stari_zdroju() -> None:
    """Pojistka proti tise zastaralym zdrojum.

    Denni beh drzi UZIS a RUIAN v cache GitHub Actions a stahuje je, az kdyz sonda ohlasi novou
    verzi. Kdyz sonda trvale selhava (vypadek CUZK, zmena formatu feedu), spadne beh do vetve
    "pokracuji nad posledni ulozenou verzi", cteni cache pokazde obnovi jeji sedmidennu lhutu
    a build zustava zeleny nad libovolne starymi daty. Prahova kontrola to nezachyti, protoze
    ta hlida zmenu poctu mist, a ta zadna neni - data se prece nemeni.

    Cte se datum z _cache/*_meta.json, tedy ze snapshotu, nad kterym se prave stavi, ne
    z publikovaneho data/meta.json - to zaostava zamerne (zapisuje se az za kontrolou hashe)
    a jeho stari o cerstvosti zdroje nevypovida.

    Prah 50 dni: MPSV vydava denne, UZIS a RUIAN mesicne, takze ve zdravem provozu je nejstarsi
    snapshot ~31 dni plus zpozdeni do nejblizsiho denniho behu. Zmereno 9. 9. 2026: mpsv 1 den,
    uzis 8 dni, ruian 9 dni. Rezerva do prahu je tedy zhruba 18 dni nad nejhorsim zdravym stavem.

    Zdroj z NAHRADNI_DATA je zavada bez ohledu na prah: dosazene dnesni datum je vzdy cerstve,
    takze by prah nikdy neprekrocilo a kontrola by mlcela prave v pripade, kdy o stari zdroje
    nic nevime.
    """
    dnes = datetime.date.today()
    zavady = []
    for zdroj, datum in sorted(DATUM_ZDROJOVYCH_DAT.items()):
        if zdroj in NAHRADNI_DATA:
            print(f"  {zdroj}: {datum} (dosazene dnesni datum, skutecne nezname)")
            zavady.append(f"{zdroj} - datum zdroje nezjisteno, dosazeno dnesni")
            continue
        stari = (dnes - datetime.date.fromisoformat(datum)).days
        print(f"  {zdroj}: {datum} ({stari} dni)")
        if stari > PRAH_STARI_ZDROJU:
            zavady.append(f"{zdroj} {datum} ({stari} dni)")

    if not zavady:
        return
    if "--zastarale-zdroje-ok" in sys.argv:
        print(
            f"UPOZORNENI: zdroje neprosly kontrolou stari ({', '.join(zavady)}), limit je "
            f"{PRAH_STARI_ZDROJU} dni. Pokracuji vedome pres --zastarale-zdroje-ok.",
            file=sys.stderr,
        )
        return
    print(
        f"POJISTKA: stari zdrojovych dat neni v poradku ({', '.join(zavady)}), limit je "
        f"{PRAH_STARI_ZDROJU} dni. NEPUBLIKUJI, zustava posledni platna verze. Overte, ze sonda "
        "na verze zdroju funguje a ze zdroj skutecne vydava nove verze; kdyz je prodleva na strane "
        "zdroje a je zamerne prijata, prepnete rucne pres --zastarale-zdroje-ok.",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    print("Kontroluji stari zdrojovych dat...")
    zkontroluj_stari_zdroju()

    print("Validuji zdrojova data MPSV proti rpss.schema.json...")
    validuj_zdroj_rpss()
    print("  OK")

    print("Nacitam MPSV...")
    items = load_rpss(CACHE / "rpss.json")
    senior = filter_senior_services(items)
    places = build_place_groups(senior, TODAY)
    print(f"  {len(senior)} senior sluzeb, {len(places)} mist")

    ciselniky = load_all(CACHE)
    kody = load_kody(CACHE)
    with open(CACHE / "typy-kapacity-socialni-sluzby.json", encoding="utf-8") as f:
        typ_kapacity_nazvy = {i["id"]: i["nazev"]["cs"] for i in json.load(f)["polozky"]}
    with open(CACHE / "druhy-socialni-sluzby.json", encoding="utf-8") as f:
        druhy_nazvy = {i["id"]: i["nazev"]["cs"] for i in json.load(f)["polozky"]}

    print("Nacitam UZIS...")
    rows = load_nrpzs(CACHE / "nrpzs.csv")
    relevant = filter_relevant(rows, UZIS_RELEVANT_DRUHY)
    zaznamy, priznaky = split_zaznamy_a_priznaky(relevant)
    print(f"  {len(rows)} radku, {len(relevant)} relevantnich, {len(zaznamy)} zaznamu, {len(priznaky)} priznaku")

    for p in places.values():
        p["poskytujeZdravotniPeci"] = False
        p["uzis_sluzby"] = []

    # CLAUDE.md 3.4 - "Zdravotni pece v ustavech socialni p." neni zarizeni, kam se da jit. Je to
    # zdravotnicka licence, kterou musi mit domov, aby smel zamestnavat sestry, a UZIS ji eviduje
    # zvlast na tez adrese. Nikdy z ni tedy nevznika misto ani polozka v sluzby[], jen priznak
    # u domova na tomtez adresnim bode; radek, ktery zadny takovy domov v katalogu nema, do vystupu
    # nejde vubec.
    #
    # Driv tyto radky pri neuspesnem parovani propadaly mezi bezne zaznamy, takze zakladaly
    # samostatna mista v zalozce Zdravi (338 mist, ctvrtina zalozky) - typicky druhy pin par desitek
    # metru od tehoz domova, ktery uz v katalogu byl z MPSV. Zaroven to bylo nekonzistentni: tataz
    # situace koncila bud jako priznak, nebo jako samostatne misto, podle toho, jestli se povedlo
    # sparovat ICO. Viz CLAUDE.md sekce 8.
    priznak_pripojeno = priznak_zahozeno = 0
    for row in priznaky:
        klic = ruian_klic(row)
        if klic in places:
            places[klic]["poskytujeZdravotniPeci"] = True
            priznak_pripojeno += 1
        else:
            priznak_zahozeno += 1

    uzis_standalone: list[dict] = list(zaznamy)

    print(
        f"  priznaky (zdravotni pece v ustavech): {priznak_pripojeno} pripojeno k domovu na tomtez "
        f"adresnim bode, {priznak_zahozeno} bez domova v katalogu "
        f"(nejdou do vystupu, CLAUDE.md 3.4)"
    )

    # Oprava feedbacku vyvojare (bod 6): zaklad. jednotka je fyzicka adresa, ne registrace (CLAUDE.md 4.2).
    # UZIS zaznam se pripoji k MPSV mistu prave tehdy, kdyz sdili kod adresniho mista - jeden adresni
    # bod je jedno misto a jeden pin, bez ohledu na to, kolik poskytovatelu za nim stoji. Shoda ICO se
    # zamerne nepouziva ani jako doplnkove kriterium: vic zarizeni na jedne adrese ma byt jedno misto
    # (ICO by je roztrhlo) a vic pobocek jedne organizace ma zustat oddelenych (ICO by je slepilo).
    # Zbytek, tedy radky bez MPSV mista na teze adrese, zaklada samostatna UZIS mista.
    uzis_groups: dict = {}
    for row in uzis_standalone:
        key = ruian_klic(row)
        if key is None:
            key = ("no_kod_uzis", row["ZZ_misto_poskytovani_ID"])
        uzis_groups.setdefault(key, []).append(row)

    uzis_only_groups: dict = {}
    adresa_matched = 0
    for key, rows_ in uzis_groups.items():
        if isinstance(key, int) and key in places:
            places[key]["uzis_sluzby"].extend(rows_)
            adresa_matched += len(rows_)
        else:
            uzis_only_groups[key] = rows_

    print(f"  {len(uzis_standalone)} UZIS zaznamu, z toho:")
    print(f"    {adresa_matched} pripojeno k existujicimu MPSV mistu podle sdileneho adresniho bodu (RUIAN kodu)")
    print(f"    {len(uzis_standalone) - adresa_matched} zustava jako samostatna UZIS mista ({len(uzis_only_groups)} mist)")

    # needed_kody zahrnuje i UZIS-only mista (klic = jejich RUIAN kod) - RUIAN CSV ma primo sloupec
    # "Kod obce", takze z nej dohledame kodObce i pro cistě UZIS mista, ktera vlastni kod obce v UZIS
    # CSV nemaji (jen textovy nazev). Souradnice UZIS-only mist ale zustavaji z jejich vlastniho ZZ_GPS.
    needed_kody = {k for k in places if isinstance(k, int)}
    needed_kody |= {k for k in uzis_only_groups if isinstance(k, int)}
    print(f"Nacitam RUIAN data pro {len(needed_kody)} adres...")
    ruian_body = load_address_points(CACHE / "ruian_adr.zip", needed_kody=needed_kody)
    print(f"  dohledano {len(ruian_body)}/{len(needed_kody)} adresnich bodu")

    mista_out = []

    for k, p in places.items():
        sluzby_out = [
            mpsv_sluzba_to_output(s, zarizeni_nazvy, typ_kapacity_nazvy, druhy_nazvy)
            for s, zarizeni_nazvy in slouc_zarizeni_jedne_sluzby(p["sluzby"])
        ]
        sluzby_out += [uzis_sluzba_to_output(r) for r in p["uzis_sluzby"]]

        kategorie = set()
        for s in p["sluzby"]:
            kategorie |= kategorie_pro_sluzbu(s["druhSocialniSluzby"], s["formy"])
        for r in p["uzis_sluzby"]:
            kategorie |= kategorie_pro_uzis(r["ZZ_druh_nazev"])

        if isinstance(k, int):
            misto_id = f"misto-{k}"
            coords = ruian_body.get(k)
        else:
            misto_id = bezadresy_id(k)
            coords = None

        mista_out.append(
            {
                "id": misto_id,
                "kodAdresnihoMista": k if isinstance(k, int) else None,
                "adresa": mpsv_addr_text(p["adresa"], ciselniky, kody),
                "souradnice": souradnice_out(coords),
                "kategorie": sorted(kategorie),
                "poskytujeZdravotniPeci": p["poskytujeZdravotniPeci"],
                "sluzby": sluzby_out,
            }
        )

    # UZIS-only mista: to, co po adresni shode s MPSV mistem (viz vyse) zbylo. Mezi sebou uz jsou
    # seskupena podle RUIAN kodu, pripadne podle ZZ_misto_poskytovani_ID, pokud kod chybi.
    for key, rows_ in uzis_only_groups.items():
        rows_sorted = sorted(rows_, key=lambda r: r["ZZ_misto_poskytovani_ID"])
        first = rows_sorted[0]
        if isinstance(key, int):
            # ID se odvozuje od adresniho bodu bez ohledu na zdroj, stejne jako u MPSV mist vyse.
            # Driv tato mista dostavala "misto-uzis-<ZZ_misto_poskytovani_ID>", i kdyz RUIAN kod
            # mela (985 z 986 ho ma). To ale porusuje CLAUDE.md 4.2 o stabilnich ID: slozeni zdroju
            # na jedne adrese se v case meni, a s nim se menilo i ID teze budovy. Realny priklad
            # z behu 4.9.2026 - na adresnim bode 19824068 (Tabor) skoncila posledni socialni
            # registrace, misto zustalo jen zdravotnicke a preklopilo se z "misto-19824068" na
            # "misto-uzis-225450". V zmeny.json to vypada jako zanik jednoho mista a vznik jineho,
            # takze druha strana zahodi zaznam a zalozi novy pro tutez budovu. Plati to i obracene:
            # jakmile na kterekoli z tech 985 adres pribude socialni sluzba, ID by se preklopilo zpet.
            misto_id = f"misto-{key}"
            kod_adm = key
        else:
            misto_id = f"misto-uzis-bezadresy-{first['ZZ_misto_poskytovani_ID']}"
            kod_adm = None

        coords = None
        for r in rows_sorted:
            coords = parse_gps(r.get("ZZ_GPS"))
            if coords:
                break

        adresa = uzis_addr_text(first)
        if kod_adm is not None:
            ruian_hit = ruian_body.get(kod_adm)
            if ruian_hit:
                adresa["kodObce"] = ruian_hit[2]

        mista_out.append(
            {
                "id": misto_id,
                "kodAdresnihoMista": kod_adm,
                "adresa": adresa,
                "souradnice": souradnice_out(coords),
                "kategorie": sorted(
                    {k for r in rows_sorted for k in kategorie_pro_uzis(r["ZZ_druh_nazev"])}
                ),
                "poskytujeZdravotniPeci": False,
                "sluzby": [uzis_sluzba_to_output(r) for r in rows_sorted],
            }
        )

    # CLAUDE.md 4.2 - nikdy nepublikovat prazdny vystup. Pad zde je vzdy chyba zpracovani,
    # ne legitimni stav (kdyby MPSV+UZIS vratily 0 mist, je to znamka rozbiteho zdroje,
    # ne ze by v CR nebyly zadne seniorske sluzby).
    if not mista_out:
        raise RuntimeError("Vystup je prazdny (0 mist) - NEPUBLIKUJI, jde o chybu zpracovani.")

    # CLAUDE.md 4.2 - stabilni identifikatory. Duplicitni ID znamena, ze druha strana neumi zaznamy
    # rozlisit a zmeny.json u nich ztraci smysl. Schema to neuhlida (mista[] nema uniqueItems a
    # schema uz je odsouhlasene, nemenime ho), takze kontrola musi byt tady. Neni to teoreticka
    # pojistka - do 4.9.2026 kolidovala 3 ID na 8 mistech.
    pocty = Counter(m["id"] for m in mista_out)
    duplicitni = sorted(mid for mid, n in pocty.items() if n > 1)
    if duplicitni:
        raise RuntimeError(
            f"Duplicitni ID mist ({len(duplicitni)}): {duplicitni[:10]} - NEPUBLIKUJI."
        )

    out = {"verzeSchematu": VERZE_SCHEMATU, "mista": mista_out}

    print("Validuji vystup proti schematu...")
    with open(ROOT / "schema" / "katalog.schema.json", encoding="utf-8") as f:
        schema = json.load(f)
    # format_checker je nutny explicitne: bez nej jsonschema klicove slovo "format" jen anotuje
    # a nekontroluje, takze by "format": "date" u datumPoskytovaniOd/Do neodhalilo nic.
    jsonschema.validate(out, schema, format_checker=jsonschema.Draft7Validator.FORMAT_CHECKER)
    print("  OK, 0 chyb")

    content = json.dumps(out, ensure_ascii=False, indent=2)
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    pocet_bez_souradnic = sum(1 for m in mista_out if m["souradnice"]["lat"] is None)
    print(f"Mist bez souradnic: {pocet_bez_souradnic} z {len(mista_out)}")

    stary_meta_path = DATA / "meta.json"
    stary_meta = None
    if stary_meta_path.exists():
        stary_meta = json.loads(stary_meta_path.read_text(encoding="utf-8"))

    # CLAUDE.md 5.2 bod 3 - prahova kontrola. Zmena o vic nez 5 % proti poslednimu dobremu
    # behu znamena nepublikovat a upozornit, ne tise prepsat mozna rozbita data.
    if stary_meta is not None and stary_meta.get("pocetMist"):
        stare_pocet = stary_meta["pocetMist"]
        delta = abs(len(mista_out) - stare_pocet) / stare_pocet
        if delta > PRAH_ZMENY:
            # Prah hlida rozbity zdroj, ne zamernou zmenu zpracovani. Kdyz zmenime pravidla na nasi
            # strane (napr. odstraneni zdravotnickych licenci domovu podle 3.4), prah zabere taky,
            # a bez teto vyjimky by takovou zmenu neslo publikovat vubec. Prepnout jde jen rucne -
            # workflow prepinac nikdy nepredava, takze v automatice pojistka plati bez vyjimky.
            if "--zamerna-velka-zmena" not in sys.argv:
                print(
                    f"POJISTKA: pocet mist se zmenil o {delta:.1%} ({stare_pocet} -> {len(mista_out)}), "
                    f"limit je {PRAH_ZMENY:.0%}. NEPUBLIKUJI, zustava posledni platna verze.",
                    file=sys.stderr,
                )
                sys.exit(1)
            print(
                f"UPOZORNENI: pocet mist se zmenil o {delta:.1%} ({stare_pocet} -> {len(mista_out)}), "
                f"prah {PRAH_ZMENY:.0%} prekrocen vedome pres --zamerna-velka-zmena.",
                file=sys.stderr,
            )

    # Pojistka na tise zahozene souradnice. Prahova kontrola vyse hlida POCET mist, ne jejich
    # vyplnenost, takze by nezabrala na scenari, ktery je u tohoto zdroje realny: kdyby UZIS
    # opravil poradi lat/lng (CLAUDE.md 3.1), padly by vsechny jeho souradnice mimo bounding box
    # CR, parse_gps by vratil None a ~650 UZIS mist by naraz prislo o pin, aniz by ubylo jedine
    # misto. Zmereno pres celou historii data/katalog.json (10 verzi, 4. az 9. 9. 2026): mist bez
    # souradnic je 110 az 112, tedy rozptyl 2, a nepohnula s nim ani vymena mesicniho snapshotu
    # RUIAN 31. 7. -> 31. 8. Prah 30 je proti tomu patnactinasobna rezerva a proti popsanemu
    # scenari porad o rad nizsi, nez by byl jeho dopad.
    stare_bez = referencni_pocet_bez_souradnic(stary_meta)
    if stare_bez is not None:
        narust = pocet_bez_souradnic - stare_bez
        if narust > PRAH_BEZ_SOURADNIC:
            if "--zamerna-velka-zmena" not in sys.argv:
                print(
                    f"POJISTKA: mist bez souradnic pribylo o {narust} ({stare_bez} -> "
                    f"{pocet_bez_souradnic}), limit je {PRAH_BEZ_SOURADNIC}. NEPUBLIKUJI, "
                    "zustava posledni platna verze.",
                    file=sys.stderr,
                )
                sys.exit(1)
            print(
                f"UPOZORNENI: mist bez souradnic pribylo o {narust} ({stare_bez} -> "
                f"{pocet_bez_souradnic}), prah {PRAH_BEZ_SOURADNIC} prekrocen vedome "
                "pres --zamerna-velka-zmena.",
                file=sys.stderr,
            )

    # CLAUDE.md 5.3 - porovnavat obsahem (hashem), ne datem, a soubor se nema ani prepsat,
    # kdyz je shodny. Proto se hash pocita a porovnava PRED zapisem, ne az git diffem po nem.
    if stary_meta is not None and stary_meta.get("hashKatalogu") == content_hash:
        print("Data se nezmenila (shodny hash), nic se nezapisuje.")
        return

    # Skutecny diff pro zmeny.json - porovnani se starym data/katalog.json podle ID mista.
    # Pokud stary soubor neexistuje, jde o prvni produkcni beh a vse je "pridano" (CLAUDE.md 8).
    stary_katalog_path = DATA / "katalog.json"
    if stary_katalog_path.exists():
        stara_mista = {m["id"]: m for m in json.loads(stary_katalog_path.read_text(encoding="utf-8"))["mista"]}
        nova_mista = {m["id"]: m for m in mista_out}
        pridano = sorted(set(nova_mista) - set(stara_mista))
        odebrano = sorted(set(stara_mista) - set(nova_mista))
        zmeneno = sorted(
            mid for mid in (set(stara_mista) & set(nova_mista)) if stara_mista[mid] != nova_mista[mid]
        )
    else:
        pridano = [m["id"] for m in mista_out]
        zmeneno = []
        odebrano = []

    (DATA / "katalog.json").write_text(content, encoding="utf-8")
    print(f"Zapsano {len(mista_out)} mist do data/katalog.json")

    pocet_podle_kategorie = {
        kat: sum(1 for m in mista_out if kat in m["kategorie"]) for kat in ["domovy", "terenni", "bezpeci", "zdravi"]
    }
    meta = {
        "verzeSchematu": VERZE_SCHEMATU,
        "hashKatalogu": content_hash,
        "pocetMist": len(mista_out),
        "pocetSluzeb": sum(len(m["sluzby"]) for m in mista_out),
        "pocetMistPodleKategorie": pocet_podle_kategorie,
        "pocetMistBezKategorie": sum(1 for m in mista_out if not m["kategorie"]),
        "pocetMistSPoskytovanimZdravotniPece": sum(1 for m in mista_out if m["poskytujeZdravotniPeci"]),
        "pocetMistBezSouradnic": pocet_bez_souradnic,
        "datumZdrojovychDat": DATUM_ZDROJOVYCH_DAT,
    }
    with open(DATA / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("Zapsano data/meta.json")

    zmeny = {
        "verzeSchematu": VERZE_SCHEMATU,
        "pridano": pridano,
        "zmeneno": zmeneno,
        "odebrano": odebrano,
    }
    with open(DATA / "zmeny.json", "w", encoding="utf-8") as f:
        json.dump(zmeny, f, ensure_ascii=False, indent=2)
    print(f"Zapsano data/zmeny.json (pridano {len(pridano)}, zmeneno {len(zmeneno)}, odebrano {len(odebrano)})")


if __name__ == "__main__":
    main()
