"""Etapa 4: orchestrace stahovani vsech zdroju do _cache/ pro automatizovane behy.

Rozdeleno podle CLAUDE.md 5.1 na dva rezimy, protoze MPSV se aktualizuje denne
a UZIS+RUIAN jen mesicne:

    python stahni_zdroje.py --mpsv        # rpss.json, rpss.schema.json, ciselniky
    python stahni_zdroje.py --uzis-ruian  # nrpzs.csv, RUIAN ZIP (pres ATOM feed)
    python stahni_zdroje.py --all         # obojí (lokalni test)

Kazdy rezim si vedle stazenych dat zapisuje vlastni meta soubor s datem zdrojovych
dat (_cache/mpsv_meta.json, _cache/uzis_ruian_meta.json), ktery pak cte build_katalog.py
misto drivejsi natvrdo zapsane konstanty.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fetch import download, last_modified  # noqa: E402
from ciselniky import BASE_URL as CISELNIKY_BASE_URL, FILES as CISELNIK_FILES  # noqa: E402
from ruian import ATOM_FEED_URL, resolve_download_url  # noqa: E402

import requests  # noqa: E402

ROOT = Path(__file__).parent.parent
CACHE = ROOT / "_cache"

RPSS_URL = "https://data.mpsv.cz/od/soubory/rpss/rpss.json"
RPSS_SCHEMA_URL = "https://data.mpsv.cz/od/soubory/rpss/rpss.schema.json"
NRPZS_URL = (
    "https://datanzis.uzis.gov.cz/data/NR-01-NRPZS/NR-01-06/"
    "Otevrena-data-NR-01-06-nrpzs-mista-poskytovani-zdravotnich-sluzeb.csv"
)

RUIAN_DATE_RE = re.compile(r"(\d{8})_OB_ADR_csv\.zip")


def fetch_mpsv() -> None:
    print("Stahuji rpss.json...")
    download(RPSS_URL, CACHE / "rpss.json")
    download(RPSS_SCHEMA_URL, CACHE / "rpss.schema.json")

    print("Stahuji ciselniky...")
    for filename in CISELNIK_FILES:
        download(CISELNIKY_BASE_URL.format(name=filename), CACHE / f"{filename}.json")

    datum = last_modified(RPSS_URL)
    if datum is None:
        datum = date.today().isoformat()
        print(f"  VAROVANI: Last-Modified pro rpss.json nezjisteno, pouzivam dnesni datum {datum}", file=sys.stderr)
    with open(CACHE / "mpsv_meta.json", "w", encoding="utf-8") as f:
        json.dump({"mpsv": datum}, f)
    print(f"  datum zdrojovych dat MPSV: {datum}")


def fetch_uzis_ruian() -> None:
    print("Stahuji nrpzs.csv...")
    download(NRPZS_URL, CACHE / "nrpzs.csv")
    uzis_datum = last_modified(NRPZS_URL)
    if uzis_datum is None:
        uzis_datum = date.today().isoformat()
        print(f"  VAROVANI: Last-Modified pro nrpzs.csv nezjisteno, pouzivam dnesni datum {uzis_datum}", file=sys.stderr)

    print("Zjistuji aktualni odkaz na RUIAN ZIP z ATOM feedu...")
    atom_resp = requests.get(ATOM_FEED_URL, timeout=60)
    atom_resp.raise_for_status()
    zip_url = resolve_download_url(atom_resp.content)
    print(f"  odkaz: {zip_url}")
    download(zip_url, CACHE / "ruian_adr.zip")

    match = RUIAN_DATE_RE.search(zip_url)
    if match:
        raw = match.group(1)
        ruian_datum = f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    else:
        ruian_datum = date.today().isoformat()
        print(f"  VAROVANI: datum nejde vytahnout z nazvu souboru RUIAN, pouzivam dnesni datum {ruian_datum}", file=sys.stderr)

    with open(CACHE / "uzis_ruian_meta.json", "w", encoding="utf-8") as f:
        json.dump({"uzis": uzis_datum, "ruian": ruian_datum}, f)
    print(f"  datum zdrojovych dat UZIS: {uzis_datum}, RUIAN: {ruian_datum}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mpsv", action="store_true", help="stahnout rpss.json + ciselniky")
    parser.add_argument("--uzis-ruian", action="store_true", help="stahnout nrpzs.csv + RUIAN ZIP")
    parser.add_argument("--all", action="store_true", help="stahnout obojí (lokalni test)")
    args = parser.parse_args()

    if not (args.mpsv or args.uzis_ruian or args.all):
        parser.error("zadej alespon jeden z prepinacu --mpsv / --uzis-ruian / --all")

    if args.mpsv or args.all:
        fetch_mpsv()
    if args.uzis_ruian or args.all:
        fetch_uzis_ruian()


if __name__ == "__main__":
    main()
