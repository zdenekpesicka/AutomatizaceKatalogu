# Katalog registrovaných služeb pro seniory

Repozitář sjednocuje data o sociálních a zdravotních službách pro seniory z veřejných registrů (MPSV, ÚZIS, RÚIAN) do jednoho datového výstupu a udržuje ho automaticky aktuální. Vede jen data, s repozitářem webu nemá nic společného.

## Odběr dat

| Soubor | Obsah |
|---|---|
| [`data/katalog.json`](https://raw.githubusercontent.com/zdenekpesicka/AutomatizaceKatalogu/main/data/katalog.json) | kompletní data |
| [`data/meta.json`](https://raw.githubusercontent.com/zdenekpesicka/AutomatizaceKatalogu/main/data/meta.json) | verze schématu, hash obsahu, počty záznamů, datum zdrojových dat |
| [`data/zmeny.json`](https://raw.githubusercontent.com/zdenekpesicka/AutomatizaceKatalogu/main/data/zmeny.json) | ID přidaných, změněných a odebraných míst od posledního běhu se změnou |
| [`schema/katalog.schema.json`](https://raw.githubusercontent.com/zdenekpesicka/AutomatizaceKatalogu/main/schema/katalog.schema.json) | JSON Schema (draft-07) pro validaci na straně příjemce |

Soubory jsou statické, staví se přímo z větve `main`, žádné API se neprovozuje. Aktuální verze schématu je **1.2.0**, uvedená v `meta.json` i v `katalog.json`. `data/ukazka.json` je zmrazená ilustrace k dokumentaci ve verzi 1.0.0, neaktualizuje se a neodebírá se.

**Popis polí, sémantika ID, kategorie, souřadnice a práce se `zmeny.json`: [`data/dokumentace-rozhrani.md`](data/dokumentace-rozhrani.md).**

## Aktualizace

| Workflow | Soubor | Zdroje | Plán (UTC) |
|---|---|---|---|
| **Denni import** | `.github/workflows/import.yml` | MPSV vždy, ÚZIS + RÚIAN při změně | `0 4 * * *` |
| **Rucni import (vynuti stazeni UZIS + RUIAN)** | `.github/workflows/import-mesicni.yml` | MPSV vždy, ÚZIS + RÚIAN vždy | bez plánu |

Čas v plánu je nejdřívější možný start, ne závazek. GitHub naplánované běhy řadí do fronty podle vytížení a spuštění může nastat i o několik hodin později; na konkrétní hodinu se proto nelze spoléhat. Skutečné časy jsou v historii běhů. Obě workflow jdou spustit ručně přes **Actions → vybrat workflow → Run workflow** (`workflow_dispatch`).

**Všechno obstarává denní běh, včetně ÚZIS a RÚIAN.** Ty se mění jen jednou měsíčně, takže by bylo plýtvání stahovat 92 MB každý den. Denní běh se proto nejdřív levně zeptá, jakou verzi zdroje právě nabízejí — ÚZIS přes hlavičku `Last-Modified`, ČÚZK přes název souboru v ATOM feedu — a z odpovědí složí klíč cache, například `uzis-ruian-2026-09-01-2026-08-31`:

| Situace | Co se stane |
|---|---|
| klíč sedí na uloženou cache | zdroje se nezměnily, stahují se jen data MPSV |
| klíč nesedí | zdroje vydaly novou verzi, ÚZIS i RÚIAN se stáhnou a uloží pod nový klíč |
| cache neexistuje | totéž, stáhne se |
| verzi nejde zjistit (výpadek zdroje) **a zároveň jsou oba soubory v cache** | pokračuje se nad poslední uloženou verzí, aby výpadek ČÚZK nezastavil i import MPSV |
| verzi nejde zjistit **a soubor chybí** | stáhne se; když ani to nejde, běh selže a `data/` zůstane beze změny |

Z MPSV se stahuje jedenáct souborů: `rpss.json`, jeho schéma a devět číselníků — druhy služeb, cílové skupiny, formy, typy kapacity, věkové skupiny a čtyři územní (kraje, okresy, obce, části obcí).

Protože klíč popisuje **data, ne kalendář**, nová verze se použije v nejbližším denním běhu po jejím vydání: jiná data mají jiný klíč, takže na obsazeném klíči nemůže uvíznout starší snapshot. Neplatí to bezvýhradně — klíč pokrývá jen případy, kdy sonda funguje, a proti trvale selhávající sondě stojí kontrola stáří zdrojů popsaná níže. Cache mizí po sedmi dnech bez přečtení, denní běh ji čtením sám udržuje.

Ruční workflow **Rucni import** dělá totéž co denní, jen ÚZIS a RÚIAN stahuje vždy načisto, bez ohledu na cache. Slouží k vynucení čerstvého stažení (poškozený snapshot, změna zpracování), běžný provoz ho nepotřebuje.

**Commit vzniká jen tehdy, když se data skutečně změnila.** Běh, který doběhne bez commitu, je úspěšný běh beze změny ve zdrojích, ne chyba. Že import proběhl, je vidět v historii běhů; `meta.json` proto záměrně neobsahuje čas běhu, jen údaje odvozené od dat. Změnu obsahu poznáte podle `hashKatalogu` v `meta.json`.

## Když běh selže

Do `data/` se nic nezapíše a zůstane poslední platná verze. Publikace se zastaví, pokud:

- testy nad zpracováním neprojdou (běží před stahováním, viz níže),
- některý ze zdrojů je starší než 50 dnů,
- u některého ze zdrojů se nepodařilo zjistit datum vydání a dosadilo se dnešní (platí bez ohledu na práh 50 dnů — dosazené datum je vždy čerstvé, takže by ho práh nikdy nezachytil),
- zdrojová data neprojdou validací proti schématu registru,
- výstup neobsahuje ani jedno místo,
- ve výstupu vznikne duplicitní `misto.id`,
- vlastní výstup neprojde validací proti `schema/katalog.schema.json`,
- se počet míst změní o víc než 5 % proti poslední publikované verzi,
- přibude víc než 30 míst bez souřadnic proti poslední publikované verzi.

Testy z `tests/` běží v obou workflow hned po instalaci závislostí, ještě před stahováním zdrojů: když je rozbité zpracování, nemá smysl tahat 190 MB dat. Nesahají na síť a chybějící `_cache/` jim nevadí, takže v tu chvíli mají všechno, co potřebují.

Kontrola stáří zdrojů hlídá stav, kdy sonda na verzi zdroje trvale selhává a běh se tiše drží starého snapshotu v cache — zelený build nad daty z loňska. Kontrole podléhají všechny tři zdroje; ÚZIS a RÚIAN vycházejí měsíčně, takže jejich zdravé maximum je kolem 32 dnů, MPSV vychází denně a k prahu se nikdy nepřiblíží. Při ručním běhu nad záměrně starým `_cache/` se kontrola překlene přepínačem `--zastarale-zdroje-ok`; tentýž přepínač povoluje i běh s dosazeným datem.

Prahové kontroly hlídají rozbitý zdroj: počet míst i počet míst bez souřadnic. Druhá zabírá tam, kde by se RÚIAN stáhl useknutý — míst by zůstal stejný počet, jen by přišly o souřadnice, a první kontrola by to nepoznala. Když je velká změna záměrná (úprava zpracování na naší straně), obojí se překlene ručním přepínačem `--zamerna-velka-zmena` při lokálním běhu. Workflow žádný z těchto přepínačů nepředává, v automatice tedy platí bez výjimky.

Oba přepínače `build_katalog.py` čte přímo z argumentů příkazu a nezná jiné; **překlep se proto neohlásí, jen se přepínač neuplatní** a běh skončí odmítnutím, jako by zadaný nebyl.

### Když selže opakovaně na stáří zdrojů

Selhání na dosazeném datu se za normálních okolností samo vyřeší příštím během. Pokud se opakuje každý den, může být v cache uložený snapshot, u kterého se datum vydání nepodařilo zjistit. Poznáte to podle toho, že krok **Stahni UZIS/RUIAN** hlásí `Cache odpovida aktualni verzi zdroju`, ale běh přesto padá na kontrole stáří.

Obnova je smazání cache; nový běh si data stáhne znovu:

```
gh cache list
gh cache delete <klíč>
```

Totéž jde v **Actions → Caches**. Ruční workflow na to nestačí: ukládá pod stejný klíč a `cache/save` na obsazeném klíči tiše skončí, takže uloženou cache nepřepíše.

Notifikace o selhání naplánovaného běhu chodí jen tomu, kdo workflow naposledy zapnul, a jen když má v **Settings → Notifications → System → Actions** přepnuto na Email (výchozí stav je „Don't notify"). Kdo workflow vypne a znovu zapne, stane se příjemcem.

## Lokální běh

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r import/requirements-dev.txt  # v CI běží Python 3.11
python -m pytest tests/ -q
python import/stahni_zdroje.py --all        # nebo --mpsv / --uzis-ruian
python import/build_katalog.py
```

`import/requirements.txt` obsahuje jen to, co potřebuje samotné sestavení katalogu; `requirements-dev.txt` k tomu přidává `pytest`.

Stažené zdroje se ukládají do `_cache/` (asi 190 MB, není verzované). `build_katalog.py` zapisuje do `data/` jen při skutečné změně obsahu, stejně jako v automatice.

## Struktura

```
import/             stahování zdrojů a sestavení katalogu
config/             mapování na kategorie webu: druhy sociálních služeb (MPSV)
                    i druhy zařízení (ÚZIS); klíče u ÚZIS zároveň určují,
                    které druhy jsou vůbec relevantní
data/               katalog.json, meta.json, zmeny.json, dokumentace, ukázka
schema/             katalog.schema.json
tests/              testy nad zpracováním, běží před stahováním
.github/workflows/  denní běh a ruční vynucené stažení
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
