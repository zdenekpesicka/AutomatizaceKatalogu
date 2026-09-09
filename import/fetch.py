"""Stahovani zdrojovych souboru s podporou obnoveni preruseneho prenosu a komprese."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1 MB
TIMEOUT = 60

# Odstup mezi pokusy: 2, 4, 8, 16 s. Bez nej probehne vsech pet pokusu behem milisekund,
# tedy driv, nez staci odeznit i ten nejkratsi vypadek zdroje - retry pak jen zopakuje
# tutez chybu a beh spadne. Strop drzi celkove cekani na nejvyse 30 s na soubor (2+4+8+16),
# tedy hluboko pod limitem jobu (15 minut u denniho behu, 30 u rucniho).
BACKOFF_ZAKLAD = 2
BACKOFF_STROP = 16


def download(url: str, dest: Path, *, max_retries: int = 5) -> Path:
    """Stahne soubor do `dest`. Pri preruseni prenosu pokracuje pomoci Range hlavicky.

    Pozaduje kompresi pres Accept-Encoding (requests to posila automaticky);
    server rpss.json ji v praxi nenabizi, ale jine zdroje ano.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")

    attempt = 0
    while attempt < max_retries:
        attempt += 1
        existing = tmp.stat().st_size if tmp.exists() else 0
        headers = {"Range": f"bytes={existing}-"} if existing else {}
        try:
            with requests.get(url, headers=headers, stream=True, timeout=TIMEOUT) as resp:
                if existing and resp.status_code == 200:
                    # server nepodporuje Range, zacit znovu od nuly
                    tmp.unlink(missing_ok=True)
                    existing = 0
                resp.raise_for_status()

                mode = "ab" if existing else "wb"
                with open(tmp, mode) as f:
                    for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)

            tmp.replace(dest)
            logger.info("Stazeno %s (%d bajtu)", dest, dest.stat().st_size)
            return dest
        except requests.RequestException as exc:
            logger.warning("Pokus %d/%d selhal pro %s: %s", attempt, max_retries, url, exc)
            if attempt >= max_retries:
                raise
            odstup = min(BACKOFF_ZAKLAD ** attempt, BACKOFF_STROP)
            logger.info("Cekam %d s pred dalsim pokusem", odstup)
            time.sleep(odstup)
    raise RuntimeError(f"Stazeni {url} selhalo po {max_retries} pokusech")


def get_bytes(url: str, *, max_retries: int = 5) -> bytes:
    """Stahne maly soubor do pameti, se stejnym odstupem mezi pokusy jako `download`.

    Pro ATOM feed CUZK: je to par kB, takze streamovani ani Range nema smysl, ale odolnost
    proti kratkemu vypadku ano. Bez retry shodil jediny neuspesny pozadavek cele stazeni
    UZIS a RUIAN, pripadne poslal denni beh zbytecne na nahradni klic cache - a ten stoji
    92 MB stazeni navic.
    """
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as exc:
            logger.warning("Pokus %d/%d selhal pro %s: %s", attempt, max_retries, url, exc)
            if attempt >= max_retries:
                raise
            odstup = min(BACKOFF_ZAKLAD ** attempt, BACKOFF_STROP)
            logger.info("Cekam %d s pred dalsim pokusem", odstup)
            time.sleep(odstup)
    raise RuntimeError(f"Stazeni {url} selhalo po {max_retries} pokusech")


def last_modified(url: str, *, max_retries: int = 5) -> Optional[str]:
    """Zjisti datum posledni zmeny zdroje pres HEAD pozadavek (hlavicka Last-Modified).

    Vraci ISO datum (YYYY-MM-DD), nebo None, pokud server hlavicku neposila nebo HEAD selze -
    CLAUDE.md 5.3 pozaduje datum zdrojovych dat v meta.json, ale neni to blokujici udaj,
    volajici si v takovem pripade poradi sam (typicky fallback na dnesni datum + varovani).

    Opakuje se stejnym odstupem jako `download` a `get_bytes`. Bez toho stacil jediny neuspesny
    HEAD k tomu, aby se do `_cache/uzis_ruian_meta.json` zapsalo nahradni datum - a to je drazsi
    porucha, nez vypada: beh na nem spadne v kontrole stari zdroju, ale meta soubor se mezitim
    ulozi do cache pod platny klic sondy, takze ho tam kazdy dalsi denni beh najde znovu.
    """
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        try:
            resp = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("HEAD pokus %d/%d selhal pro %s: %s", attempt, max_retries, url, exc)
            if attempt >= max_retries:
                return None
            odstup = min(BACKOFF_ZAKLAD ** attempt, BACKOFF_STROP)
            logger.info("Cekam %d s pred dalsim pokusem", odstup)
            time.sleep(odstup)
            continue

        raw = resp.headers.get("Last-Modified")
        if not raw:
            return None
        try:
            dt = datetime.strptime(raw, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
        except ValueError:
            logger.warning("Last-Modified hlavicka v neocekavanem formatu: %r", raw)
            return None
        return dt.date().isoformat()
    return None
