# Dokumentace rozhraní — katalog registrovaných služeb pro seniory

Verze schématu 1.0.0. Viz `schema/katalog.schema.json` a `data/katalog.json` — plná data, 3 252 míst z ostrých dat MPSV a ÚZIS (stav zdrojových dat: MPSV 31. 8. 2026, ÚZIS 1. 9. 2026, RÚIAN 31. 7. 2026, viz `data/meta.json`).

## Soubory

| Soubor | K čemu slouží |
|---|---|
| `data/katalog.json` | Kompletní data. Načítejte vždy celý soubor, ne po částech. |
| `schema/katalog.schema.json` | JSON Schema (draft-07) pro validaci na vaší straně. Doporučujeme validovat při každém stažení. |
| `data/meta.json` | Verze schématu, hash obsahu, počty záznamů, datum zdrojových dat. Podle hashe poznáte, že se data změnila. **Neobsahuje čas běhu importu** — to, kdy import naposledy proběhl, není totéž jako to, kdy se data naposledy změnila. |
| `data/zmeny.json` | ID přidaných, změněných a odebraných míst od posledního běhu, kdy k reálné změně došlo. |

## Základní jednotka: místo, ne registrace

Jeden záznam v `mista[]` odpovídá jedné fyzické adrese (adresní bod RÚIAN), ne jedné registraci v registru. Na jedné adrese běžně sídlí víc služeb, případně od různých poskytovatelů (např. domov pro seniory jedné organizace a ambulantní poradna jiné organizace ve stejné budově) — proto `sluzby[]` je pole.

`misto.id` je odvozené od `kodAdresnihoMista` (RÚIAN, `misto-<kod>`) a je stabilní mezi jednotlivými běhy — pokud se místo znovu objeví se stejnou adresou, dostane stejné ID. Pro malou část záznamů (u aktivních seniorských zařízení MPSV k 31. 8. 2026 cca 1,8 %) `kodAdresnihoMista` chybí; tyto záznamy mají náhradní stabilní ID `misto-bezadresy-<portalId>`. Obdobně místa vzniklá čistě ze zdravotnických dat ÚZIS mají ID `misto-uzis-<ID místa poskytování>`, případně `misto-uzis-bezadresy-<ID>`, pokud ani ÚZIS nemá RÚIAN kód.

**Slučování napříč zdroji je vždy podle adresy, ne podle poskytovatele.** Pokud ÚZIS záznam sdílí `kodAdresnihoMista` s existujícím MPSV místem, stane se další položkou v jeho `sluzby[]` (dostane `misto-<kód>` ID toho místa), i když jde o jiného poskytovatele (typicky nemocnice a zdravotní úsek v budově domova pro seniory). Samostatné `misto-uzis-*` vzniká jen tam, kde na dané adrese žádné MPSV místo není.

I když se `misto.kodAdresnihoMista` v datech najde, souřadnice se u malé části adres (aktuálně cca 3 %) nepodařilo dohledat, protože RÚIAN je aktualizovaný měsíčně a mezitím mohl být adresní bod přečíslován — `souradnice.lat/lng` je pak `null`, jak popisuje sekce Souřadnice níže.

## Kategorie (`kategorie`)

Pole hodnot z `domovy`, `terenni`, `bezpeci`, `zdravi`, odpovídá záložkám na webu. Jedno místo může mít víc kategorií zároveň, pokud tam sídlí služby z různých kategorií.

**Důležité:** pole může být prázdné (`[]`). Nejde o chybu, ale o službu, jejíž druh naše mapovací tabulka zatím nezařazuje do žádné záložky (typicky odborné sociální poradenství a několik dalších menších druhů služeb — netýká se domovů, terénních služeb ani zdravotní péče). Tato místa jsou ve výstupu, aby se informace neztratila, ale nezobrazí se v žádné záložce, dokud se zařazení nedořeší. Řešíme to s klientem zvlášť, ne teď v rámci tohoto schématu.

## `poskytujeZdravotniPeci`

Příznak, že na tomto místě funguje i zdravotní péče uvnitř sociálního zařízení (typicky ošetřovatelský úsek domova pro seniory, evidovaný v registru ÚZIS zvlášť). **Není to samostatný záznam** — informace se připojuje k existujícímu místu, ne jako duplicitní položka v `sluzby[]`. V ukázkových datech viz `misto-79121519`.

**Záměrně a trvale se nepromítá do `kategorie[]`.** `poskytujeZdravotniPeci: true` nikdy automaticky nepřidává `zdravi` do kategorií místa. Jde o interní ošetřovatelský úsek konkrétního domova, ne o samostatně vyhledávanou zdravotní službu typu hospic/LDN/domácí péče — proto zůstává jen jako doplňkový příznak (např. badge na kartě domova), místo se dál řadí jen podle svých vlastních služeb. Pokud budete chtít filtrovat i podle tohoto příznaku, udělejte to na frontendu nad `poskytujeZdravotniPeci`, ne přes `kategorie`.

## Souřadnice (`souradnice`)

Vždy objekt `{"lat": ..., "lng": ...}`, nikdy vynechané pole. `lat`/`lng` jsou `null`, když se souřadnice nepodařilo určit (viz `misto-bezadresy-4674` v ukázce). Souřadnice jsou vždy WGS84 (běžný formát pro mapy, GPS), i u zdrojů, které interně používají jiný systém.

## Formy a kapacita (`formy`, `kapacitaRegistrovana`)

`sluzby[].formy` je pole, jedna položka za každou formu poskytování (`amb`/`pob`/`ter`), a **kapacita je vždy uvnitř konkrétní formy**, ne jedno společné pole za celou službu — služba může mít víc forem zároveň (typicky odlehčovací služby pobytové i ambulantní) a jejich kapacity se nesčítají ani jinak neslučují, jde o oddělené kapacity oddělených provozů. Např.:

```json
"formy": [
  {"forma": "pob", "kapacitaRegistrovana": [{"typ": "luzka", "typNazev": "Počet lůžek", "pocet": 24}]},
  {"forma": "ter", "kapacitaRegistrovana": [{"typ": "klient", "typNazev": "Počet klientů", "pocet": 1}]}
]
```

**`kapacitaRegistrovana` je registrovaná maximální kapacita, ne aktuální volná místa.** Registr volná místa neobsahuje. Pole `typ` nabývá hodnot `klient`, `kontakt`, `interv`, `luzka`, `hovor` (počet klientů / kontaktů 10min. jednání / intervencí 30min. jednání / lůžek / hovorů) — jednotku vždy zobrazujte podle `typNazev`, ať nevznikne třeba "32 lůžek" u pečovatelské služby, která lůžka nemá.

## Adresa u zdroje ÚZIS: `cisloOrientacni` může obsahovat obojí

U `zdroj: "MPSV"` jsou `cisloDomovni` a `cisloOrientacni` dvě oddělená pole tak, jak je má MPSV. ÚZIS ale popisné a orientační číslo eviduje v jednom sloupci (typicky ve tvaru `"2063/46"`) — u míst ze zdroje ÚZIS je tedy `cisloDomovni` vždy `null` a celá hodnota (i s lomítkem) je v `cisloOrientacni`. Není to chyba zpracování, je to formát zdrojových dat ÚZIS. Při zobrazení adresy u ÚZIS míst tedy nezkoušejte `cisloDomovni`/`cisloOrientacni` skládat jako u MPSV, vypište `cisloOrientacni` tak, jak je.

## Kódy obce, okresu a kraje (`kodObce`, `kodOkresu`, `kodKraje`)

Vedle textového názvu je u obce, okresu a kraje k dispozici i oficiální kód pro jednoznačné rozlišení (např. "Kraj Vysočina" vs. "Vysočina", nebo shodné názvy obcí v různých krajích): `kodObce` je číselný kód ČSÚ/RÚIAN (např. `554782` pro Prahu), `kodOkresu` je kód LAU 1 (např. `CZ0100` pro Prahu, `CZ020A` pro Prahu-západ), `kodKraje` je kód NUTS 3 (např. `CZ010` pro Prahu). `kodOkresu`/`kodKraje` mají stejný formát u obou zdrojů (MPSV i ÚZIS mají tento kód přímo v datech). U míst čistě ze zdroje ÚZIS `kodObce` v samotných ÚZIS datech chybí (jen textový název), proto se dohledává přes RÚIAN (stejný zdroj jako souřadnice, přes `ZZ_RUIAN_kod`) — pokrytí 99,8 %. `kodObce` je `null` jen výjimečně, u míst bez dohledaného RÚIAN bodu (stejná skupina jako místa bez souřadnic, viz výše).

## IČO

Vždy 8 znaků, jen číslice, jako text (`"03017621"` je platné IČO se sedmi platnými číslicemi a úvodní nulou — nikdy nepřevádět na číslo).

## Kontakty

`kontakt.weby/emaily/telefony` jsou vždy pole (i prázdné), nikdy jedna hodnota. Pravidlo: nejdřív kontakt konkrétní služby, a když ho registr nemá, kontakt poskytovatele jako celku — obojí je v `mista.sluzby[].kontakt` už sloučené, žádné další rozlišování není potřeba.

## Zdroj (`zdroj`)

`MPSV` (sociální služby, id začíná `mpsv-`) nebo `UZIS` (zdravotní služby, id začíná `uzis-`). Pole `formy` dává smysl jen u `MPSV` (u ÚZIS chybí úplně, ne prázdné pole). Pole `oborPece` jen u `UZIS`.

## Datum poskytování (`datumPoskytovaniOd`, `datumPoskytovaniDo`)

Jen u `MPSV`. `datumPoskytovaniOd` je vyplněné u všech seniorských služeb, `datumPoskytovaniDo` jen u služeb, které mají v registru evidované ukončení (cca 15 %) — u aktivní služby je `null`. Do výstupu jdou jen aktivní služby (viz filtr v `import/mpsv.py`), takže `datumPoskytovaniDo` tu buď chybí, nebo je v budoucnosti, nikdy v minulosti.

## `zmeny.json` a zaniklé záznamy

Formát:
```json
{
  "verzeSchematu": "1.0.0",
  "pridano": ["misto-123456"],
  "zmeneno": ["misto-234567"],
  "odebrano": ["misto-345678"]
}
```
Zaniklé místo je **explicitně** v `odebrano`, nikdy se nemá odvozovat z toho, že v novém `katalog.json` chybí. Pokud se od posledního běhu nic nezměnilo, `zmeny.json` se nepřepisuje — zůstává poslední platná verze, nikdy nedostanete prázdný seznam změn, který byste museli rozlišovat od chyby.

## Verzování

`verzeSchematu` je sémantické verzování (`MAJOR.MINOR.PATCH`). Nekompatibilní změna (přejmenování/odebrání pole, změna typu) zvedne MAJOR verzi a bude ohlášena dopředu, nikdy tichým přepsáním produkčních dat.

## Co ve schématu ještě chybí a doplní se v další fázi

- Automatizované denní/měsíční běhy a pojistky (validace, prahové kontroly, commit jen při změně) — teď je `data/katalog.json` výsledkem ručně spuštěného plného běhu, ne automatizace.
- `data/zmeny.json` u tohoto běhu obsahuje jen `pridano` (jde o první produkční verzi, nemá se s čím porovnávat). Od příštího běhu, kdy už bude existovat předchozí verze, se budou plnit i `zmeneno` a `odebrano`.
