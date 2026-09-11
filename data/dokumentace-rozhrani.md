# Dokumentace rozhraní — katalog registrovaných služeb pro seniory

Verze schématu 1.3.0. Viz `schema/katalog.schema.json` a `data/katalog.json` — plná data z ostrých dat MPSV a ÚZIS. Aktuální počet míst a datum zdrojových dat najdete vždy v `data/meta.json`; tady je záměrně neopakujeme, aby se obě čísla časem nerozešla.

## Soubory

| Soubor | K čemu slouží |
|---|---|
| `data/katalog.json` | Kompletní data. Načítejte vždy celý soubor, ne po částech. |
| `schema/katalog.schema.json` | JSON Schema (draft-07) pro validaci na vaší straně. Doporučujeme validovat při každém stažení. |
| `data/meta.json` | Verze schématu, hash obsahu, počty záznamů, datum zdrojových dat. Podle hashe poznáte, že se data změnila. **Neobsahuje čas běhu importu** — to, kdy import naposledy proběhl, není totéž jako to, kdy se data naposledy změnila. |
| `data/zmeny.json` | ID přidaných, změněných a odebraných míst od posledního běhu, kdy k reálné změně došlo. |
| `data/ukazka.json` | **Neodebírejte, nejsou to živá data.** Zmrazený výřez 32 míst, na kterém se odsouhlasila struktura a formát. Slouží už jen jako ilustrace k této dokumentaci a dál se neaktualizuje, proto v něm zůstává `verzeSchematu: "1.0.0"` a nenajdete v něm pole `sluzby[].zarizeni` přidané v 1.1.0, `sluzby[].oboryPece` přidané v 1.2.0 ani kategorii `poradenstvi` přidanou v 1.3.0. |

## Struktura souboru

`katalog.json` má dva kořenové klíče: `verzeSchematu` a `mista[]`. Každé místo má tato pole, všechna povinná a nikdy vynechaná:

```
misto
├─ id                        string   stabilní identifikátor, viz níže
├─ kodAdresnihoMista         int|null kód adresního bodu RÚIAN, ze kterého je odvozené id
├─ adresa                    obj|null ulice, cisloDomovni, cisloOrientacni, psc,
│                                     obec, kodObce, castObce, okres, kodOkresu, kraj, kodKraje
├─ souradnice                obj      { lat, lng }, obě mohou být null
├─ kategorie                 [string] může být prázdné pole
├─ poskytujeZdravotniPeci    bool
└─ sluzby                    [obj]    nikdy prázdné
   ├─ id                     string   "mpsv-<n>" nebo "uzis-<n>"
   ├─ zdroj                  string   "MPSV" | "UZIS"
   ├─ nazev                  string
   ├─ poskytovatel           obj      { nazev, ico }
   ├─ druhSluzby             obj      { kod, nazev }
   ├─ formy                  [obj]    jen u MPSV, jinak pole chybí
   ├─ zarizeni               [string] nepovinné, viz níže
   ├─ oborPece / oboryPece            jen u UZIS, jinak chybí
   ├─ datumPoskytovaniOd/Do  str|null jen u MPSV
   └─ kontakt                obj      { weby, emaily, telefony } — vždy pole
```

Následující počty se vztahují **k vyplněným objektům `adresa`**, tedy k 2 871 z 2 907 míst — u zbylých 36 je celá `adresa` rovna `null`. Uvnitř `adresa` je `obec` vyplněná vždy, `psc`, `kodObce`, `kraj` a `kodKraje` až na jednotky případů; `ulice` chybí u 347 (obce, kde se adresuje jen číslem popisným), `cisloDomovni` u 651 (místa ze zdroje ÚZIS, viz sekce o číslech níže), `castObce` u 653 (ÚZIS ji nevede vůbec), `okres`/`kodOkresu` u 193 a `kraj`/`kodKraje` u 2. Sekce o kódech níže uvádí u okresu číslo 229 — to je táž skupina počítaná **přes všech 2 907 míst**, tedy 193 s adresou plus 36 bez ní.

`cisloDomovni` je **číslo** (`int`), `cisloOrientacni` **řetězec** (`"54"`, u zdroje ÚZIS i `"2063/46"`). Obě mohou být `null`.

`poskytovatel.nazev` je úřední název subjektu z registru, ne obchodní značka — u jednoho místa se běžně liší od `sluzby[].nazev`, který je názvem konkrétní služby. Pro zobrazení na kartě používejte `sluzby[].nazev`, pro párování `poskytovatel.ico`.

## Druh služby (`druhSluzby`)

Objekt `{ "kod": ..., "nazev": ... }`. **Kódy z obou registrů jsou v jiném jmenném prostoru a nikdy se neporovnávají mezi sebou** — MPSV má tvar `"DruhSocialniSluzby/13"` (druh sociální služby), ÚZIS holé číslo v uvozovkách, `"110"` (druh zdravotnického zařízení). Před porovnáním kódu se proto vždy nejdřív ptejte na `zdroj`, jinak vám kód `"110"` a `"DruhSocialniSluzby/110"` splynou nebo naopak rozejdou.

```json
{"kod": "DruhSocialniSluzby/13", "nazev": "domovy pro seniory"}
{"kod": "110", "nazev": "Léčebna pro dlouhodobě nemocné (LDN)"}
```

`nazev` přebíráme z číselníku registru včetně způsobu psaní — MPSV píše druhy malým písmenem, ÚZIS velkým. Nesjednocujeme to, protože jde o hodnotu číselníku.

## Základní jednotka: místo, ne registrace

Jeden záznam v `mista[]` odpovídá jedné fyzické adrese (adresní bod RÚIAN), ne jedné registraci v registru. Na jedné adrese běžně sídlí víc služeb, případně od různých poskytovatelů (např. domov pro seniory jedné organizace a ambulantní poradna jiné organizace ve stejné budově) — proto `sluzby[]` je pole.

**`misto.id` je odvozené od `kodAdresnihoMista` (RÚIAN, `misto-<kod>`), a to vždy, bez ohledu na to, ze kterého registru záznam pochází.** Pokud se místo znovu objeví se stejnou adresou, dostane stejné ID — i když se mezitím změnilo složení služeb na té adrese. To je podstatné: když na adrese skončí poslední sociální registrace a zůstane jen zdravotnická (nebo naopak), **ID se nemění** a vy nemusíte nic přezakládat.

Zbývají dva případy bez RÚIAN kódu, kde se ID odvodit nedá:

| Situace | Tvar ID |
|---|---|
| Zařízení MPSV bez `kodAdresnihoMista` (cca 1,3 % aktivních) | `misto-bezadresy-<portalId>-<otisk názvu>` |
| Místo jen z ÚZIS, které nemá RÚIAN kód ani tam | `misto-uzis-bezadresy-<ID místa poskytování>` |

**Číslo v `misto-uzis-bezadresy-<n>` není totéž číslo jako v `uzis-<n>`.** ID místa je odvozené od `ZZ_misto_poskytovani_ID`, kdežto `sluzby[].id` od `ZZ_ID`; jsou to dva různé identifikátory téhož registru. Aktuálně je takové místo jediné (`misto-uzis-bezadresy-259989` se službou `uzis-180066`), ale nepokoušejte se jedno z druhého odvozovat.

U prvního tvaru je název zařízení jediný rozlišovač, který registr nabízí — zařízení v MPSV nemá vlastní identifikátor. Když tedy MPSV název zařízení přepíše, dostane místo nové ID a ve `zmeny.json` se objeví jako odebrané a přidané. Týká se to řádově desítek míst z celého katalogu a spolehlivěji to nejde, dokud MPSV zařízením vlastní identifikátor nedá.

**U těchto míst může být celé `adresa` rovno `null`** — ne prázdný objekt, ale `null`. Registr u nich neuvádí ani ulici a obec, takže není co vypsat. Aktuálně je takových míst 36 z 39 bez RÚIAN kódu; zbylá 3 adresní text mají, jen k němu chybí kód (např. `misto-bezadresy-316-9d95f40b`, Žižkova, Příbram). **Ošetřete to při čtení**, `misto.adresa.obec` na těchto záznamech spadne. Místo samo je platné a má název i kontakt, jen bez adresy se nedá umístit na mapu ani filtrovat podle území. Od doplnění zatřídění v 1.3.0 má kategorii všech 36 — do 1.2.0 jich pět zůstávalo bez kategorie, protože šlo o poradenství a aktivizační služby, které mapovací tabulka tehdy nepokrývala.

**Slučování napříč zdroji je vždy podle adresy, ne podle poskytovatele.** Pokud ÚZIS záznam sdílí `kodAdresnihoMista` s existujícím MPSV místem, stane se další položkou v jeho `sluzby[]`, i když jde o jiného poskytovatele (typicky nemocnice a zdravotní úsek v budově domova pro seniory). Rozlišujte proto zdroj podle `sluzby[].zdroj`, ne podle tvaru ID — z ID to poznat nejde a záměrně nemá.

**Jedno místo je jeden adresní bod, i když areál má bodů víc.** Registry evidují adresní body nezávisle a rozlehlejší areál jich má běžně několik: tentýž komplex může mít v MPSV jiný `kodAdresnihoMista` než v ÚZIS a i uvnitř jednoho registru má dům se dvěma vchody dva body. Slučování je nespojí, takže v katalogu zůstanou dvě místa se stejným IČO pár desítek metrů od sebe. **19 takových dvojic vzniká mezi registry** (jedno místo jen z ÚZIS, druhé se sociální službou téhož poskytovatele, 10 až 95 m — např. `misto-14264633` a `misto-72537001`, Charita Šumperk, 25 m) a **dalších 140 uvnitř jednoho zdroje**. Ty druhé ale z velké části oddělené být mají, jde o sousední budovy jedné organizace, ne o jeden areál. Rozlišit to za vás nemůžeme — registry vazbu „tyto body patří k sobě“ nevedou a dopočítávat ji ze vzdálenosti by znamenalo vymýšlet data. Pokud vám blízké piny vadí, shlukněte si je na frontendu podle shody `sluzby[].poskytovatel.ico` a vzdálenosti; kde je hranice, je pak vaše rozhodnutí.

Souřadnice chybí u části míst ze dvou různých důvodů. **Kód adresního místa je vyplněný, ale aktuální snapshot RÚIAN ho nezná** (2,4 % míst) — RÚIAN se aktualizuje měsíčně a adresní bod mezitím mohl vzniknout nebo být přečíslován. `misto.id` je v tomto případě normální `misto-<kód>` a je stabilní, `null` jsou jen souřadnice; s dalším měsíčním během RÚIAN se část z nich doplní. Druhá skupina jsou místa **bez kódu adresního místa vůbec** (tvary ID z tabulky výše), tam se souřadnice dohledat nemá z čeho a stav se sám nezlepší. V obou případech je `souradnice.lat/lng` rovno `null`, viz sekce Souřadnice níže.

## Jedna registrace je v `sluzby[]` právě jednou (`zarizeni`)

**`sluzby[].id` je unikátní v rámci jednoho místa, ne v rámci celého katalogu.** Uvnitř jednoho `misto` se žádné `sluzby[].id` neopakuje, takže se dá bezpečně použít jako klíč seznamu při vykreslení jednoho místa.

**Globální klíč je až dvojice `(misto.id, sluzby[].id)`.** Terénní služba je registrovaná jednou, ale poskytuje se z několika adres, takže totéž `sluzby[].id` je u několika míst. Změřeno na aktuálním výstupu: 410 identifikátorů služby se opakuje napříč místy, nejčastější u 15 míst (`mpsv-6831`, `mpsv-6832`, `mpsv-7052`). Kdo si služby indexuje jen podle `sluzby[].id`, přepíše si tím záznamy navzájem a zbude mu jedna adresa místo patnácti.

Není to samozřejmé, protože MPSV vede pod jednou registrací seznam zařízení a jedna registrace může mít na jedné adrese víc zařízení — typicky pečovatelská služba a její středisko osobní hygieny v témže domě, nebo dvě nadzemní podlaží jedné budovy. Do verze 1.0.0 se taková registrace objevila v `sluzby[]` vícekrát se stejným `id`.

Od 1.1.0 je registrace v poli jednou a názvy zařízení nese nepovinné pole `zarizeni`:

```json
{
  "id": "mpsv-2627",
  "zdroj": "MPSV",
  "nazev": "Pečovatelská služba",
  "zarizeni": ["Pečovatelská služba", "Středisko osobní hygieny"],
  "formy": [
    {"forma": "ter", "kapacitaRegistrovana": [{"typ": "klient", "typNazev": "Počet klientů", "pocet": 62}]},
    {"forma": "amb", "kapacitaRegistrovana": [{"typ": "klient", "typNazev": "Počet klientů", "pocet": 20}]}
  ]
}
```

Pravidla, na která se můžete spolehnout:

- `zarizeni` je **jen u `zdroj: "MPSV"`** a **jen tam, kde má registrace na daném místě víc než jedno zařízení**. Jinak pole chybí úplně a název je v `nazev`. Čtěte tedy `sluzby[].zarizeni ?? [sluzby[].nazev]`.
- Když je pole přítomné, `nazev` je vždy jeho první prvek. Žádný název se cestou neztrácí.
- Sloučení se dnes týká 13 položek ve 12 místech, ale spoléhejte na pravidlo, ne na to číslo. U 11 z nich se názvy zařízení liší, takže je `zarizeni` vidět; u zbylých dvou byly názvy shodné, takže pole nevznikne.

**Proč to bylo potřeba: kapacita je v MPSV registrovaná na službu, ne na zařízení.** Dokud byla registrace v poli dvakrát, byla dvakrát i její kapacita. U Domova Chrudim (`misto-27763331`) jsou registrace tři — 20, 5 a 95 lůžek, dohromady 120 — ale ta poslední byla v poli dvakrát, jednou za 2. a jednou za 3. nadzemní podlaží, takže součet přes `sluzby[]` dával 215. Teď se sčítat dá.

Poslední věc k názvům v `zarizeni`: u čtyř zařízení uvádí MPSV název jednoho města a adresní kód jiného (např. „Ledax o.p.s. středisko Prachatice“ s adresním bodem v Týně nad Vltavou). Místo umisťujeme podle kódu, tedy správně; nesprávný je název. Opravit ho nemůžeme, dohledat správné přiřazení není z čeho — proto ho vypisujeme tak, jak ho registr vede. Když název zařízení zobrazujete, počítejte s tím, že nemusí odpovídat obci v `adresa`.

## Kategorie (`kategorie`)

Pole hodnot z `domovy`, `terenni`, `bezpeci`, `zdravi`, `poradenstvi`, odpovídá záložkám na webu. Jedno místo může mít víc kategorií zároveň, pokud tam sídlí služby z různých kategorií.

**`poradenstvi` přibylo ve verzi 1.3.0**, spolu s doplněním zatřídění u dalších šesti druhů sociálních služeb. Kdo výčet hodnot validuje nebo podle něj větví, musí pátou hodnotu přidat — jinak mu 374 míst spadne do neznámé kategorie. Naplňuje ji odborné sociální poradenství (`DruhSocialniSluzby/1`), tedy služba, která sama péči neposkytuje, ale je obvykle prvním krokem rodiny, která péči shání. Ze 374 míst je 217 jen v této kategorii, zbylých 157 má vedle poradenství i jinou službu. Touž změnou se rozšířily i dvě stávající kategorie: `terenni` o sociálně aktivizační služby pro seniory, sociální rehabilitaci, centra denních služeb a průvodcovské a předčitatelské služby (1 280 → 1 381 míst), `bezpeci` o telefonickou krizovou pomoc a krizovou pomoc (24 → 35 míst). Žádné místo o kategorii nepřišlo, jen přibývaly.

**Důležité:** pole může být prázdné (`[]`). Nejde o chybu, ale o službu, jejíž druh mapovací tabulka nezařazuje do žádné záložky. Po doplnění zatřídění v 1.3.0 jsou taková místa už jen 3: `misto-13000209` (domov pro osoby se zdravotním postižením) a `misto-25253867` a `misto-3250377` (sociálně terapeutické dílny). Zdravotní péče ze zdroje ÚZIS je zařazená vždy — nezařazené jsou výhradně sociální služby z MPSV. Tato místa jsou ve výstupu, aby se informace neztratila, ale nezobrazí se v žádné záložce. **Prázdné pole ošetřete i tak**, počet se mění s tím, jak registr přibírá nové druhy služeb u seniorské cílové skupiny.

**V záložce Domovy nejsou jen domovy pro seniory.** Rozhoduje forma poskytování, ne druh služby, takže pobytová odlehčovací služba patří do Domovů stejně jako domov pro seniory — je to pobytová služba s lůžky, jen na dobu určitou. Změřeno na aktuálním výstupu: z 810 míst v Domovech je **122 tam výhradně kvůli pobytové odlehčovací službě**, tedy bez domova pro seniory, domova se zvláštním režimem, týdenního stacionáře nebo chráněného bydlení na téže adrese. Registrovanou kapacitu má všech 122 (121 v lůžkách, dohromady 1 824 lůžek v rozmezí 1 až 54 na místo; `misto-9164898` má kapacitu registrovanou v klientech, ne v lůžkách). 87 z nich je zároveň v Terénních službách, protože táž organizace na téže adrese provozuje i terénní službu. Pokud budete chtít na webu odlišit trvalé bydlení od pobytu na přechodnou dobu, poznáte to podle `sluzby[].druhSluzby.kod` — `DruhSocialniSluzby/8` jsou odlehčovací služby. Filtrovat je ven z Domovů ale nedoporučujeme, uživatel hledající úlevu pro pečujícího je hledá právě tam.

## `poskytujeZdravotniPeci`

Příznak, že na tomto místě funguje i zdravotní péče uvnitř sociálního zařízení (typicky ošetřovatelský úsek domova pro seniory, evidovaný v registru ÚZIS zvlášť). **Není to samostatný záznam** — informace se připojuje k existujícímu místu, ne jako duplicitní položka v `sluzby[]`. V ukázkových datech viz `misto-79121519`.

Nejde o zařízení, kam se dá jít, ale o zdravotnickou licenci, kterou musí mít domov, aby směl zaměstnávat sestry. Proto z ní **nikdy nevzniká místo ani položka v `sluzby[]`** — buď se připojí jako tento příznak k domovu, nebo, když domov v katalogu není (jeho zřizovatel neposkytuje seniorskou sociální službu, typicky domovy pro osoby se zdravotním postižením), do výstupu nejde vůbec. Důsledek pro vás: v záložce Zdraví jsou jen služby, které si klient může sám vybrat — hospice, LDN, domácí péče, nemocnice následné péče a rehabilitační ústavy — ne ošetřovatelské úseky domovů, které by tam jinak tvořily druhý pin pár desítek metrů od domova samotného.

**Záměrně a trvale se nepromítá do `kategorie[]`.** `poskytujeZdravotniPeci: true` nikdy automaticky nepřidává `zdravi` do kategorií místa. Jde o interní ošetřovatelský úsek konkrétního domova, ne o samostatně vyhledávanou zdravotní službu typu hospic/LDN/domácí péče — proto zůstává jen jako doplňkový příznak (např. badge na kartě domova), místo se dál řadí jen podle svých vlastních služeb. Pokud budete chtít filtrovat i podle tohoto příznaku, udělejte to na frontendu nad `poskytujeZdravotniPeci`, ne přes `kategorie`.

## Souřadnice (`souradnice`)

Vždy objekt `{"lat": ..., "lng": ...}`, nikdy vynechané pole. `lat`/`lng` jsou `null`, když se souřadnice nepodařilo určit — v ukázce viz `misto-bezadresy-4674-f7e6ac50` (místo bez kódu adresního místa) a `misto-80030152` (kód je vyplněný, jen ho snapshot RÚIAN nezná). Souřadnice jsou vždy WGS84 (běžný formát pro mapy, GPS), i u zdrojů, které interně používají jiný systém. Schéma je navíc omezuje na obalový obdélník ČR (`lat` 48–52, `lng` 12–19), takže bod mimo ČR neprojde validací a nikdy se nepublikuje.

## Formy a kapacita (`formy`, `kapacitaRegistrovana`)

`sluzby[].formy` je pole, jedna položka za každou formu poskytování (`amb`/`pob`/`ter`), a **kapacita je vždy uvnitř konkrétní formy**, ne jedno společné pole za celou službu — služba může mít víc forem zároveň (typicky odlehčovací služby pobytové i ambulantní) a jejich kapacity se nesčítají ani jinak neslučují, jde o oddělené kapacity oddělených provozů. Např.:

```json
"formy": [
  {"forma": "pob", "kapacitaRegistrovana": [{"typ": "luzka", "typNazev": "Počet lůžek", "pocet": 24}]},
  {"forma": "ter", "kapacitaRegistrovana": [{"typ": "klient", "typNazev": "Počet klientů", "pocet": 1}]}
]
```

Kapacita je registrovaná **na službu, ne na zařízení**. Každá registrace je v `sluzby[]` právě jednou (viz sekce výše), takže součet kapacit přes `sluzby[]` jednoho místa je správný a nic se v něm nezapočítá dvakrát.

**Přes víc míst se ale kapacity sčítat nesmějí bez odečtení duplicit.** Táž registrace je u všech svých adresních bodů se stejnou kapacitou, protože MPSV kapacitu vede na registraci a neuvádí, kolik z ní připadá na kterou adresu. Změřeno na aktuálním výstupu: 410 z 2 217 MPSV registrací je na víc místech (maximum 15), a naivní součet přes všechna místa napočítá 54 600 lůžek proti skutečným 44 527, tedy o 23 % víc; u typu `klient` je to 101 430 proti 39 226, tedy o 159 % víc. Příklad: `mpsv-922` (Podkrušnohorské domovy, 137 lůžek) je u 4 míst, `mpsv-1572` (odlehčovací služby, Poděbrady — 24 lůžek na formě `pob`, 8 klientů na formě `ter`) u 8. **Před jakýmkoli součtem za okres, kraj nebo celý katalog proto nejdřív deduplikujte podle `sluzby[].id`.** Rozpočítat kapacitu mezi adresní body nelze, ten údaj registr neobsahuje.

**`kapacitaRegistrovana` je registrovaná maximální kapacita, ne aktuální volná místa.** Registr volná místa neobsahuje. Pole `typ` nabývá hodnot `klient`, `kontakt`, `interv`, `luzka`, `hovor` (počet klientů / kontaktů 10min. jednání / intervencí 30min. jednání / lůžek / hovorů) — jednotku vždy zobrazujte podle `typNazev`, ať nevznikne třeba "32 lůžek" u pečovatelské služby, která lůžka nemá.

## Adresa u zdroje ÚZIS: `cisloOrientacni` může obsahovat obojí

U `zdroj: "MPSV"` jsou `cisloDomovni` a `cisloOrientacni` dvě oddělená pole tak, jak je má MPSV. ÚZIS ale popisné a orientační číslo eviduje v jednom sloupci (typicky ve tvaru `"2063/46"`) — u míst ze zdroje ÚZIS je tedy `cisloDomovni` vždy `null` a celá hodnota (i s lomítkem) je v `cisloOrientacni`. Není to chyba zpracování, je to formát zdrojových dat ÚZIS. Při zobrazení adresy u ÚZIS míst tedy nezkoušejte `cisloDomovni`/`cisloOrientacni` skládat jako u MPSV, vypište `cisloOrientacni` tak, jak je.

## Kódy obce, okresu a kraje (`kodObce`, `kodOkresu`, `kodKraje`)

Vedle textového názvu je u obce, okresu a kraje k dispozici i oficiální kód pro jednoznačné rozlišení (např. "Kraj Vysočina" vs. "Vysočina", nebo shodné názvy obcí v různých krajích): `kodObce` je kód obce ČSÚ/RÚIAN a v JSONu je to **řetězec**, ne číslo (např. `"554782"` pro Prahu), `kodOkresu` je kód LAU 1 (např. `CZ0100` pro Prahu, `CZ020A` pro Prahu-západ), `kodKraje` je kód NUTS 3 (např. `CZ010` pro Prahu). `kodOkresu`/`kodKraje` mají stejný formát u obou zdrojů (MPSV i ÚZIS mají tento kód přímo v datech). U míst čistě ze zdroje ÚZIS `kodObce` v samotných ÚZIS datech chybí (jen textový název), proto se dohledává přes RÚIAN (stejný zdroj jako souřadnice, přes `ZZ_RUIAN_kod`) — pokrytí 99,7 %, tedy 649 ze 651 míst čistě ze zdroje ÚZIS. `kodObce` je `null` jen výjimečně, u míst bez dohledaného RÚIAN bodu: ze 2 871 míst s vyplněnou adresou jsou to 2 (`misto-uzis-bezadresy-259989` a `misto-22498818`). Jsou to zároveň místa bez souřadnic — obojí má tutéž příčinu — ale opačně to neplatí. Ze 109 míst bez souřadnic jich 36 nemá adresu vůbec (a tedy ani pole `kodObce`), 71 má `kodObce` vyplněné a jen tato 2 ho mají `null`.

**`okres` a `kodOkresu` jsou `null` u 229 míst, tedy 7,9 %.** Nejde o mezeru ve zpracování, ale o to, že okres u nich neexistuje: 191 z nich jsou pražská místa se sociální službou (Praha je zároveň kraj i obec, MPSV u nich okres nevede), 36 jsou místa bez adresy vůbec a zbylá 2 jsou místa z MPSV bez kódu adresního místa, u kterých registr vede jen ulici, číslo popisné a obec. **Filtr podle okresu proto vždy ošetřete na `null`**, jinak vám vypadne celá Praha.

`kraj` a `kodKraje` jsou vyplněné skoro všude, kde je vyplněná `adresa`, ale **ne vždy** — u 2 míst jsou `null` a jsou to právě ta dvě z předchozího odstavce (`misto-bezadresy-316-9d95f40b`, Žižkova, Příbram, a `misto-bezadresy-714-43443061`, Pražská, Bystřany). Filtr podle kraje tedy ošetřete na `null` také.

**Filtrujte a seskupujte podle kódu, ne podle názvu obce.** Textový název přebíráme z registru, ze kterého místo pochází, a oba registry ho pro Prahu píší jinak: místa se sociální službou mají `obec: "Praha"` (191 míst), místa jen ze zdroje ÚZIS mají městskou část, tedy `"Praha 1"` až `"Praha 16"` (85 míst). Filtr na `obec == "Praha"` by vám tedy 85 pražských míst zahodil. `kodObce` je přitom u 275 z těch 276 míst shodně `"554782"` (u jednoho se RÚIAN bod nedohledal, viz výše), takže při filtrování podle kódu problém nevzniká. Totéž platí obecně — název je pro zobrazení, kód pro logiku.

## IČO

Vždy 8 znaků, jen číslice, jako text (`"03017621"` je platné IČO se sedmi platnými číslicemi a úvodní nulou — nikdy nepřevádět na číslo).

## Kontakty

`kontakt.weby/emaily/telefony` jsou vždy pole (i prázdné), nikdy jedna hodnota. Pravidlo: nejdřív kontakt konkrétní služby, a když ho registr nemá, kontakt poskytovatele jako celku — obojí je v `mista.sluzby[].kontakt` už sloučené, žádné další rozlišování není potřeba.

**Služba může mít všechna tři pole prázdná.** Ve výstupu je takových služeb 12 a všechny jsou ze zdroje ÚZIS — pobytová zařízení, u kterých registr kontakt nevede, ale název a adresa stačí k tomu, aby se dala najít. U sociálních služeb z MPSV to nenastává, tam má kontakt každá. Vyřazení kvůli chybějícímu kontaktu se týká **výhradně jediného druhu ze zdroje ÚZIS — domácí zdravotní péče**: k té se jinak než telefonem nedovoláte, takže záznam bez kontaktu by byl k ničemu. U ostatních druhů ÚZIS (hospic, LDN, nemocnice následné péče, rehabilitační ústav) záznam bez kontaktu zůstává, protože se dá najít podle názvu a adresy. **Počítejte tedy s prázdným `kontakt`, ale jen u pobytových míst.**

## Zdroj (`zdroj`)

`MPSV` (sociální služby, id začíná `mpsv-`) nebo `UZIS` (zdravotní služby, id začíná `uzis-`). Pole `formy` dává smysl jen u `MPSV` (u ÚZIS chybí úplně, ne prázdné pole). Pole `oborPece` a `oboryPece` jen u `UZIS`.

## Obor péče (`oborPece`, `oboryPece`)

**Používejte `oboryPece`.** Zdrojové pole ÚZIS je vícehodnotové, obory jsou v jedné buňce oddělené čárkou. `oboryPece` je pole se všemi obory v pořadí registru, `oborPece` je jen jeho první prvek. **Když registr obor neuvádí, je `oboryPece` prázdné pole a `oborPece` je `null`** — nastává to u 73 z 930 ÚZIS služeb, takže s tím počítejte.

`oborPece` existovalo dřív než `oboryPece` a zůstává kvůli kompatibilitě se schématem 1.0.0. Kdo podle něj filtruje, přijde o obory na dalších pozicích: ze 930 publikovaných ÚZIS služeb jich 242 uvádí oborů víc, maximum na jedné službě je 32. Konkrétně u 20 služeb není v `oborPece` vidět „paliativní medicína", protože ji registr neuvádí jako první — mezi nimi Hospicová péče sv. Kleofáše a PAHOP. Pro rozpoznání hospicové a paliativní péče je proto `oboryPece` jediné použitelné pole.

## Datum poskytování (`datumPoskytovaniOd`, `datumPoskytovaniDo`)

Jen u `MPSV`. `datumPoskytovaniOd` je vyplněné u všech položek. `datumPoskytovaniDo` je u služby, která má v registru evidované ukončení, jinak `null`.

**Ve výstupu je `datumPoskytovaniDo` vždy buď `null`, nebo v budoucnosti, nikdy v minulosti ani dnešní.** Ukončené registrace se do katalogu nedostanou: z 2 606 seniorských služeb má 389 datum ukončení vyplněné a 381 z nich k dnešku nebo dřív, do výstupu nejde ani jedna. Zůstává 8 služeb s ohlášeným ukončením k budoucímu datu, které se ve výstupu objeví jako 13 položek (jedna registrace může být na víc adresních bodech), tedy 0,3 %. Příjemce tak nemusí datum sám vyhodnocovat — co je v katalogu, to se poskytuje.

## `meta.json`

Ukázka odpovídá stavu publikovanému k 11. 9. 2026; aktuální hodnoty vždy v `data/meta.json`.

```json
{
  "verzeSchematu": "1.3.0",
  "hashKatalogu": "945e1e82…",
  "pocetMist": 2907,
  "pocetSluzeb": 4003,
  "pocetMistPodleKategorie": {"bezpeci": 35, "domovy": 810, "poradenstvi": 374, "terenni": 1381, "zdravi": 890},
  "pocetMistBezKategorie": 3,
  "pocetMistSPoskytovanimZdravotniPece": 429,
  "pocetMistBezSouradnic": 109,
  "datumZdrojovychDat": {"mpsv": "2026-09-10", "uzis": "2026-09-01", "ruian": "2026-08-31"}
}
```

**`hashKatalogu` je SHA-256 obsahu `katalog.json`** (hex, malá písmena), počítaný nad souborem tak, jak se zapisuje — UTF-8, `indent=2`, bez escapování diakritiky. Je to jediný spolehlivý indikátor toho, že se data změnila: stáhněte `meta.json` (pár set bajtů), porovnejte hash s tím, který máte, a `katalog.json` tahejte, jen když se liší.

`pocetMistPodleKategorie` **se nesečte na `pocetMist`** — jedno místo může být ve víc kategoriích zároveň a 3 místa nemají kategorii žádnou. Klíče tohoto objektu se odvozují z mapovací tabulky, takže **s přibytím kategorie přibude i klíč**; čtěte ho jako slovník, ne jako pevnou pětici. Od 1.3.0 jsou klíče seřazené abecedně.

`pocetMistBezSouradnic` je počet míst, kde je `souradnice.lat` i `lng` rovno `null`. Slouží k provozní kontrole na naší straně (viz Provoz níže) a příjemci dává čitelný podíl míst, která nejde vykreslit na mapu — dlouhodobě kolem 110 z 2 900, tedy necelá 4 %.

`datumZdrojovychDat` jsou **tři samostatná data**, jedno za každý registr, protože se každý aktualizuje jinak často (MPSV denně, ÚZIS a RÚIAN měsíčně). Není to jedno datum běhu, viz Provoz níže.

## `zmeny.json` a zaniklé záznamy

Formát:
```json
{
  "verzeSchematu": "1.3.0",
  "pridano": ["misto-123456"],
  "zmeneno": ["misto-234567"],
  "odebrano": ["misto-345678"]
}
```
Zaniklé místo je **explicitně** v `odebrano`, nikdy se nemá odvozovat z toho, že v novém `katalog.json` chybí. Pokud se od posledního běhu nic nezměnilo, `zmeny.json` se nepřepisuje — zůstává poslední platná verze, nikdy nedostanete prázdný seznam změn, který byste museli rozlišovat od chyby.

Jak se tři seznamy určují: porovnává se nový a poslední publikovaný `katalog.json` podle `misto.id`. `pridano` je ID, které přibylo, `odebrano` ID, které zmizelo, a **`zmeneno` je ID přítomné v obou verzích, u kterého se liší cokoli v celém objektu místa** — kontakt, kapacita, jedna služba navíc i změna souřadnic. Seznam tedy neříká, *co* se změnilo, jen *že* se to změnilo; rozdíl si musíte dopočítat sami, nebo prostě přepsat celé místo. Všechny tři seznamy — `pridano`, `zmeneno` i `odebrano` — jsou seřazené podle ID, ne podle času změny.

**Nespoléhejte se na pořadí prvků v `mista[]` ani v `sluzby[]`.** Kopíruje pořadí záznamů ve zdrojových registrech a není nijak garantované — párujte vždy podle `id`, tak jak to dělá i `zmeny.json`. Kdyby některý registr vyexportoval tatáž data v jiném pořadí, dostanete `katalog.json` s jinak seřazenými prvky, ale `zmeny.json` u něj bude hlásit nulové změny. To je korektní stav, ne chyba: obsah je stejný, jen přeskupený.

## Verzování

`verzeSchematu` je sémantické verzování (`MAJOR.MINOR.PATCH`). Nekompatibilní změna (přejmenování/odebrání pole, změna typu) zvedne MAJOR verzi a bude ohlášena dopředu, nikdy tichým přepsáním produkčních dat.

**Rozšíření výčtu hodnot je hraniční případ a hlásíme ho taky.** Přidání hodnoty do `kategorie[]` (1.3.0) žádné pole neodebírá ani nemění typ, takže je to MINOR změna — ale čtenáři, který výčet validuje nebo na něm má `switch` bez větve `default`, ji rozbít může. Dokud web nejede, je to levná změna; po spuštění by táž změna byla důvod k MAJOR verzi.

| Verze | Změna |
|---|---|
| 1.3.0 | Přibyla kategorie `poradenstvi`, výčet `kategorie[]` má nově pět hodnot místo čtyř. Zároveň se doplnilo zatřídění u sedmi druhů sociálních služeb, které dosud žádnou záložku nenaplňovaly, takže míst bez kategorie ubylo z 324 na 3. Žádné pole nepřibylo, nezmizelo ani nezměnilo typ, žádné místo o kategorii nepřišlo — všechny změny jsou přírůstkové. Přechodový běh označil ve `zmeny.json` 468 míst jako změněná, 6 jako odebraná a 1 jako přidané; ze 468 se u 464 liší **výhradně pole `kategorie`**, zbylé 4 a všechna přidaná i odebraná místa jsou běžný denní pohyb registru MPSV (nový snapshot z 10. 9. 2026), ne důsledek této změny. |
| 1.2.0 | Přibylo nepovinné `sluzby[].oboryPece` s úplným seznamem oborů péče. `oborPece` zůstává beze změny typu i obsahu, čtenář 1.1.0 běží dál beze změny. Ověřeno porovnáním celého výstupu: proti 1.1.0 se u žádného z 2 912 míst nezměnilo nic jiného než přibylé pole, `oborPece` se u žádné z 930 ÚZIS služeb neliší od prvního prvku `oboryPece`. Ve `zmeny.json` je 890 míst jako změněná (ta, která obsahují ÚZIS službu), 0 přidaných a 0 odebraných. |
| 1.1.0 | Přibylo nepovinné `sluzby[].zarizeni`. Registrace je nově v `sluzby[]` právě jednou, takže `sluzby[].id` je v rámci místa unikátní a kapacity se dají sčítat. Zároveň se přestaly publikovat služby s ukončenou registrací (viz Datum poskytování). Žádné pole nezmizelo ani nezměnilo typ, čtenář 1.0.0 běží dál beze změny. Přechodový běh označil ve `zmeny.json` 15 míst jako změněná a 6 jako odebraná (ty s ukončenou registrací), žádné jako přidané. U změněných míst se lišilo výhradně pole `sluzby` — `misto.id`, souřadnice, adresy, kategorie ani `poskytujeZdravotniPeci` se nezměnily u žádného místa. |
| 1.0.0 | Výchozí odsouhlasené schéma. |

## Provoz

Aktualizace je automatická jedním denním během přes GitHub Actions (`0 4 * * *` UTC). MPSV se stahuje vždy, ÚZIS a RÚIAN jen tehdy, když u zdroje vyjde nová verze — běh se na ni nejdřív levně zeptá a podle odpovědi buď stáhne, nebo použije poslední uloženou. Nová měsíční verze se tak projeví v nejbližším denním běhu po jejím vydání. Čas v plánu je nejdřívější možný start, ne závazek — GitHub naplánované běhy řadí do fronty a spuštění může nastat i o několik hodin později. Odebírejte proto podle změny `hashKatalogu`, ne podle očekávané hodiny. Vedle denního běhu existuje ještě ruční workflow bez plánu, které se spouští jen výjimečně (vynucené čerstvé stažení ÚZIS a RÚIAN) — může tedy publikovat i mimo denní rytmus.

**Commit vzniká jen tehdy, když se obsah `katalog.json` skutečně změnil.** Běh bez commitu je úspěšný běh beze změny ve zdrojích, ne chyba. Změnu poznáte podle `hashKatalogu` v `meta.json`.

**`datumZdrojovychDat` nepoužívejte k posouzení, jestli import běží.** Je to datum snapshotu, ze kterého jsou postavená *právě publikovaná* data, ne datum poslední kontroly zdroje. Celý `meta.json` se totiž přepisuje jen spolu s katalogem — když registr vydá nový soubor, ale na seniorských službách se nic nezmění, katalog i `meta.json` zůstanou beze změny a datum se neposune. Reálný příklad: 8. 9. 2026 měl `rpss.json` u MPSV datum 7. 9., ale publikované `meta.json` uvádělo 5. 9., protože poslední skutečná změna dat byla z 5. 9. Je to důsledek pravidla o commitech výše, ne zpoždění importu — kdyby se datum přepisovalo při každém běhu, vznikal by commit každý den. Že import běží, ověříte v historii běhů na GitHubu (**Actions**).

Před každou publikací běží sedm kontrol: stáří zdrojových dat (žádný snapshot starší než 50 dnů a u žádného zdroje nesmí být datum vydání jen dosazené), validace zdrojových dat proti schématu registru, kontrola, že výstup obsahuje aspoň jedno místo, kontrola na duplicitní `misto.id`, validace výstupu proti `schema/katalog.schema.json`, prahová kontrola na změnu počtu míst o víc než 5 % a prahová kontrola na nárůst počtu míst bez souřadnic o víc než 30. Když kterákoli neprojde, do `data/` se nezapíše nic a zůstane poslední platná verze — nikdy nedostanete prázdný ani useknutý soubor.
