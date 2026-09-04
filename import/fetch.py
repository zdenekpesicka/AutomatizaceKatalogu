"""Stahovani zdrojovych souboru s podporou obnoveni preruseneho prenosu a komprese."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1 MB
TIMEOUT = 60


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
    raise RuntimeError(f"Stazeni {url} selhalo po {max_retries} pokusech")


def last_modified(url: str) -> Optional[str]:
    """Zjisti datum posledni zmeny zdroje pres HEAD pozadavek (hlavicka Last-Modified).

    Vraci ISO datum (YYYY-MM-DD), nebo None, pokud server hlavicku neposila nebo HEAD selze -
    CLAUDE.md 5.3 pozaduje datum zdrojovych dat v meta.json, ale neni to blokujici udaj,
    volajici si v takovem pripade poradi sam (typicky fallback na dnesni datum + varovani).
    """
    try:
        resp = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("HEAD pozadavek na %s selhal: %s", url, exc)
        return None

    raw = resp.headers.get("Last-Modified")
    if not raw:
        return None
    try:
        dt = datetime.strptime(raw, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
    except ValueError:
        logger.warning("Last-Modified hlavicka v neocekavanem formatu: %r", raw)
        return None
    return dt.date().isoformat()
