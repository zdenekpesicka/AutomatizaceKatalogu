"""Testy nad cistymi funkcemi zpracovani.

Zamerne pokryvaji prave ta mista, kde uz jednou vznikla chyba v datech nebo kde ji zdroje
aktivne zvou - datove pasti z CLAUDE.md sekce 3 a rozhodnuti ze sekce 8.3. Nejsou to testy
"pro pokryti"; kazdy odpovida konkretni vlastnosti zdroje, kterou nelze odvodit z kodu.

Nesahaji na sit, takze bezi i pred stazenim zdroju. Na _cache sahaji jen nepricmo: import
`build_katalog` spusti `nacti_datum_zdrojovych_dat()`, ktera meta soubory precte, kdyz existuji.
Kdyz chybi, jen varuje na stderr a dosadi dnesni datum, takze testum to nevadi - v CI bezi
prave nad neexistujicim _cache.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "import"))

import fetch  # noqa: E402
from ruian import resolve_download_url  # noqa: E402
from stahni_zdroje import ruian_datum_z_url  # noqa: E402
from uzis import parse_gps, split_obor_pece  # noqa: E402


# --- CLAUDE.md 3.1: UZIS ma ve WKT prohozene poradi, prvni je sirka ---

def test_parse_gps_cte_prvni_cislo_jako_sirku():
    # Ceske Budejovice. Pri standardnim cteni (prvni = delka) by bod padl do Somalska.
    assert parse_gps("POINT(48.959066276499 14.470410383763)") == (48.959066276499, 14.470410383763)


def test_parse_gps_odmitne_bod_mimo_cr():
    # Tentyz bod prohozene - presne to, co by vzniklo, kdyby UZIS poradi "opravil".
    # Musi vratit None, ne souradnici mimo CR.
    assert parse_gps("POINT(14.470410383763 48.959066276499)") is None


@pytest.mark.parametrize("hodnota", [None, "", "48.9 14.4", "POINT(nesmysl)", "POINT(48.9)"])
def test_parse_gps_odmitne_vadny_vstup(hodnota):
    assert parse_gps(hodnota) is None


# --- CLAUDE.md 3.3: ZZ_obor_pece je vicehodnotove, pred filtrovanim se musi rozpadnout ---

def test_split_obor_pece_rozpada_a_orezava():
    assert split_obor_pece("vseobecne prakticke lekarstvi, paliativni medicina") == [
        "vseobecne prakticke lekarstvi",
        "paliativni medicina",
    ]


@pytest.mark.parametrize("hodnota", [None, "", "   "])
def test_split_obor_pece_prazdna_hodnota(hodnota):
    assert split_obor_pece(hodnota) == []


# --- CLAUDE.md 8.3: jedna registrace je v sluzby[] prave jednou ---

def _sluzba(portal_id: int, nazev: str) -> dict:
    return {"portalId": portal_id, "nazevZarizeni": nazev, "kapacita": 95}


def test_slouceni_podle_portal_id_nikoli_podle_nazvu():
    from build_katalog import slouc_zarizeni_jedne_sluzby

    vysledek = slouc_zarizeni_jedne_sluzby([
        _sluzba(7228, "2. nadzemni podlazi"),
        _sluzba(7228, "3. nadzemni podlazi"),
        _sluzba(9999, "Jina registrace"),
    ])
    # Domov Chrudim: bez slouceni se kapacita 95 zapocitala dvakrat.
    assert len(vysledek) == 2
    assert vysledek[0][1] == ["2. nadzemni podlazi", "3. nadzemni podlazi"]
    assert vysledek[1][1] == ["Jina registrace"]


def test_slouceni_ignoruje_koncovou_mezeru_ale_zachova_puvodni_tvar():
    from build_katalog import slouc_zarizeni_jedne_sluzby

    # mpsv-311: tentyz nazev se lisi jen koncovou mezerou, coz je preklep v registru.
    vysledek = slouc_zarizeni_jedne_sluzby([
        _sluzba(311, "Domov pro seniory Bukov "),
        _sluzba(311, "Domov pro seniory Bukov"),
    ])
    assert len(vysledek) == 1
    # Nazev jde do vystupu v puvodnim tvaru, orez slouzi jen k rozhodnuti o duplicite.
    assert vysledek[0][1] == ["Domov pro seniory Bukov "]


# --- CLAUDE.md 8.3: klic cache se odvozuje od nazvu souboru CUZK ---

def test_ruian_datum_z_url():
    assert ruian_datum_z_url(
        "https://vdp.cuzk.gov.cz/vymenny_format/csv/20260831_OB_ADR_csv.zip"
    ) == "2026-08-31"


def test_ruian_datum_z_url_neznamy_tvar():
    assert ruian_datum_z_url("https://vdp.cuzk.gov.cz/vymenny_format/csv/neco.zip") is None


# --- ATOM feed CUZK: odkaz se pouziva ke stazeni, takze se kontroluje host i tvar ---

def _feed(id_text: str) -> bytes:
    return (
        '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
        f"<entry><id>{id_text}</id></entry></feed>"
    ).encode("utf-8")


def test_resolve_download_url_platny_feed():
    url = "https://vdp.cuzk.gov.cz/vymenny_format/csv/20260831_OB_ADR_csv.zip"
    assert resolve_download_url(_feed(url)) == url


@pytest.mark.parametrize(
    "xml",
    [
        b'<feed xmlns="http://www.w3.org/2005/Atom"></feed>',
        b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>x</title></entry></feed>',
    ],
)
def test_resolve_download_url_rozbity_feed(xml):
    with pytest.raises(ValueError):
        resolve_download_url(xml)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.invalid/vymenny_format/csv/20260831_OB_ADR_csv.zip",  # cizi host
        "http://vdp.cuzk.gov.cz/x/20260831_OB_ADR_csv.zip",  # bez TLS
        "https://vdp.cuzk.gov.cz/vymenny_format/csv/neco_jineho.zip",  # jiny nazev souboru
    ],
)
def test_resolve_download_url_neocekavany_odkaz(url):
    with pytest.raises(ValueError):
        resolve_download_url(_feed(url))


# --- Odstup mezi pokusy. Bez nej probehne vsech pet pokusu behem milisekund, tedy driv, nez
# --- stihne odeznit i ten nejkratsi vypadek zdroje, a retry jen zopakuje tutez chybu.
# --- Sit se nepouziva, requests.get i time.sleep jsou nahrazene.

class _FakeResponse:
    content = b"data"

    def raise_for_status(self):
        pass


def test_get_bytes_ceka_mezi_pokusy(monkeypatch):
    pokusy = []
    cekani = []

    def fake_get(url, timeout):
        pokusy.append(url)
        if len(pokusy) < 3:
            raise fetch.requests.RequestException("simulovany vypadek")
        return _FakeResponse()

    monkeypatch.setattr(fetch.requests, "get", fake_get)
    monkeypatch.setattr(fetch.time, "sleep", cekani.append)

    assert fetch.get_bytes("https://example.invalid/feed") == b"data"
    assert len(pokusy) == 3
    assert cekani == [2, 4]


# --- last_modified: jedine selhani HEAD zapisovalo do meta souboru nahradni datum, ktere se
# --- pak ulozilo do cache pod platny klic sondy a kazdy dalsi denni beh na nem spadl znovu.

class _FakeHead:
    headers = {"Last-Modified": "Mon, 01 Sep 2026 03:00:00 GMT"}

    def raise_for_status(self):
        pass


def test_last_modified_ceka_mezi_pokusy(monkeypatch):
    pokusy = []
    cekani = []

    def fake_head(url, timeout, allow_redirects):
        pokusy.append(url)
        if len(pokusy) < 3:
            raise fetch.requests.RequestException("simulovany vypadek")
        return _FakeHead()

    monkeypatch.setattr(fetch.requests, "head", fake_head)
    monkeypatch.setattr(fetch.time, "sleep", cekani.append)

    assert fetch.last_modified("https://example.invalid/csv") == "2026-09-01"
    assert len(pokusy) == 3
    assert cekani == [2, 4]


def test_last_modified_vrati_none_az_po_vycerpani_pokusu(monkeypatch):
    pokusy = []
    cekani = []

    def fake_head(url, timeout, allow_redirects):
        pokusy.append(url)
        raise fetch.requests.RequestException("simulovany vypadek")

    monkeypatch.setattr(fetch.requests, "head", fake_head)
    monkeypatch.setattr(fetch.time, "sleep", cekani.append)

    # Na rozdil od get_bytes se nevyhazuje - datum zdroje neni blokujici udaj, volajici
    # si dosadi dnesni a zapise zdroj do nahradniDatum. Musi to ale byt az posledni moznost.
    assert fetch.last_modified("https://example.invalid/csv") is None
    assert len(pokusy) == 5
    assert cekani == [2, 4, 8, 16]


def test_get_bytes_selze_po_vycerpani_pokusu(monkeypatch):
    cekani = []

    def fake_get(url, timeout):
        raise fetch.requests.RequestException("simulovany vypadek")

    monkeypatch.setattr(fetch.requests, "get", fake_get)
    monkeypatch.setattr(fetch.time, "sleep", cekani.append)

    with pytest.raises(fetch.requests.RequestException):
        fetch.get_bytes("https://example.invalid/feed")
    # Strop 16 s drzi celkove cekani na nejvyse 30 s, tedy hluboko pod limitem jobu.
    assert cekani == [2, 4, 8, 16]
    assert sum(cekani) <= 30
