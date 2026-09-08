# Datový výstup: registrované služby pro seniory

Zadání pro realizaci. Verze 4.1, 31. 8. 2026.

**Zásadní změna proti verzi 3.** Napojení na WordPress a frontend dělá vývojář klienta. Naše dodávka končí u datového výstupu.

Verze 4.1 zapracovává dohodu s vývojářem klienta: integraci dělá on, kategorie zatřiďujeme my.

---

## 0. Jak s tímto dokumentem pracovat

1. **Údaje v sekci 2 a 3 jsou ověřené proti reálným datům.** Nepřepisuj je podle toho, co si myslíš, že je pravda. Když se realita rozejde s dokumentem, zapiš to do sekce 8 a upozorni.
2. **Nic si nedomýšlej.** Neznáš-li název pole nebo hodnotu číselníku, ověř to v datech. Nikdy nevymýšlej hodnotu, která "dává smysl".
3. **Po každé etapě je kontrolní bod.** Neposouvej se dál, dokud neprojde.
4. **Pracuj na vzorku, dokud to jde.**

---

## 1. Co se dodává a co ne

```
zdroje MPSV / ÚZIS / ČÚZK
        |
        v
   naše zpracování a sjednocení        <- naše odpovědnost končí zde
        |
        v
   katalog.json + schéma + meta        <- rozhraní
        |
        v
   napojení do WordPressu              <- vývojář klienta
        |
        v
   zobrazení v katalogu
```

| Dodáváme | Nedodáváme |
|---|---|
| Zpracování a sjednocení dat z obou registrů | Plugin pro WordPress |
| Doplnění souřadnic z RÚIAN | Napojení na výpis, karty a vyhledávání |
| Sloučení služeb na společné adrese | Zobrazení a design |
| Zatřídění do kategorií odpovídajících záložkám webu | Stránky pro vyhledávače |
| JSON Schema a dokumentaci rozhraní | Laické popisy služeb, fotografie |
| Automatickou aktualizaci a kontroly | Správa a rozvoj po předání |
| Předání repozitáře a zaškolení | |

**Akceptační kritérium dodávky je validní výstup podle odsouhlaseného schématu, ne podoba webu.**

**Očekávaný objem:** zhruba 3 800 míst, konkrétně 2 600 sociálních služeb na 2 942 adresách plus asi 900 zdravotnických zařízení.

---

## 2. Ověřená fakta o zdrojích

Ověřeno proti reálným datům a živým stránkám mezi 27. a 31. 8. 2026.

### 2.1 Registr poskytovatelů sociálních služeb (MPSV)

```
https://data.mpsv.cz/od/soubory/rpss/rpss.json
https://data.mpsv.cz/od/soubory/rpss/rpss.schema.json
https://data.mpsv.cz/od/soubory/ciselniky/druhy-socialni-sluzby.json
https://data.mpsv.cz/od/soubory/ciselniky/cilove-skupiny-osoby.json
https://data.mpsv.cz/od/soubory/ciselniky/formy-soc-sluzby.json
```

Územní číselníky (kraje, okresy, obce, části obcí) jsou nutné, protože v datech jsou jen kódy. Jsou na stejné base URL jako ostatní číselníky pod názvy `kraje.json`, `okresy.json`, `obce.json` a `casti-obci.json`; přehled je na `https://data.mpsv.cz/web/data/ciselniky`.

- Aktualizace denně, velikost přes 30 MB, kořenový klíč `polozky`
- Podmínky užití (4. 5. 2022): žádná licenční povinnost, žádná povinná citace

**Změřené hodnoty (31. 8. 2026):**

| Metrika | Hodnota |
|---|---|
| Služeb celkem | 6 733 |
| Služeb s cílovou skupinou senioři | 2 600 |
| Zařízení celkem | 18 907 |
| Zařízení u seniorských služeb | 6 627 |
| Unikátních adres u seniorských služeb | 2 942 |
| Zařízení bez `kodAdresnihoMista` | 676 (3,58 %) |

Na jedné adrese sídlí v průměru 2,25 seniorské služby.

**Klíče první úrovně** (z reálných dat):

```
portalId, id, identifikator, datumPoskytovaniOd, datumPoskytovaniDo,
kontaktniAdresy, druhSocialniSluzby, zarizeni, poskytovatel,
emaily, telefony, faxy, weby, ciloveSkupiny, vekoveSkupiny,
doplnujiciInformaceVekoveSkupiny, formy, rozsirenePusobnostiVKraji,
doplnkoveUdaje
```

**Kontakty jsou na dvou úrovních.** Na úrovni služby `weby`, `emaily`, `telefony`, na úrovni poskytovatele totéž pod `poskytovatel`. Všechno jsou pole objektů:

```json
"weby": [{"web": "http://www.carvac.cz", "poznamka": null}]
"emaily": [{"email": "ldn@carvac.cz", "poznamka": null}]
"telefony": [{"telefon": "354525345", "poznamka": null}]
```

Pravidlo: kontakt služby, a když chybí, kontakt poskytovatele. Ve výstupu dodat obojí zvlášť, ať si druhá strana může vybrat.

**Vyplněnost u 2 600 seniorských služeb:** weby 94,2 %, emaily 99,7 %, telefony 99,9 %, bez jakéhokoli kontaktu 0.

**Adresa zařízení, reálná podoba:**

```json
{"cisloDomovni": 2272, "cisloOrientacni": "54", "dodatekAdresy": null,
 "kodAdresnihoMista": 11867906, "psc": "35201",
 "typCislaDomovniho": {"id": "TypStavebnihoObjektu/1"},
 "kraj": {"id": "Kraj/51"}, "okres": {"id": "Okres/3402"},
 "obec": {"id": "Obec/554499"}, "castObce": {"id": "CastObce/405507"},
 "mestskyObvodMestskaCast": null, "mestskyObvodVPraze": null,
 "ulice": {"nazev": "Nemocniční"}}
```

**Pole `formy` je vyplněné u všech 2 600 služeb:**

```json
[{"forma": {"id": "FormaSocialniSluzby/pob"},
  "nepretrzitePoskytovani": true, "casoveRozsahy": null,
  "kapacity": [{"pocet": 32,
                "popis": "Maximální kapacita 32 lůžek s účinností od 01.09.2016.",
                "typ": {"id": "TypKapacitySocialniSluzby/luzka"}}]}]
```

- `forma.id` rozlišuje pobytovou, ambulantní a terénní formu. **Toto je klíč pro zařazení do kategorie**, ne druh služby.
- `kapacity[].pocet` je **registrovaná maximální kapacita, ne volná místa.** Ve výstupu to pojmenuj tak, aby se to nedalo splést, například `kapacitaRegistrovana`. Volná místa registr neobsahuje.
- `kapacity[].typ` se liší podle formy, jinak vznikne "32 lůžek" u pečovatelské služby. Napříč všemi službami se vyskytuje pět hodnot `TypKapacitySocialniSluzby`: `klient`, `kontakt`, `interv`, `luzka` a `hovor` — počet klientů, kontaktů (10 min.), intervencí (30 min.), lůžek a hovorů. Předat druhé straně.
- `popis` je úřední text s datem účinnosti, do výstupu patří jen jako doplněk

**Známé hodnoty číselníků:** číselník druhů má 34 položek, `DruhSocialniSluzby/13` je "domovy pro seniory". `CilovaSkupinaOsoby/24` senioři, `/30` osoby žijící s demencí, `/26` pečující osoby, `/27` osoby s potřebou paliativní péče. Zbytek vyčti z číselníků, nehádej.

### 2.2 Národní registr poskytovatelů zdravotních služeb (ÚZIS)

```
https://datanzis.uzis.gov.cz/data/NR-01-NRPZS/NR-01-06/Otevrena-data-NR-01-06-nrpzs-mista-poskytovani-zdravotnich-sluzeb.csv
```

CSVW schéma je na stejné adrese s příponou `.csv-metadata.json`.

**REST API na `nrpzs.uzis.cz/api/doc` je mrtvé, vrací 404.** Pracuj s měsíčním CSV.

- Měsíční aktualizace, licence **CC BY 4.0, povinná citace** podle znění na stránce datové sady. Citaci předej druhé straně, musí být na webu.
- UTF-8 bez BOM, oddělovač čárka, pole v uvozovkách, CRLF
- 40 848 řádků, 49 sloupců, bez zaniklých subjektů a bez zařízení MV a MSp

**Klíčové sloupce:** `poskytovatel_ICO` (velká písmena), `ZZ_ID`, `ZZ_nazev`, `ZZ_druh_nazev`, `ZZ_obor_pece`, `ZZ_GPS`, `ZZ_RUIAN_kod`, `ZZ_kraj_nazev`, `ZZ_okres_nazev`, `ZZ_obec`, `ZZ_PSC`, `ZZ_ulice`, `poskytovatel_nazev`, `poskytovatel_web`, `poskytovatel_email`, `poskytovatel_telefon`.

**Vyplněnost:** `ZZ_GPS` chybí u 0,24 %, `ZZ_RUIAN_kod` u 0,15 %, web u 57,05 %, telefon u 45,30 %, e-mail u 38,35 %.

**Relevantní druhy zařízení:** Domácí zdravotní péče 946, Zdravotní péče v ústavech sociální p. 778, Nemocnice následné péče 55, Léčebna pro dlouhodobě nemocné (LDN) 55, Hospic 29, Rehabilitační ústav 28.

**IČO:** vždy 8 znaků, jen číslice, 12 336 řádků začíná nulou. **Číst jako text**, jinak selže párování.

### 2.3 RÚIAN (ČÚZK)

```
https://nahlizenidokn.cuzk.gov.cz/StahniAdresniMistaRUIAN.aspx
```

Soubor `RRRRMMDD_strukt_ADR.csv.zip`, celá ČR, měsíčně, CC BY 4.0. **Souřadnice jsou v S-JTSK**, převod přes `pyproj` z EPSG:5514 do EPSG:4326. Používá se jen pro záznamy z MPSV, ÚZIS má souřadnice vlastní.

**Aktualizace z etapy 3, viz sekce 8:** stránka výše je chráněná hCaptchou a nejde stáhnout automatizovaně; skutečný zdroj je atomový feed `https://atom.cuzk.gov.cz/get.ashx?theme=RUIAN-CSV-ADR-ST`, který vrací přímý odkaz na `vdp.cuzk.gov.cz`. Soubor navíc není jeden celostátní CSV, ale ZIP s jedním CSV na obec (6 258 souborů). A převod souřadnic je jinak, než tvrdí odstavec výše — ověřeno EPSG:5513, ne 5514.

---

## 3. Datové pasti

Objeveno v reálných datech, nejsou to hypotézy.

### 3.1 Souřadnice z ÚZIS mají prohozené pořadí

Formát WKT POINT, ale první je zeměpisná šířka, pak délka, tedy obráceně proti standardu.

```
POINT(48.959066276499 14.470410383763)  ->  48,959 N a 14,470 E = České Budějovice
```

Při standardním čtení padne bod do Somálska. Bounding box ČR: první číslo 48,59 až 51,02, druhé 12,17 až 18,81. **Po parsování vždy ověř.**

### 3.2 Hospice nelze filtrovat podle druhu zařízení

Druh `Hospic` má 29 záznamů, ale slovo "hospic" je v názvu u 69 řádků a obor `paliativní medicína` u 233. Domácí hospice jsou registrované jako domácí zdravotní péče. Filtr musí kombinovat druh, obor a text názvu.

### 3.3 Pole oborů je víchodnotové

`ZZ_obor_pece` má obory oddělené čárkou v jedné buňce. 1 803 unikátních řetězců, po rozpadu 170 atomických oborů. Před filtrováním rozpadnout.

### 3.4 Zdravotní péče v ústavech sociální péče vyrábí duplicity

778 řádků jsou zdravotní služby uvnitř domovů pro seniory, tedy zařízení už přítomných z MPSV. **Neposílat jako samostatné záznamy.** Ve výstupu jako příznak u existujícího místa, například `poskytujeZdravotniPeci: true`.

### 3.5 Část záznamů ÚZIS nemá žádný kontakt

Bez webu, e-mailu i telefonu je 10 311 z 40 848 (25,24 %). Domácí zdravotní péče 185 z 946 (19,56 %), hospic 1 z 29, LDN 6 z 55, nemocnice následné péče 3 z 55.

**Pravidlo:** u domácí zdravotní péče zařadit jen záznamy s alespoň jedním kontaktem. U pobytových zařízení zařadit i bez kontaktu, stačí název a adresa. **Týká se výhradně dat z ÚZIS**, v MPSV není bez kontaktu ani jedna seniorská služba.

### 3.6 Osobní údaje

**Do výstupu nikdy nezařazovat:**

- ÚZIS: `poskytovatel_odborny_zastupce`
- MPSV: `poskytovatel.statutarniOrgany[]` (obsahuje `jmeno`, `prijmeni`, tituly, ověřeno v datech)
- MPSV: jména vedoucích u `zarizeni`

### 3.7 V datech jsou URL, které nejsou weby poskytovatelů

`doplnkoveUdaje.realizacePoskytovani[].priloha.url`, `doplnkoveUdaje.planyFinancnihoZajisteni[].priloha.url` a `doplnkoveUdaje.personalniZajisteni[].priloha.url` odkazují na dokumenty na `mpsv.cz/agportal-server/rest/documents/...`.

**Nikdy nehledej kontakty textovým prohledáváním záznamu.** Hledání "http" kdekoli v záznamu vrací falešně vysoká čísla. Čti konkrétní klíče.

---

## 4. Rozhraní

### 4.1 Výstupní soubory

Statické soubory v repozitáři, publikované po každém úspěšném běhu. **Ne API endpoint, ne databáze.** Statický soubor nemá výpadky, cachuje se, verzuje se sám.

| Soubor | Obsah |
|---|---|
| `katalog.json` | kompletní data |
| `katalog.schema.json` | JSON Schema pro validaci na straně příjemce |
| `meta.json` | verze schématu, hash obsahu, počty záznamů, datum zdrojových dat. **Bez času běhu importu**, viz 5.3 |
| `zmeny.json` | ID přidaných, změněných a odebraných od posledního běhu |

### 4.2 Kontrakt, který musí výstup splnit

- **Stabilní identifikátory.** Základní jednotkou je **místo, ne registrace.** ID odvozené od kódu adresního místa RÚIAN, neměnné mezi běhy.
- **Explicitní tombstones.** Zaniklé záznamy ve `zmeny.json` jako odebrané, ne aby se mazání dedukovalo z nepřítomnosti.
- **IČO u každého záznamu**, aby druhá strana mohla párovat své partnerské záznamy.
- **Souřadnice ve WGS84** všude, kde jdou určit. Kde nejdou, explicitně `null`, ne vynechané pole.
- **Nikdy nepublikovat prázdný nebo nevalidní výstup.** Když se zdroj pokazí, běh se zastaví, zůstane poslední platná verze, odejde upozornění. Druhá strana se nemusí bránit proti nesmyslným datům.
- **Verzování schématu.** Nekompatibilní změnu ohlásit dopředu, nikdy tichým přepsáním.

### 4.3 Kategorie

Ve výstupu je pole s kategorií odpovídající záložkám na webu. Přiřazení děláme my, protože známe sémantiku registrů. Zobrazení je jejich.

| Kategorie | Naplní |
|---|---|
| Domovy | domovy pro seniory, domovy se zvláštním režimem, týdenní stacionáře, chráněné bydlení |
| Terénní služby | pečovatelská služba, osobní asistence, odlehčovací služby, denní stacionáře, terénní programy |
| Bezpečí | tísňová péče |
| Zdraví | hospice, domácí zdravotní péče, LDN, nemocnice následné péče, rehabilitační ústavy |
| Mobilita | nic, registry ji nepokrývají, zůstává partnerská |

Mapovací tabulka patří do konfiguračního souboru, ne do kódu. **Rozdělení Domovy versus Terénní služby rozhoduj podle `formy`, ne podle druhu služby**, odlehčovací služby existují v obou formách.

Jedno místo může mít víc kategorií zároveň. Ve výstupu tedy pole kategorií, ne jedna hodnota.

### 4.4 Předávání dat

Repozitář vede jen data, s repozitářem webu nemá nic společného.

```
/import/            Python skript
/config/            mapování kategorií, konfigurace
/data/              katalog.json, meta.json, zmeny.json
/schema/            katalog.schema.json
/.github/workflows/ import.yml, import-mesicni.yml
```

Odběr dat:

**Veřejný repozitář, přímý odkaz na `raw.githubusercontent.com`.** Nejjednodušší, doporučená varianta. Data jsou beztak veřejná otevřená data.

---

## 5. Automatizace

### 5.1 Běhy

- MPSV denně
- ÚZIS a RÚIAN měsíčně, samostatné workflow
- Obojí i ručně přes `workflow_dispatch`

### 5.2 Pojistky

Nejhorší scénář není pád skriptu, ten je vidět. Nejhorší je běh, který "úspěšně" zapíše prázdný nebo useknutý soubor.

1. Validace zdroje proti `rpss.schema.json` při každém běhu
2. Validace vlastního výstupu proti `katalog.schema.json` před zápisem
3. Prahová kontrola: změna počtu záznamů o víc než 5 % proti poslednímu dobrému běhu znamená nepublikovat a upozornit
4. Když kontrola neprojde, **commit se neprovede** a v repozitáři zůstane poslední platná verze

### 5.3 Commitovat jen změny, ne každý běh

Import běží denně, ale data se každý den nemění. Kdyby workflow commitoval po každém běhu, vznikne za rok přes 300 commitů, z nichž většina nemění nic. Historie se tím zaplevelí, repozitář zbytečně roste a `zmeny.json` ztratí smysl, protože bude většinou prázdný.

**Pravidlo:** commit se provede jen tehdy, když se obsah `katalog.json` skutečně liší od poslední publikované verze. Jinak workflow doběhne, nic nezapíše a skončí úspěchem. Že proběhl, je vidět v historii běhů na GitHubu, k tomu není potřeba commit.

Porovnávat obsahem, tedy hashem vygenerovaného souboru, ne datem. Nespoléhej na `git diff` po zápisu, soubor se nemá ani přepsat, když je shodný.

**Důsledek pro `meta.json`, na který se snadno zapomene.** Kdyby `meta.json` obsahoval čas posledního běhu, měnil by se při každém spuštění a vynutil by si commit i ve dnech, kdy se data nezměnila. Tím by celé pravidlo přestalo fungovat.

`meta.json` proto smí obsahovat jen údaje odvozené od dat: verzi schématu, hash obsahu, počty záznamů podle kategorií a datum zdrojových dat z registru. **Nikdy čas běhu importu.** Druhá strana pozná, že se něco změnilo, podle hashe, a kdy naposledy import proběhl, je vidět v historii běhů.

Stejné pravidlo platí pro `zmeny.json`. Když se nic nezměnilo, nezapisuje se nová verze, zůstává ta poslední. Druhá strana tak nikdy nedostane prázdný seznam změn, který by musela rozlišovat od chyby.

### 5.4 Provozní fakta o GitHub Actions

- Veřejné repozitáře: neomezené minuty. Privátní na Free: 2 000 minut měsíčně, pak 0,006 USD za minutu, ale výchozí limit útraty je nula, takže se úlohy zastaví a nic se nenaúčtuje.
- Denní běh v řádu minut se vejde s rezervou.
- **Pravidlo 60 dnů:** GitHub vypne naplánované workflow v repozitáři bez aktivity. Nás se to nedotkne, protože import commituje data. Po nasazení ověřit.
- Naplánované běhy nemají garantovaný čas, zpoždění 5 až 30 minut je běžné. Neslibovat hodinu.
- **Notifikace o selhání** chodí u naplánovaných úloh jen tomu, kdo workflow vytvořil. **Když se workflow vypne a znovu zapne, chodí tomu, kdo ho zapnul**, to je zvolený mechanismus předání. Příjemce musí mít v Settings, Notifications, System, Actions přepnuto na Email, výchozí stav je "Don't notify". Selhání před spuštěním workflow notifikaci nevyvolají, toto riziko zůstává nepokryté a klient o něm ví.

---

## 6. Etapy

### Etapa 0. Dohoda o rozhraní

**Stav k 31. 8. 2026, dohodnuto s vývojářem klienta:**

- Integraci na web dělá vývojář klienta, naše dodávka končí u datového výstupu
- Formát výstupu: statické JSON soubory v GitHub repozitáři
- **Zatřídění do kategorií děláme my**, ne druhá strana. Důvod, který byl komunikován: rozdělení mezi Domovy a Terénní služby se řídí formou poskytování, ne druhem služby.

### Etapa 1. Prototyp na vzorku

1. Stažení `rpss.json` s obnovením přerušeného přenosu a kompresí
2. Validace proti `rpss.schema.json`
3. Číselníky včetně územních
4. Filtr na `CilovaSkupinaOsoby/24`
5. **Práce na vzorku 200 služeb**, ne na plných datech
6. Rozpad na zařízení, seskupení podle `kodAdresnihoMista`

**Kontrolní bod:** ručně zkontroluj 10 náhodných záznamů proti webu poskytovatele. Sedí název, adresa, kontakt? Objevila se adresa dvakrát? Teprve pak plná data.

### Etapa 1b. Odsouhlasení schématu

Podle odsouhlaseného schématu staví druhá strana integraci, proto se ladí na začátku, ne na konci.

1. Napiš `katalog.schema.json`
2. Vygeneruj ukázkový `katalog.json` s 30 až 50 skutečnými záznamy pokrývajícími okrajové případy: místo s několika službami, služba bez webu, záznam jen z ÚZIS, poskytovatel s více pobočkami, tísňová péče, záznam bez souřadnic
3. Napiš stručnou dokumentaci rozhraní: co které pole znamená, jak se pracuje se `zmeny.json`, jak poznat zaniklý záznam, že kapacita je registrovaná a ne volná
4. Pošli vývojáři a nech odsouhlasit

**Kontrolní bod:** vývojář odsouhlasí schéma. Teprve pak pokračuj.

### Etapa 2. ÚZIS a párování

1. Načtení CSV, IČO jako text
2. Filtr druhů podle 2.2, hospice podle 3.2
3. Parsování `ZZ_GPS` s ověřením pořadí (3.1)
4. Vyřazení domácí péče bez kontaktu (3.5)
5. Druh "Zdravotní péče v ústavech sociální p." jako příznak, ne záznam (3.4)
6. Párování s MPSV přes IČO plus RÚIAN kód, nikdy ne přes název

**Kontrolní bod:** vytiskni 20 spárovaných dvojic a ručně ověř, že jde o stejné zařízení. Falešná shoda je horší než chybějící.

### Etapa 3. Souřadnice a plná data

1. RÚIAN, join přes kód adresního místa
2. Převod S-JTSK do WGS84
3. Kontrola bounding boxu ČR
4. Řešení pro 676 záznamů bez kódu adresního místa
5. Kategorie podle 4.3
6. Plný běh, `katalog.json` a `zmeny.json`

**Kontrolní bod:** vykresli všechny body na mapu. Body mimo ČR nebo shluky na jednom místě znamenají chybu v parsování. Zkontroluj počty proti sekci 2.

### Etapa 4. Automatizace a pojistky

Podle sekce 5. Denní i měsíční workflow, prahové kontroly, validace, zákaz publikace prázdného výstupu, commit jen při změně.

**Kontrolní bod:** úmyslně podstrč poškozený soubor a ověř, že se `/data/` nezmění a přijde upozornění.

### Etapa 5. Ostrý provoz a předání

1. Sledování prvních tří automatických běhů
2. Ověření, že druhá strana data skutečně odebírá a zpracovává
3. Převod repozitáře na účet klienta. Ověřeno v dokumentaci GitHubu: převodem se zachovají commity, historie, webhooky, secrets i deploy keys a odkazy na starou adresu se přesměrují. Pozor, secrets na úrovni repozitáře se převádějí, ale secrets na úrovni organizace nebo prostředí ne.
4. **Převod notifikací:** klient si v Actions workflow vypne a hned zapne, tím se stane příjemcem. Zároveň si musí přepnout Settings, Notifications, System, Actions na Email. Ověřit společně úmyslným selháním běhu.
5. Dokumentace: jak se úloha spouští ručně, kde se ověří, že proběhla, co dělat při upozornění, a že budoucí úprava cronu přesune notifikace na toho, kdo ji provede
6. Předat citaci ÚZIS podle CC BY 4.0, musí být na webu

**Kontrolní bod:** klient má funkční automatickou aktualizaci se třemi úspěšnými běhy, repozitář na svém účtu, ověřené upozornění a dokumentaci. Druhá strana data zpracovává.

---

## 7. Průběžné testování

1. **Vzorek před plnými daty.** Nikdy neladit na 40 tisících řádcích, když stačí 200.
2. **Idempotence.** Dva běhy nad stejnými zdrojovými daty musí dát bajtově shodný `katalog.json` a **nesmí vzniknout žádný commit**. Testovat po každé úpravě generování, protože stačí jedno pole s časovým razítkem a pravidlo z 5.3 přestane platit.
3. **Ruční kontrola vzorku proti realitě.** Automatický test neodhalí prohozené souřadnice, mapa ano.
4. **Kontrola počtů proti sekci 2.** Jiné číslo znamená buď změnu dat, nebo chybu. Zjisti které, nepřepisuj dokument.
5. **Okrajové případy:** záznam bez kontaktu, bez souřadnic, se stejnou adresou jako jiný, obec s diakritikou, Praha s městskými částmi, zaniklý záznam.
6. **Validace vlastního výstupu proti vlastnímu schématu** je součástí každého běhu, ne jen testů.

---

## 8. Odchylky od zadání a otevřené otázky

### 8.1 Otevřené

| Otázka | Stav |
|---|---|
| **Souřadnice chybí u 110 z 2 912 míst (3,8 %).** | Dvě různé příčiny, které se nesmí slučovat. **(a) 71 míst (2,4 %) kód adresního místa má, ale aktuální měsíční snapshot RÚIAN ho nezná** (70 z MPSV, 1 z ÚZIS) — registry se aktualizují v jiném rytmu. ID je u nich korektní `misto-<kód>` a stabilní, chybí jen souřadnice; počet klesá s každým měsíčním během RÚIAN, ne garantovaně na nulu. **(b) 39 míst kód adresního místa nemá vůbec** (38 z MPSV, 1 z ÚZIS) — nemá se z čeho dohledat, tento počet neklesá. U obou je ve výstupu `souradnice: {lat: null, lng: null}`, schéma to podporuje. Geokódování přes externí zdroj (Nominatim) bylo zvážené a zamítnuté kvůli přesnosti: dalo by ulici nebo obec, ne adresní bod. |
| **Umístění citací na webu klienta.** | Povinné uvedení zdroje se týká ÚZIS i ČÚZK, u obou CC BY 4.0 podle NKOD. Znění obou citací je dohledané a zapsané v `README.md`, sekce Zdroje a licence. Zbývá ověřit, že je vývojář na web skutečně umístil (etapa 5, bod 6). |
| **324 míst nemá žádnou kategorii.** | Mapovací tabulka v 4.3 pokrývá 10 z 21 druhů sociálních služeb, které se u seniorů vyskytují. Nepokryté jsou hlavně odborné sociální poradenství, sociálně aktivizační služby pro seniory, centra denních služeb a sociální rehabilitace. Tato místa jsou ve výstupu se všemi údaji a `kategorie: []`, jen se nezobrazí v žádné záložce. Zařazení se posoudí zvlášť; mapování je v `config/kategorie-mapovani.json`, takže se doplní bez zásahu do kódu. |

### 8.2 Odchylky proti sekcím 2 a 3

Zaznamenáno podle pravidla 0.1. Sekce 2 a 3 popisují stav k 31. 8. 2026, tady jsou místa, kde se realita liší.

| Odchylka | Popis |
|---|---|
| **Zdroj RÚIAN je jiný, než uvádí 2.3.** | Stránka `nahlizenidokn.cuzk.gov.cz` je za hCaptchou a automatizovaně stáhnout nejde. Používá se ATOM feed `https://atom.cuzk.gov.cz/get.ashx?theme=RUIAN-CSV-ADR-ST`, který vrací přímý odkaz na `vdp.cuzk.gov.cz`. Soubor není jeden celostátní CSV, ale ZIP s 6 258 CSV po obcích, kódování Windows-1250, oddělovač středník. |
| **Převod souřadnic je EPSG:5513, ne 5514.** | Ověřeno na třech nezávislých bodech. S EPSG:5514 padají body mimo ČR. PROJ navíc nabízí pro tento převod několik operací se shodnou deklarovanou přesností 1 m, mezi nimi i slovenskou; výběr proto fixuje `area_of_interest` ohraničený na ČR v `import/ruian.py`, aby byl výsledek reprodukovatelný napříč verzemi PROJ. Souřadnice se na výstupu zaokrouhlují na 7 desetinných míst (`SOURADNICE_DESETINNYCH_MIST` v `import/build_katalog.py`), což je ~1 cm a pojme rozlišení obou zdrojů. |
| **ÚZIS a MPSV uvádějí u téhož areálu různý RÚIAN kód.** | Není to chyba určení organizace, ale systémový nesoulad mezi registry — tentýž areál má v každém registru jiný adresní bod. **Párování to neřeší a řešit nemůže:** shoda stojí na kódu adresního místa, takže záznam s odlišným kódem nechytí. Dva měřitelné důsledky. **(a)** Z 783 řádků druhu „Zdravotní péče v ústavech sociální p.“ se 438 připojí k domovu na tomtéž adresním bodě a **345 (44 %) se zahodí**, protože jejich domov v katalogu pod týmž adresním bodem není. **(b)** Ve výstupu zůstává **19 dvojic, kde je jedno místo jen z ÚZIS a druhé obsahuje MPSV službu téhož IČO, ve vzdálenosti 10 až 95 m** (například `misto-14264633` a `misto-72537001`, Charita Šumperk, 25 m), tedy dva piny pro jeden areál. Není to jev výlučný pro rozhraní registrů: dalších **143 dvojic se shodným IČO do 100 m** vzniká uvnitř jednoho zdroje a jsou mezi nimi jak sousední budovy, které oddělené být mají (Charita Frýdek-Místek, č. p. 1287 a 1288, 3 m), tak dva adresní body téhož domu (Domov na Dómském pahorku, Zahradnická 1534, orientační čísla 4 a 5, shodné souřadnice). Rozlišit obojí automaticky nelze — vazbu „tyto adresní body jsou jeden areál“ neeviduje ani jeden registr (pravidlo 0.2). Sděleno vývojáři 5. 9. 2026; případné shlukování podle IČO a vzdálenosti je na straně příjemce. |
| **Měsíční workflow nemá cron, ÚZIS a RÚIAN obstarává denní běh.** | Zadání 5.1 předepisuje „ÚZIS a RÚIAN měsíčně, samostatné workflow“. Samostatné workflow zůstává, ale bez `schedule` — spouští se jen ručně a od 8. 9. 2026 se jmenuje **Rucni import (vynuti stazeni UZIS + RUIAN)**, protože dělá totéž co denní běh, jen ÚZIS a RÚIAN stahuje vždy načisto místo čtení z cache. Denní se ze stejného důvodu jmenuje jen **Denni import**, ne „Denni import (MPSV)“ — od zavedení klíče cache obstarává i ÚZIS a RÚIAN, takže původní název sliboval míň, než workflow dělá. Commit message obou zní `Automaticky import: aktualizace dat`, bez jmenování zdroje, protože oba běhy mohou změnit data kteréhokoli z nich. Důvod věcný: od zavedení klíče cache odvozeného od dat zdrojů (viz 8.3) si denní běh novou měsíční verzi vezme sám v den, kdy vyjde, takže naplánovaný měsíční běh už nemá co dělat a byl by jen druhým pisatelem do téže cache. Kalendářní plán byl navíc příčinou měsíčního zpoždění RÚIAN, protože ČÚZK publikuje později než 3. v měsíci. Zadaný výsledek — ÚZIS a RÚIAN se aktualizují po každém měsíčním vydání — platí dál a nově i dřív; mění se jen to, které workflow ho zajišťuje. |
| **Objemy a počty v sekcích 2 a 3 se posunuly.** | Přeměřeno 8. 9. 2026 proti staženým zdrojům. Jde o běžný růst registrů, ne o změnu formátu; prahová pojistka z 5.2 se na tyto rozdíly nevztahuje, protože hlídá počet míst na výstupu, ne velikost vstupu. **Velikosti (2.1, 2.2):** `rpss.json` **99,0 MB**, ne „přes 30 MB“; `nrpzs.csv` **28,3 MB** a **40 870 řádků**, ne 40 848. **Druhy zařízení ÚZIS (2.2):** Domácí zdravotní péče **948**, ne 946; Hospic **30**, ne 29; Zdravotní péče v ústavech sociální p. **783**, ne 778. LDN 55, Nemocnice následné péče 55 a Rehabilitační ústav 28 sedí. **Chybějící kontakty (3.5):** bez kontaktu je **10 326 ze 40 870** řádků, ne 10 311 ze 40 848; u domácí zdravotní péče **186 z 948**, ne 185 z 946. **MPSV (2.1):** seniorských služeb je **2 602**, ne 2 600. **Očekávaný objem ze sekce 1** („zhruba 3 800 míst“) se nenaplnil a naplnit nemohl: sekce 1 sečetla 2 942 adres MPSV a asi 900 zdravotnických zařízení, jenže obojí se z definice místa (4.2) slučuje na adresní bod. Výstup má **2 912 míst a 4 007 položek `sluzby[]`** — počet míst je nižší, protože zdravotnická zařízení na adrese domova nevytvářejí druhé místo, a počet služeb vyšší, protože na jednom adresním bodě jich sídlí v průměru 1,4. |

### 8.3 Rozhodnutí, která upřesňují rozhraní

Vzniklo z písemného feedbacku vývojáře klienta (2. 9. 2026) a z auditu před předáním. Popisuje, jak výstup funguje.

| Téma | Pravidlo |
|---|---|
| **Verze schématu** | Aktuální je **1.2.0**. Odsouhlasené s vývojářem bylo 1.0.0; 1.1.0 přidalo `sluzby[].zarizeni`, 1.2.0 `sluzby[].oboryPece`. Obě jsou zpětně kompatibilní — žádné pole nezmizelo ani nezměnilo typ, takže čtenář 1.0.0 běží dál beze změny. **Obě přírůstková pole ale zatím nebyla vývojáři ohlášena**, i když jsou už v produkčních datech; podle 4.2 se dopředu hlásí jen nekompatibilní změna, takže jde o informaci, ne o porušení pravidla. Verze je na třech místech a musí sedět: `VERZE_SCHEMATU` v `build_katalog.py`, `verzeSchematu` v `meta.json` a v `katalog.json`. `data/ukazka.json` je zmrazený na 1.0.0 záměrně, neaktualizuje se. |
| **ID místa** | `misto-<kodAdresnihoMista>` vždy, bez ohledu na zdroj — jeden adresní bod je jedno místo a jeden pin. Kde MPSV kód adresního místa neuvádí, ID je `misto-bezadresy-<portalId>-<otisk názvu zařízení>`; zařízení nemá v MPSV vlastní identifikátor, takže název je jediný rozlišovač. Kde kód nemá ani ÚZIS, ID je `misto-uzis-bezadresy-<ID místa poskytování>` — tam vlastní identifikátor registr má, takže otisk názvu není potřeba (aktuálně 1 místo). Před zápisem běží kontrola na duplicitní ID, při shodě se nepublikuje. |
| **Slučování mezi zdroji** | **Jednotkou je adresní bod, ne organizace.** `kodAdresnihoMista` je zároveň definice místa (4.2) a jediný identifikátor, který oba registry vedou v identickém tvaru — MPSV 97,6 % zařízení u seniorských služeb (98,7 % po filtru na aktivní), ÚZIS 99,9 % relevantních řádků. ÚZIS záznam se proto připojí k MPSV místu právě tehdy, když sdílí adresní bod. Textové adresy porovnatelné nejsou (ÚZIS nemá kód obce a číslo popisné a orientační vede slepené v jednom poli), párování přes název zakazuje Etapa 2 bod 6. **Shoda IČO se záměrně nepoužívá jako samostatné kritérium.** Obě situace, kvůli kterým by se nabízela, řeší adresní bod sám: víc zařízení na jedné adrese má být jedno místo bez ohledu na to, kolik je za nimi poskytovatelů, a víc poboček jedné organizace má zůstat oddělených, protože každá má vlastní adresní bod. IČO by první případ rozštěpilo a druhý slepilo. Shoda je proto jednostupňová a klíč je jediný: kód adresního místa. Do 7. 9. 2026 stál před adresní shodou ještě stupeň s klíčem `(IČO, RÚIAN kód)`; byl odstraněn, protože jeho klíč byl jen zúžením adresní shody. Index se stavěl jako `(IČO, str(klíč místa))`, takže shoda mohla nastat jedině tam, kde se klíč místa rovná RÚIAN kódu řádku — tedy právě tam, kde uspěje i samotná adresa. Změřeno na plných datech: z 1 713 relevantních řádků našel stupeň na IČO 606, adresa 688, a rozporů, kdy by IČO ukázalo na jiné místo než adresa, bylo 0. Odstranění nezměnilo ani jedno `misto.id`, ani jeden příznak a ani jednu službu; přeskupilo jen pořadí `sluzby[]` u tří míst (`misto-3092631`, `misto-19206895`, `misto-24979848`), která dostávala záznamy z obou stupňů. |
| **Zdravotnické licence domovů** | Druh „Zdravotní péče v ústavech sociální p.“ nikdy nevytvoří místo ani položku v `sluzby[]` (viz 3.4). Připojí se jako příznak `poskytujeZdravotniPeci` u domova na tomtéž adresním bodě. Záznam, který takový domov v katalogu nemá, do výstupu nejde. Pravidlo je strukturální, je v `build_katalog.py`, ne v konfiguraci. |
| **Jedna registrace je v `sluzby[]` právě jednou** | MPSV vede pod jednou registrací seznam zařízení a zpracování ji na zařízení rozpadá, takže na jednom adresním bodě může tatáž registrace skončit vícekrát. Změřeno na plných datech: 13 takových položek ve 12 místech, a **liší se výhradně názvem zařízení** — poskytovatel, druh, formy, kapacita, kontakty i data poskytování jsou shodné, protože jsou vlastností registrace, ne zařízení. Nechat je oddělené škodilo měřitelně: kapacita je v MPSV registrovaná na službu, ne na zařízení. U `misto-27763331` (Domov Chrudim) jsou tři registrace s 20, 5 a 95 lůžky, tedy 120, ale `mpsv-7228` byla v poli dvakrát — jednou za 2. a jednou za 3. nadzemní podlaží — takže součet přes `sluzby[]` dával 215. Slučuje se proto podle `portalId`, tedy podle identifikátoru registrace, nikdy podle názvu (Etapa 2, bod 6). Názvy zařízení se nezahazují, jdou do nepovinného pole `sluzby[].zarizeni` — proto schéma 1.1.0. `pocetSluzeb` v `meta.json` je díky tomu 4 007 místo 4 020. Ve `sluzby[].zarizeni` je vidět 11 z těch 13 sloučení; u zbylých dvou má pole jediný prvek, takže se nezapíše vůbec. Jsou to jediné dva případy, kdy nějaký řetězec zmizel: `mpsv-311` měl dvě varianty názvu lišící se koncovou mezerou (porovnává se ořezaně, protože koncová mezera je překlep v registru, ne odlišující údaj) a `mpsv-4028` má dvě zařízení se shodným názvem „Pečovatelská služba“ a shodně chybějícím adresním kódem, takže obě spadnou na totéž náhradní ID. Do výstupu jde název vždy v původním tvaru. |
| **MPSV uvádí u části zařízení adresní kód jiné obce** | Ze 13 vícenásobných položek výše jsou 4 tohoto původu: „Ledax o.p.s. středisko Prachatice“ má kód adresního místa v Týně nad Vltavou, „středisko Kaplice“ v Trhových Svinech, „Charita Starý Knín — středisko Svaté Pole“ v Kamýku nad Vltavou. Zpracování je umisťuje podle kódu, tedy správně podle toho, co registr uvádí; nesprávný je název. Opravovat to nelze — určit, které středisko kam patří, by znamenalo domýšlet údaj, který v registru není (pravidlo 0.2). Ve výstupu proto zůstávají v `sluzby[].zarizeni` i tyto názvy, tak jak je vede MPSV. |
| **Textový název obce versus `kodObce`** | Název obce se přebírá z registru, ze kterého místo pochází, a nesjednocuje se. Pro Prahu se registry rozcházejí: MPSV uvádí `"Praha"` (193 míst), ÚZIS městskou část `"Praha 1"` až `"Praha 16"` (84 míst). Přepisovat jedno na druhé by znamenalo měnit údaj registru, dohledávat městskou část u MPSV míst nemáme z čeho. Řeší to `kodObce` z RÚIAN, shodně `554782` u 276 z těch 277 míst. Rozhraní proto stojí na pravidle **název pro zobrazení, kód pro logiku**; zapsáno v `data/dokumentace-rozhrani.md`. |
| **Kapacita** | `kapacitaRegistrovana` je uvnitř každé položky `formy[]` zvlášť. Služba může být registrovaná ve víc formách s různou kapacitou (například odlehčovací služby pobytově i terénně) a společné pole by tu vazbu ztratilo. |
| **Doba poskytování** | `datumPoskytovaniOd` a `datumPoskytovaniDo` jsou ve výstupu. Obě pole jsou jen u MPSV, tedy u 3 077 ze 4 007 položek `sluzby[]`. `Od` je vyplněné u všech 3 077, `Do` u 16 z nich (0,5 % položek MPSV, 0,4 % všech položek) a vždy s datem v budoucnosti — ukončené registrace se nepublikují. RPSS vede datum ukončení zvlášť na úrovni služby (`datumPoskytovaniDo`) a zvlášť na úrovni zařízení (`poskytujeDo`) a tyto dva údaje se v datech rozcházejí, proto filtr kontroluje obě úrovně (`is_sluzba_active` a `is_zarizeni_active` v `import/mpsv.py`). Ze 2 602 seniorských služeb má 389 vyplněné `Do`, z toho 380 v minulosti; ty se vyřadí, 9 s budoucím datem zůstává. |
| **Územní působnost terénních služeb se nedoplňuje** | MPSV eviduje jen `rozsirenePusobnostiVKraji`, vyplněné u 24 % terénních seniorských služeb a jen na úrovni kraje — pro vyhledávání v okruhu je to příliš hrubé. Odvozovat pokrytí z okresu sídla by znamenalo domýšlet data, která v registru nejsou (pravidlo 0.2). `adresa.kraj` a `adresa.obec` jsou u každého místa s vyplněnou adresou, `adresa.okres` u všech kromě 231 (193 pražských míst z MPSV, kde Praha okres nemá, a 36 míst bez adresy vůbec), takže si vlastní heuristiku může postavit příjemce. |
| **Klíč cache je odvozený od dat zdrojů, ne od kalendáře** | ÚZIS a RÚIAN mají dohromady 92 MB a mění se jednou měsíčně, denní běh je proto nestahuje pokaždé, ale drží v cache GitHub Actions. **Klíč té cache je `uzis-ruian-<Last-Modified ÚZIS>-<datum v názvu souboru ČÚZK>`**, například `uzis-ruian-2026-09-01-2026-08-31`. Denní běh se na obě hodnoty nejdřív levně zeptá (`stahni_zdroje.py --verze-zdroju`, HEAD na ÚZIS a pár kB ATOM feedu) a podle shody klíče buď nestahuje, nebo stáhne a uloží pod nový klíč. Nová verze zdroje = nový klíč = cache mine = stáhne se, a to v nejbližším denním běhu po vydání. Kalendářní klíč `uzis-ruian-<rok-měsíc>` tohle neuměl a měl dvě měřitelné vady. **(a) Zpoždění o měsíc:** měsíční běh startoval 3. v měsíci, ale ČÚZK publikuje později — běh `33859853428` (4. 9. 2026 09:46) stáhl `20260731_OB_ADR_csv.zip`, zatímco feed 8. 9. 2026 nabízel `20260831_OB_ADR_csv.zip`. Klíč `uzis-ruian-2026-09` byl tou dobou obsazený a `cache/save` na obsazeném klíči tiše skončí, takže srpnový RÚIAN by se do katalogu nedostal do 3. 10. **(b) Tiché zastarání:** kdyby měsíční běh selhal, denní běhy si přes `restore-keys` obnovily starší měsíc a každé čtení mu obnovilo sedmidenní lhůtu, takže by starý snapshot přežíval libovolně dlouho při zeleném buildu. Klíč odvozený od dat obojí ruší z principu — na obsazeném klíči nemůže uvíznout starší snapshot, protože jiná data mají jiný klíč. Zároveň nahrazuje dřívější samostatnou pojistku na chybějící cache: stav „cache neexistuje“ spadá do téže větve jako „zdroje mají novější verzi“ a řeší se stažením. Rozlišují se tři stavy, protože musí dopadnout různě: přesná shoda klíče (nestahovat), náhradní klíč `uzis-ruian-neurceno` při nedostupnosti zdroje a soubory na disku (pokračovat nad poslední uloženou verzí, aby výpadek ČÚZK nezastavil i import MPSV), zbytek (stáhnout). Ověřeno v sedmi stavech: přesná shoda, novější zdroj, chybějící cache, selhaná sonda se soubory i bez nich, chybí jen `nrpzs.csv`, chybí jen `ruian_adr.zip`. Sonda sama nikdy neshodí běh — při výpadku vypíše varování na stderr a náhradní klíč, návratový kód 0. **Sedmidenní lhůta, po které GitHub maže nečtenou cache, se z rizika stala úklidem.** Právě používaná cache se udržuje naživu sama, protože ji každý denní běh čte a čtení lhůtu obnovuje. Překonaná naopak vyhnije: jakmile se uloží nová verze, začne sedět přesná shoda klíče, a při přesné shodě se `restore-keys` vůbec nepoužijí, takže se staré cache už nikdo nedotkne. Změřeno 8. 9. 2026, kdy byla v repozitáři jediná cache — ještě pod starým kalendářním klíčem `uzis-ruian-2026-09`, 64 MiB, `created` 4. 9. 09:46 a `lastAccessed` 8. 9. 08:26, tedy čas denního běhu z téhož rána. Vyčerpání 10GB limitu je tím vyloučené: souběžně existují nanejvýš dvě cache po 64 MiB, a to jen v den přechodu na novou verzi zdroje. Stav „smazalo se všechno“ (workflow vypnuté přes týden, což etapa 5 kvůli předání notifikací záměrně dělá, nebo převod repozitáře, u kterého dokumentace GitHubu osud cache neuvádí) spadá do větve „stáhnout“ a vyřeší se sám. Selháním skončí jen prázdná cache **a zároveň** nedostupný zdroj — tam se do `data/` nic nezapíše a zůstane poslední platná verze, což je zamýšlené chování podle 5.2. **Klíč je společný pro oba měsíční zdroje a jedna cache drží oba soubory**, protože `actions/cache` bere celý seznam `path` jako jeden balík pod jedním klíčem (`nrpzs.csv` 28,3 MB, `ruian_adr.zip` 63,4 MB, `uzis_ruian_meta.json` 45 B, dohromady 91,7 MB a komprimováno 64 MiB). Důsledek: **když vydá novou verzi jen jeden ze dvou zdrojů, změní se klíč a stáhnou se oba**, i ten nezměněný. Vydávají každý měsíčně a ne v týž den (změřeno 8. 9. 2026: ÚZIS 1. 9., ČÚZK 31. 8.), takže se klíč mění až 24× ročně a asi polovina těch stažení je zbytečná. Oddělené klíče by to ušetřily za cenu dvou cache, dvou sond a dvou větví v rozhodování; jedno stažení 92 MB navíc měsíčně tu složitost nevyváží. MPSV cache nemá vůbec a stahuje se každý běh bezpodmínečně — mění se denně, takže by byla vždy netrefená. `_cache/` je v `.gitignore` a runner se po běhu zahazuje, takže mezi běhy nepřetrvá nic než tato jedna cache a soubory v `data/`. |
| **Obor péče se publikuje celý, `oborPece` zůstává** | `ZZ_obor_pece` je vícehodnotové (3.3) a do 8. 9. 2026 se z něj do výstupu dostával jen první obor. Změřeno na plných datech: ze 930 publikovaných ÚZIS služeb jich 242 uvádí oborů víc (na 238 místech), maximum je 32 oborů na jedné službě, a u 20 služeb kvůli tomu ve výstupu chyběla „paliativní medicína" — mimo jiné u Hospicové péče sv. Kleofáše a PAHOP. To je vada u údaje, který 3.2 označuje za jeden ze tří znaků, podle nichž se hospic vůbec pozná; filtr sám je v pořádku, `uzis.split_obor_pece` obory rozpadá správně a `filter_relevant` nad ním hospice pozná, ztrácely se až na výstupu. Úplný seznam je proto v novém poli `oboryPece`. **`oborPece` se ale neruší ani nemění na pole**, protože 1.0.0 je odsouhlasené a změna typu by znamenala 2.0.0 — dvě pole s překrývajícím se významem jsou vědomý ústupek kompatibilitě, ne nedopatření. Ověřeno porovnáním celých výstupů: proti 1.1.0 se u žádného z 2 912 míst nezměnilo nic jiného než přibylé pole a `oborPece` se u žádné služby neliší od `oboryPece[0]`. |
| **Sekundární druh zařízení ÚZIS se záměrně nečte** | `ZZ_druh_nazev_sekundarni` je vyplněný u 1 073 z 40 870 řádků a relevance se posuzuje jen podle `ZZ_druh_nazev`. Vypadá to jako opomenutí, není. Změřeno 8. 9. 2026: relevantní sekundární druh má 20 vyřazených řádků (14× domácí zdravotní péče, 4× LDN, 2× zdravotní péče v ústavech) a jejich plošné zařazení by přidalo 14 nových míst a 6 připojilo ke stávajícím. Mezi novými by byly Psychiatrická nemocnice Bohnice, Nemocnice Na Františku, Nemocnice sv. Zdislavy, Sanatorium Jablunkov, dvě zdravotnické dopravní služby (Royal Rangers, EMA Emergency), pět samostatných ordinací a lékárna — tedy přesně množina, kterou z týchž důvodů odmítá už filtr hospiců v `uzis.py` (celé nemocnice a soukromé ordinace jen proto, že mají relevantní licenci). Skutečně seniorské jsou z těch dvaceti tři: Světlo do Vašich domovů LuNA, Centrum zdravotní a sociální péče Liberec a Charita Polička. Poměr 3 ku 17 rozhodl; kdyby se sloupec začal číst, muselo by k němu přibýt další rozlišovací pravidlo, které registr neposkytuje (pravidlo 0.2). |
| **`datumZdrojovychDat` zaostává za zdrojem a je to správně** | Celý `meta.json` se zapisuje až za kontrolou hashe v `build_katalog.py`, takže když se katalog nezmění, neposune se ani datum zdrojových dat. Vypadá to jako zaseknutý import, není. Změřeno 8. 9. 2026: `rpss.json` měl toho dne `Last-Modified` 7. 9., denní běh (`34204451162`) ho stáhl, sestavil shodný katalog a skončil bez commitu — publikované `meta.json` proto dál uvádí `mpsv: 2026-09-05`, tedy datum poslední skutečné změny dat. Přepisovat datum při každém běhu nelze, tím by vznikal commit denně a padlo by pravidlo 5.3; přesně před tím ten odstavec varuje u času běhu a `datumZdrojovychDat` je tentýž případ. Sémantika pole je proto „datum snapshotu, ze kterého jsou postavená právě publikovaná data“, ne „datum poslední kontroly zdroje“ — zapsáno v `data/dokumentace-rozhrani.md`, aby to příjemce nepoužil jako indikátor běhu importu. |
| **Prahová pojistka a záměrné změny** | Kontrola z 5.2 bod 3 hlídá rozbitý zdroj. Když se záměrně změní pravidla zpracování na naší straně, práh zabere také; překročit ho lze jen ručně přepínačem `--zamerna-velka-zmena`. Workflow ho nikdy nepředává, v automatice tedy pojistka platí bez výjimky. Referenční počet se čte z `pocetMist` v `meta.json`, ne z `katalog.json` — obojí zapisuje týž běh, takže se to nemůže rozejít, ale pro test pojistky je rozhodující sáhnout na `meta.json`. |
| **Ověření pojistek (kontrolní bod etapy 4)** | Změřeno 7. 9. 2026 na plných datech, nad výstupem s 2 912 místy. **(a) Poškozený zdroj:** v `_cache/rpss.json` přepsán `druhSocialniSluzby` prvního záznamu z objektu na číslo. Běh spadl na validaci proti `rpss.schema.json` (`13 is not of type 'object'`) dřív, než se cokoli zpracovalo; `git status data/` prázdný. **(b) Prahová kontrola:** v `meta.json` snížen `pocetMist` na 2 000. Běh vypsal `POJISTKA: pocet mist se zmenil o 45.6% (2000 -> 2912), limit je 5%. NEPUBLIKUJI` a skončil s návratovým kódem 1, tedy selháním workflow, které vyvolá notifikaci. `katalog.json` i `zmeny.json` mají po běhu nezměněný kontrolní součet. **(c) Ruční přepínač:** týž stav s `--zamerna-velka-zmena` prošel jako varování místo odmítnutí, ale nic nezapsal, protože obsah katalogu byl shodný — přepínač povoluje překročení prahu, nevynucuje zápis. **(d) Kontrola duplicitních ID** se testovala sama v ostrém provozu: do 4. 9. 2026 kolidovala 3 ID na 8 místech a běh je odmítl publikovat. Validace vlastního výstupu proti `katalog.schema.json` běží při každém běhu a je v logu (`Validuji vystup proti schematu... OK, 0 chyb`). |
| **Pořadí `mista[]` a `sluzby[]` se nesrovnává** | Pořadí ve výstupu vzniká průchodem přes zdrojové soubory a kopíruje pořadí záznamů v nich; `build_katalog.py` ho před zápisem nesrovnává. Stojí to na očekávání, že registry exportují ve stabilním pořadí, a to očekávání je doložené: jediný dosavadní automatický běh (`e2a5523`, 4. 9. 2026) stahoval `rpss.json` i `nrpzs.csv` nanovo a relativní pořadí všech 3 250 společných míst zůstalo proti předchozí verzi zachované, diff se dotkl 1,2 % řádků souboru. Garance to ale není a nepředstírá se: ani jeden zdroj není seřazený podle žádného klíče (`portalId` v RPSS jde 4951, 2624, 4400, 4831, 6275…), a ověřeno přeházením pořadí na plných datech vznikne z téže množiny míst jiné pořadí, tedy jiný hash. **Kdyby k tomu došlo, projeví se to jedním commitem s diffem přes celý soubor, u kterého `zmeny.json` hlásí 0 přidaných, 0 změněných a 0 odebraných** — porovnává se podle `id`, takže pouhé přeskupení v něm není vidět. Data zůstávají správná, jde o šum v historii, ne o vadu obsahu. Příjemce se proto nemá na pořadí prvků spoléhat (zapsáno v `data/dokumentace-rozhrani.md`). Nesrovnává se proto, že by to ošetřovalo stav, který nenastal. Dostupné měření ukazuje stabilní pořadí a přibývání nových zařízení na něm nic nemění — nový záznam se vloží na svou pozici, vzájemné pořadí ostatních zůstává. Obrana proti přeskupení by tak stála na domněnce, ne na datech. Kdyby k němu došlo, řešením je seřadit `mista[]` a `sluzby[]` podle `id` před zápisem. Jediná výjimka, kde se dnes řadí: u míst čistě z ÚZIS jsou `sluzby[]` seřazené podle `ZZ_misto_poskytovani_ID` (`build_katalog.py:423`), a to ne kvůli stabilitě výstupu, ale proto, že první řádek určuje název a adresu místa — bez seřazení by je vybíral pořadím v CSV. |
