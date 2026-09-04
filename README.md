# Katalog registrovaných služeb pro seniory

Repozitář sjednocuje data o sociálních a zdravotních službách pro seniory z veřejných registrů (MPSV, ÚZIS, RÚIAN) do jednoho datového výstupu a udržuje ho automaticky aktuální. Vede jen data, s repozitářem webu nemá nic společného.

## Odběr dat

| Soubor | Obsah |
|---|---|
| [`data/katalog.json`](https://raw.githubusercontent.com/zdenekpesicka/AutomatizaceKatalogu/main/data/katalog.json) | kompletní data |
| [`data/meta.json`](https://raw.githubusercontent.com/zdenekpesicka/AutomatizaceKatalogu/main/data/meta.json) | verze schématu, hash obsahu, počty záznamů, datum zdrojových dat |
| [`data/zmeny.json`](https://raw.githubusercontent.com/zdenekpesicka/AutomatizaceKatalogu/main/data/zmeny.json) | ID přidaných, změněných a odebraných míst od posledního běhu se změnou |
| [`schema/katalog.schema.json`](https://raw.githubusercontent.com/zdenekpesicka/AutomatizaceKatalogu/main/schema/katalog.schema.json) | JSON Schema (draft-07) pro validaci na straně příjemce |

Soubory jsou statické, staví se přímo z větve `main`, žádné API se neprovozuje. `data/ukazka.json` je zmrazená ilustrace k dokumentaci, neodebírá se.

**Popis polí, sémantika ID, kategorie, souřadnice a práce se `zmeny.json`: [`data/dokumentace-rozhrani.md`](data/dokumentace-rozhrani.md).**

## Aktualizace

| Běh | Zdroje | Plán (UTC) | Workflow |
|---|---|---|---|
| denní | MPSV | `0 4 * * *` | `.github/workflows/import.yml` |
| měsíční | ÚZIS + RÚIAN + MPSV | `0 5 3 * *` | `.github/workflows/import-mesicni.yml` |

Naplánované běhy GitHub Actions nemají garantovaný čas, zpoždění 5 až 30 minut je běžné. Oba workflow jdou spustit i ručně přes **Actions → vybrat workflow → Run workflow** (`workflow_dispatch`).

**Commit vzniká jen tehdy, když se data skutečně změnila.** Běh, který doběhne bez commitu, je úspěšný běh beze změny ve zdrojích, ne chyba. Že import proběhl, je vidět v historii běhů; `meta.json` proto záměrně neobsahuje čas běhu, jen údaje odvozené od dat. Změnu obsahu poznáte podle `hashKatalogu` v `meta.json`.

## Když běh selže

Do `data/` se nic nezapíše a zůstane poslední platná verze. Publikace se zastaví, pokud:

- zdrojová data neprojdou validací proti schématu registru,
- vlastní výstup neprojde validací proti `schema/katalog.schema.json`,
- se počet míst změní o víc než 5 % proti poslední publikované verzi,
- ve výstupu vznikne duplicitní `misto.id`.

Prahová kontrola hlídá rozbitý zdroj. Když je velká změna záměrná (úprava zpracování na naší straně), překlene se ručním přepínačem `--zamerna-velka-zmena` při lokálním běhu. Workflow ho nikdy nepředává, v automatice tedy platí bez výjimky.

Notifikace o selhání naplánovaného běhu chodí jen tomu, kdo workflow naposledy zapnul, a jen když má v **Settings → Notifications → System → Actions** přepnuto na Email (výchozí stav je „Don't notify"). Kdo workflow vypne a znovu zapne, stane se příjemcem.

## Lokální běh

```
pip install -r import/requirements.txt      # Python 3.11
python import/stahni_zdroje.py --all        # nebo --mpsv / --uzis-ruian
python import/build_katalog.py
```

Stažené zdroje se ukládají do `_cache/`. `build_katalog.py` zapisuje do `data/` jen při skutečné změně obsahu, stejně jako v automatice.

## Struktura

```
import/             stahování zdrojů a sestavení katalogu
config/             mapování druhů služeb na kategorie webu
data/               katalog.json, meta.json, zmeny.json, dokumentace, ukázka
schema/             katalog.schema.json
.github/workflows/  denní a měsíční import
```

`CLAUDE.md` je zadání a technický záznam k realizaci: ověřená fakta o zdrojích, datové pasti, pravidla rozhraní a odchylky od původního zadání.

## Zdroje a licence

Podmínky užití podle Národního katalogu otevřených dat, ověřeno 4. 9. 2026.

| Zdroj | Data | Podmínky užití |
|---|---|---|
| MPSV | [Registr poskytovatelů sociálních služeb](https://data.mpsv.cz/od/soubory/rpss/rpss.json) | Neobsahuje autorská díla, databáze není chráněna. **Bez povinné citace.** |
| ÚZIS ČR | [NRPZS: Místa poskytování zdravotních služeb](https://datanzis.uzis.gov.cz/data/NR-01-NRPZS/NR-01-06/Otevrena-data-NR-01-06-nrpzs-mista-poskytovani-zdravotnich-sluzeb.csv) | Autorské dílo pod **CC BY 4.0**, databáze nechráněná. **Povinné uvedení zdroje.** |
| ČÚZK | [RÚIAN, adresní místa (CSV pro stát)](https://atom.cuzk.gov.cz/get.ashx?theme=RUIAN-CSV-ADR-ST) | **CC BY 4.0** na všech třech úrovních. **Povinné uvedení zdroje.** |

### Citace na webu, který data zobrazuje

Licence CC BY 4.0 u ÚZIS a ČÚZK vyžaduje uvedení autora, názvu, zdroje a licence. Obě citace musí být na webu; níže je znění sestavené z údajů evidovaných v NKOD:

> **Zdravotní služby:** NRPZS: Místa poskytování zdravotních služeb. Zelinková H., Klimeš D., Šnábl I., Májek T., Jarkovský J., Klika P., Vičar M., Jochcová M., Komenda M., Dušek L. Praha: ÚZIS ČR. Dostupné z <https://nrpzs.uzis.cz>. Licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
>
> **Adresní body:** Data RÚIAN o adresách poskytovaná pro stát ve formátu CSV. Český úřad zeměměřický a katastrální. Dostupné z <https://vdp.cuzk.gov.cz>. Licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Poznámka k rozporu ve zdrojích: CSVW metadata publikovaná vedle CSV souboru ÚZIS (`…csv-metadata.json`) uvádějí jako licenci „volný přístup", zatímco záznam téže distribuce v NKOD uvádí u autorského díla CC BY 4.0 se jmenným seznamem autorů. Uvádí se přísnější varianta, tedy citace podle NKOD.
