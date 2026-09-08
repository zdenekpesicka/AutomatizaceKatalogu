# Dokumentace rozhraní — katalog registrovaných služeb pro seniory

Verze schématu 1.2.0. Viz `schema/katalog.schema.json` a `data/katalog.json` — plná data z ostrých dat MPSV a ÚZIS. Aktuální počet míst a datum zdrojových dat najdete vždy v `data/meta.json`; tady je záměrně neopakujeme, aby se obě čísla časem nerozešla.

## Soubory

| Soubor | K čemu slouží |
|---|---|
| `data/katalog.json` | Kompletní data. Načítejte vždy celý soubor, ne po částech. |
| `schema/katalog.schema.json` | JSON Schema (draft-07) pro validaci na vaší straně. Doporučujeme validovat při každém stažení. |
| `data/meta.json` | Verze schématu, hash obsahu, počty záznamů, datum zdrojových dat. Podle hashe poznáte, že se data změnila. **Neobsahuje čas běhu importu** — to, kdy import naposledy proběhl, není totéž jako to, kdy se data naposledy změnila. |
| `data/zmeny.json` | ID přidaných, změněných a odebraných míst od posledního běhu, kdy k reálné změně došlo. |
| `data/ukazka.json` | **Neodebírejte, nejsou to živá data.** Zmrazený výřez 32 míst, na kterém se odsouhlasila struktura a formát. Slouží už jen jako ilustrace k této dokumentaci a dál se neaktualizuje, proto v něm zůstává `verzeSchematu: "1.0.0"` a nenajdete v něm pole `sluzby[].zarizeni` přidané v 1.1.0 ani `sluzby[].oboryPece` přidané v 1.2.0. |

## Základní jednotka: místo, ne registrace

Jeden záznam v `mista[]` odpovídá jedné fyzické adrese (adresní bod RÚIAN), ne jedné registraci v registru. Na jedné adrese běžně sídlí víc služeb, případně od různých poskytovatelů (např. domov pro seniory jedné organizace a ambulantní poradna jiné organizace ve stejné budově) — proto `sluzby[]` je pole.

**`misto.id` je odvozené od `kodAdresnihoMista` (RÚIAN, `misto-<kod>`), a to vždy, bez ohledu na to, ze kterého registru záznam pochází.** Pokud se místo znovu objeví se stejnou adresou, dostane stejné ID — i když se mezitím změnilo složení služeb na té adrese. To je podstatné: když na adrese skončí poslední sociální registrace a zůstane jen zdravotnická (nebo naopak), **ID se nemění** a vy nemusíte nic přezakládat.

Zbývají dva případy bez RÚIAN kódu, kde se ID odvodit nedá:

| Situace | Tvar ID |
|---|---|
| Zařízení MPSV bez `kodAdresnihoMista` (cca 1,3 % aktivních) | `misto-bezadresy-<portalId>-<otisk názvu>` |
| Místo jen z ÚZIS, které nemá RÚIAN kód ani tam | `misto-uzis-bezadresy-<ID místa poskytování>` |

U prvního tvaru je název zařízení jediný rozlišovač, který registr nabízí — zařízení v MPSV nemá vlastní identifikátor. Když tedy MPSV název zařízení přepíše, dostane místo nové ID a ve `zmeny.json` se objeví jako odebrané a přidané. Týká se to řádově desítek míst z celého katalogu a spolehlivěji to nejde, dokud MPSV zařízením vlastní identifikátor nedá.

**U těchto míst může být celé `adresa` rovno `null`** — ne prázdný objekt, ale `null`. Registr u nich neuvádí ani ulici a obec, takže není co vypsat. Aktuálně je takových míst 36 z 39 bez RÚIAN kódu; zbylá 3 adresní text mají, jen k němu chybí kód (např. `misto-bezadresy-316-9d95f40b`, Žižkova, Příbram). **Ošetřete to při čtení**, `misto.adresa.obec` na těchto záznamech spadne. Místo samo je platné a má název, kontakt i kategorii, jen bez adresy se nedá umístit na mapu ani filtrovat podle území.

**Slučování napříč zdroji je vždy podle adresy, ne podle poskytovatele.** Pokud ÚZIS záznam sdílí `kodAdresnihoMista` s existujícím MPSV místem, stane se další položkou v jeho `sluzby[]`, i když jde o jiného poskytovatele (typicky nemocnice a zdravotní úsek v budově domova pro seniory). Rozlišujte proto zdroj podle `sluzby[].zdroj`, ne podle tvaru ID — z ID to poznat nejde a záměrně nemá.

**Jedno místo je jeden adresní bod, i když areál má bodů víc.** Registry evidují adresní body nezávisle a rozlehlejší areál jich má běžně několik: tentýž komplex může mít v MPSV jiný `kodAdresnihoMista` než v ÚZIS a i uvnitř jednoho registru má dům se dvěma vchody dva body. Slučování je nespojí, takže v katalogu zůstanou dvě místa se stejným IČO pár desítek metrů od sebe. **19 takových dvojic vzniká mezi registry** (jedno místo jen z ÚZIS, druhé se sociální službou téhož poskytovatele, 10 až 95 m — např. `misto-14264633` a `misto-72537001`, Charita Šumperk, 25 m) a **dalších 143 uvnitř jednoho zdroje**. Ty druhé ale z velké části oddělené být mají, jde o sousední budovy jedné organizace, ne o jeden areál. Rozlišit to za vás nemůžeme — registry vazbu „tyto body patří k sobě“ nevedou a dopočítávat ji ze vzdálenosti by znamenalo vymýšlet data. Pokud vám blízké piny vadí, shlukněte si je na frontendu podle shody `sluzby[].poskytovatel.ico` a vzdálenosti; kde je hranice, je pak vaše rozhodnutí.

Souřadnice chybí u části míst ze dvou různých důvodů. **Kód adresního místa je vyplněný, ale aktuální snapshot RÚIAN ho nezná** (2,4 % míst) — RÚIAN se aktualizuje měsíčně a adresní bod mezitím mohl vzniknout nebo být přečíslován. `misto.id` je v tomto případě normální `misto-<kód>` a je stabilní, `null` jsou jen souřadnice; s dalším měsíčním během RÚIAN se část z nich doplní. Druhá skupina jsou místa **bez kódu adresního místa vůbec** (tvary ID z tabulky výše), tam se souřadnice dohledat nemá z čeho a stav se sám nezlepší. V obou případech je `souradnice.lat/lng` rovno `null`, viz sekce Souřadnice níže.

## Jedna registrace je v `sluzby[]` právě jednou (`zarizeni`)

**`sluzby[].id` je v rámci jednoho místa unikátní.** Můžete podle něj bezpečně párovat, klíčovat v Reactu i deduplikovat na své straně.

Není to samozřejmé, protože MPSV vede pod jednou registrací seznam zařízení a jedna registrace může mít na jedné adrese víc zařízení — typicky pečovatelská služba a její středisko osobní hygieny v témže domě, nebo dvě nadzemní podlaží jedné budovy. Do verze 1.0.0 se taková registrace objevila v `sluzby[]` vícekrát se stejným `id`.

Od 1.1.0 je registrace v poli jednou a názvy zařízení nese nepovinné pole `zarizeni`:

```json
{
  "id": "mpsv-2627",
  "zdroj": "MPSV",
  "nazev": "Pečovatelská služba",
  "zarizeni": ["Pečovatelská služba", "Středisko osobní hygieny"],
  "formy": [{"forma": "ter", "kapacitaRegistrovana": [{"typ": "klient", "typNazev": "Počet klientů", "pocet": 62}]}]
}
```

Pravidla, na která se můžete spolehnout:

- `zarizeni` je **jen u `zdroj: "MPSV"`** a **jen tam, kde má registrace na daném místě víc než jedno zařízení**. Jinak pole chybí úplně a název je v `nazev`. Čtěte tedy `sluzby[].zarizeni ?? [sluzby[].nazev]`.
- Když je pole přítomné, `nazev` je vždy jeho první prvek. Žádný název se cestou neztrácí.
- Týká se to dnes 11 položek v celém katalogu, ale spoléhejte na pravidlo, ne na to číslo.

**Proč to bylo potřeba: kapacita je v MPSV registrovaná na službu, ne na zařízení.** Dokud byla registrace v poli dvakrát, byla dvakrát i její kapacita. U Domova Chrudim (`misto-27763331`) jsou registrace tři — 20, 5 a 95 lůžek, dohromady 120 — ale ta poslední byla v poli dvakrát, jednou za 2. a jednou za 3. nadzemní podlaží, takže součet přes `sluzby[]` dával 215. Teď se sčítat dá.

Poslední věc k názvům v `zarizeni`: u čtyř zařízení uvádí MPSV název jednoho města a adresní kód jiného (např. „Ledax o.p.s. středisko Prachatice“ s adresním bodem v Týně nad Vltavou). Místo umisťujeme podle kódu, tedy správně; nesprávný je název. Opravit ho nemůžeme, dohledat správné přiřazení není z čeho — proto ho vypisujeme tak, jak ho registr vede. Když název zařízení zobrazujete, počítejte s tím, že nemusí odpovídat obci v `adresa`.

## Kategorie (`kategorie`)

Pole hodnot z `domovy`, `terenni`, `bezpeci`, `zdravi`, odpovídá záložkám na webu. Jedno místo může mít víc kategorií zároveň, pokud tam sídlí služby z různých kategorií.

**Důležité:** pole může být prázdné (`[]`). Nejde o chybu, ale o službu, jejíž druh naše mapovací tabulka zatím nezařazuje do žádné záložky (typicky odborné sociální poradenství a několik dalších menších druhů služeb — netýká se domovů, terénních služeb ani zdravotní péče). Tato místa jsou ve výstupu, aby se informace neztratila, ale nezobrazí se v žádné záložce, dokud se zařazení nedořeší. Řešíme to s klientem zvlášť, ne teď v rámci tohoto schématu.

## `poskytujeZdravotniPeci`

Příznak, že na tomto místě funguje i zdravotní péče uvnitř sociálního zařízení (typicky ošetřovatelský úsek domova pro seniory, evidovaný v registru ÚZIS zvlášť). **Není to samostatný záznam** — informace se připojuje k existujícímu místu, ne jako duplicitní položka v `sluzby[]`. V ukázkových datech viz `misto-79121519`.

Nejde o zařízení, kam se dá jít, ale o zdravotnickou licenci, kterou musí mít domov, aby směl zaměstnávat sestry. Proto z ní **nikdy nevzniká místo ani položka v `sluzby[]`** — buď se připojí jako tento příznak k domovu, nebo, když domov v katalogu není (jeho zřizovatel neposkytuje seniorskou sociální službu, typicky domovy pro osoby se zdravotním postižením), do výstupu nejde vůbec. Důsledek pro vás: v záložce Zdraví jsou jen služby, které si klient může sám vybrat — hospice, LDN, domácí péče, nemocnice následné péče a rehabilitační ústavy — ne ošetřovatelské úseky domovů, které by tam jinak tvořily druhý pin pár desítek metrů od domova samotného.

**Záměrně a trvale se nepromítá do `kategorie[]`.** `poskytujeZdravotniPeci: true` nikdy automaticky nepřidává `zdravi` do kategorií místa. Jde o interní ošetřovatelský úsek konkrétního domova, ne o samostatně vyhledávanou zdravotní službu typu hospic/LDN/domácí péče — proto zůstává jen jako doplňkový příznak (např. badge na kartě domova), místo se dál řadí jen podle svých vlastních služeb. Pokud budete chtít filtrovat i podle tohoto příznaku, udělejte to na frontendu nad `poskytujeZdravotniPeci`, ne přes `kategorie`.

## Souřadnice (`souradnice`)

Vždy objekt `{"lat": ..., "lng": ...}`, nikdy vynechané pole. `lat`/`lng` jsou `null`, když se souřadnice nepodařilo určit — v ukázce viz `misto-bezadresy-4674-f7e6ac50` (místo bez kódu adresního místa) a `misto-80030152` (kód je vyplněný, jen ho snapshot RÚIAN nezná). Souřadnice jsou vždy WGS84 (běžný formát pro mapy, GPS), i u zdrojů, které interně používají jiný systém.

## Formy a kapacita (`formy`, `kapacitaRegistrovana`)

`sluzby[].formy` je pole, jedna položka za každou formu poskytování (`amb`/`pob`/`ter`), a **kapacita je vždy uvnitř konkrétní formy**, ne jedno společné pole za celou službu — služba může mít víc forem zároveň (typicky odlehčovací služby pobytové i ambulantní) a jejich kapacity se nesčítají ani jinak neslučují, jde o oddělené kapacity oddělených provozů. Např.:

```json
"formy": [
  {"forma": "pob", "kapacitaRegistrovana": [{"typ": "luzka", "typNazev": "Počet lůžek", "pocet": 24}]},
  {"forma": "ter", "kapacitaRegistrovana": [{"typ": "klient", "typNazev": "Počet klientů", "pocet": 1}]}
]
```

Kapacita je registrovaná **na službu, ne na zařízení**. Každá registrace je v `sluzby[]` právě jednou (viz sekce výše), takže součet kapacit přes `sluzby[]` jednoho místa je správný a nic se v něm nezapočítá dvakrát.

**`kapacitaRegistrovana` je registrovaná maximální kapacita, ne aktuální volná místa.** Registr volná místa neobsahuje. Pole `typ` nabývá hodnot `klient`, `kontakt`, `interv`, `luzka`, `hovor` (počet klientů / kontaktů 10min. jednání / intervencí 30min. jednání / lůžek / hovorů) — jednotku vždy zobrazujte podle `typNazev`, ať nevznikne třeba "32 lůžek" u pečovatelské služby, která lůžka nemá.

## Adresa u zdroje ÚZIS: `cisloOrientacni` může obsahovat obojí

U `zdroj: "MPSV"` jsou `cisloDomovni` a `cisloOrientacni` dvě oddělená pole tak, jak je má MPSV. ÚZIS ale popisné a orientační číslo eviduje v jednom sloupci (typicky ve tvaru `"2063/46"`) — u míst ze zdroje ÚZIS je tedy `cisloDomovni` vždy `null` a celá hodnota (i s lomítkem) je v `cisloOrientacni`. Není to chyba zpracování, je to formát zdrojových dat ÚZIS. Při zobrazení adresy u ÚZIS míst tedy nezkoušejte `cisloDomovni`/`cisloOrientacni` skládat jako u MPSV, vypište `cisloOrientacni` tak, jak je.

## Kódy obce, okresu a kraje (`kodObce`, `kodOkresu`, `kodKraje`)

Vedle textového názvu je u obce, okresu a kraje k dispozici i oficiální kód pro jednoznačné rozlišení (např. "Kraj Vysočina" vs. "Vysočina", nebo shodné názvy obcí v různých krajích): `kodObce` je číselný kód ČSÚ/RÚIAN (např. `554782` pro Prahu), `kodOkresu` je kód LAU 1 (např. `CZ0100` pro Prahu, `CZ020A` pro Prahu-západ), `kodKraje` je kód NUTS 3 (např. `CZ010` pro Prahu). `kodOkresu`/`kodKraje` mají stejný formát u obou zdrojů (MPSV i ÚZIS mají tento kód přímo v datech). U míst čistě ze zdroje ÚZIS `kodObce` v samotných ÚZIS datech chybí (jen textový název), proto se dohledává přes RÚIAN (stejný zdroj jako souřadnice, přes `ZZ_RUIAN_kod`) — pokrytí 99,7 %, tedy 649 ze 651 míst čistě ze zdroje ÚZIS. `kodObce` je `null` jen výjimečně, u míst bez dohledaného RÚIAN bodu (stejná skupina jako místa bez souřadnic, viz výše).

**Filtrujte a seskupujte podle kódu, ne podle názvu obce.** Textový název přebíráme z registru, ze kterého místo pochází, a oba registry ho pro Prahu píší jinak: místa se sociální službou mají `obec: "Praha"` (193 míst), místa jen ze zdroje ÚZIS mají městskou část, tedy `"Praha 1"` až `"Praha 16"` (83 míst). Filtr na `obec == "Praha"` by vám tedy 83 pražských míst zahodil. `kodObce` je přitom u 276 z těch 277 míst shodně `554782` (u jednoho se RÚIAN bod nedohledal, viz výše), takže při filtrování podle kódu problém nevzniká. Totéž platí obecně — název je pro zobrazení, kód pro logiku.

## IČO

Vždy 8 znaků, jen číslice, jako text (`"03017621"` je platné IČO se sedmi platnými číslicemi a úvodní nulou — nikdy nepřevádět na číslo).

## Kontakty

`kontakt.weby/emaily/telefony` jsou vždy pole (i prázdné), nikdy jedna hodnota. Pravidlo: nejdřív kontakt konkrétní služby, a když ho registr nemá, kontakt poskytovatele jako celku — obojí je v `mista.sluzby[].kontakt` už sloučené, žádné další rozlišování není potřeba.

## Zdroj (`zdroj`)

`MPSV` (sociální služby, id začíná `mpsv-`) nebo `UZIS` (zdravotní služby, id začíná `uzis-`). Pole `formy` dává smysl jen u `MPSV` (u ÚZIS chybí úplně, ne prázdné pole). Pole `oborPece` a `oboryPece` jen u `UZIS`.

## Obor péče (`oborPece`, `oboryPece`)

**Používejte `oboryPece`.** Zdrojové pole ÚZIS je vícehodnotové, obory jsou v jedné buňce oddělené čárkou. `oboryPece` je pole se všemi obory v pořadí registru (prázdné, když registr obor neuvádí), `oborPece` je jen jeho první prvek.

`oborPece` existovalo dřív než `oboryPece` a zůstává kvůli kompatibilitě se schématem 1.0.0. Kdo podle něj filtruje, přijde o obory na dalších pozicích: ze 930 publikovaných ÚZIS služeb jich 242 uvádí oborů víc, maximum na jedné službě je 32. Konkrétně u 20 služeb není v `oborPece` vidět „paliativní medicína", protože ji registr neuvádí jako první — mezi nimi Hospicová péče sv. Kleofáše a PAHOP. Pro rozpoznání hospicové a paliativní péče je proto `oboryPece` jediné použitelné pole.

## Datum poskytování (`datumPoskytovaniOd`, `datumPoskytovaniDo`)

Jen u `MPSV`. `datumPoskytovaniOd` je vyplněné u všech položek. `datumPoskytovaniDo` je u služby, která má v registru evidované ukončení, jinak `null`.

**Ve výstupu je `datumPoskytovaniDo` vždy buď `null`, nebo v budoucnosti, nikdy v minulosti.** Ukončené registrace se do katalogu nedostanou: v registru jich je 380 z 2 602 seniorských služeb, do výstupu nejde ani jedna. Zůstává jen 9 služeb s ohlášeným ukončením k budoucímu datu, které se ve výstupu objeví jako 16 položek (jedna registrace může být na víc adresních bodech), tedy 0,4 %. Příjemce tak nemusí datum sám vyhodnocovat — co je v katalogu, to se poskytuje.

## `zmeny.json` a zaniklé záznamy

Formát:
```json
{
  "verzeSchematu": "1.2.0",
  "pridano": ["misto-123456"],
  "zmeneno": ["misto-234567"],
  "odebrano": ["misto-345678"]
}
```
Zaniklé místo je **explicitně** v `odebrano`, nikdy se nemá odvozovat z toho, že v novém `katalog.json` chybí. Pokud se od posledního běhu nic nezměnilo, `zmeny.json` se nepřepisuje — zůstává poslední platná verze, nikdy nedostanete prázdný seznam změn, který byste museli rozlišovat od chyby.

**Nespoléhejte se na pořadí prvků v `mista[]` ani v `sluzby[]`.** Kopíruje pořadí záznamů ve zdrojových registrech a není nijak garantované — párujte vždy podle `id`, tak jak to dělá i `zmeny.json`. Kdyby některý registr vyexportoval tatáž data v jiném pořadí, dostanete `katalog.json` s jinak seřazenými prvky, ale `zmeny.json` u něj bude hlásit nulové změny. To je korektní stav, ne chyba: obsah je stejný, jen přeskupený.

## Verzování

`verzeSchematu` je sémantické verzování (`MAJOR.MINOR.PATCH`). Nekompatibilní změna (přejmenování/odebrání pole, změna typu) zvedne MAJOR verzi a bude ohlášena dopředu, nikdy tichým přepsáním produkčních dat.

| Verze | Změna |
|---|---|
| 1.2.0 | Přibylo nepovinné `sluzby[].oboryPece` s úplným seznamem oborů péče. `oborPece` zůstává beze změny typu i obsahu, čtenář 1.1.0 běží dál beze změny. Ověřeno porovnáním celého výstupu: proti 1.1.0 se u žádného z 2 912 míst nezměnilo nic jiného než přibylé pole, `oborPece` se u žádné z 930 ÚZIS služeb neliší od prvního prvku `oboryPece`. Ve `zmeny.json` je 890 míst jako změněná (ta, která obsahují ÚZIS službu), 0 přidaných a 0 odebraných. |
| 1.1.0 | Přibylo nepovinné `sluzby[].zarizeni`. Registrace je nově v `sluzby[]` právě jednou, takže `sluzby[].id` je v rámci místa unikátní a kapacity se dají sčítat. Zároveň se přestaly publikovat služby s ukončenou registrací (viz Datum poskytování). Žádné pole nezmizelo ani nezměnilo typ, čtenář 1.0.0 běží dál beze změny. Přechodový běh označil ve `zmeny.json` 15 míst jako změněná a 6 jako odebraná (ty s ukončenou registrací), žádné jako přidané. U změněných míst se lišilo výhradně pole `sluzby` — `misto.id`, souřadnice, adresy, kategorie ani `poskytujeZdravotniPeci` se nezměnily u žádného místa. |
| 1.0.0 | Výchozí odsouhlasené schéma. |

## Provoz

Aktualizace je automatická: MPSV denně (`0 4 * * *` UTC), ÚZIS a RÚIAN měsíčně (`0 5 3 * *` UTC), obojí přes GitHub Actions. Naplánované běhy nemají garantovaný čas, zpoždění 5 až 30 minut je běžné.

**Commit vzniká jen tehdy, když se obsah `katalog.json` skutečně změnil.** Běh bez commitu je úspěšný běh beze změny ve zdrojích, ne chyba. Změnu poznáte podle `hashKatalogu` v `meta.json`.

Před každou publikací běží validace zdrojových dat proti schématu registru, validace výstupu proti `schema/katalog.schema.json`, kontrola na duplicitní `misto.id` a prahová kontrola na změnu počtu míst o víc než 5 %. Když kterákoli neprojde, do `data/` se nezapíše nic a zůstane poslední platná verze — nikdy nedostanete prázdný ani useknutý soubor.
