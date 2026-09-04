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
| **Souřadnice chybí u 110 z 2 917 míst (3,8 %).** | Jde o adresní body, které MPSV eviduje, ale aktuální měsíční snapshot RÚIAN je nezná — registry se aktualizují v jiném rytmu. Ve výstupu `souradnice: {lat: null, lng: null}`, schéma to podporuje. Geokódování přes externí zdroj (Nominatim) bylo zvážené a zamítnuté kvůli přesnosti: dalo by ulici nebo obec, ne adresní bod. Počet klesá s každým měsíčním během RÚIAN, ne garantovaně na nulu. Vývojáři sdělit, ať to v UI ošetří jako dočasný stav. |
| **Znění povinné citace ÚZIS.** | Licence CC BY 4.0 vyžaduje citaci na webu. Přesné znění je na stránce datové sady, zatím neopsané. Předat klientovi při předání (etapa 5, bod 6). |
| **327 míst nemá žádnou kategorii.** | Mapovací tabulka v 4.3 pokrývá 9 z 21 druhů sociálních služeb, které se u seniorů vyskytují. Nepokryté jsou hlavně odborné sociální poradenství, sociálně aktivizační služby pro seniory, centra denních služeb a sociální rehabilitace. Tato místa jsou ve výstupu se všemi údaji a `kategorie: []`, jen se nezobrazí v žádné záložce. Zařazení se posoudí zvlášť; mapování je v `config/kategorie-mapovani.json`, takže se doplní bez zásahu do kódu. |

### 8.2 Odchylky proti sekcím 2 a 3

Zaznamenáno podle pravidla 0.1. Sekce 2 a 3 popisují stav k 31. 8. 2026, tady jsou místa, kde se realita liší.

| Odchylka | Popis |
|---|---|
| **Zdroj RÚIAN je jiný, než uvádí 2.3.** | Stránka `nahlizenidokn.cuzk.gov.cz` je za hCaptchou a automatizovaně stáhnout nejde. Používá se ATOM feed `https://atom.cuzk.gov.cz/get.ashx?theme=RUIAN-CSV-ADR-ST`, který vrací přímý odkaz na `vdp.cuzk.gov.cz`. Soubor není jeden celostátní CSV, ale ZIP s 6 258 CSV po obcích, kódování Windows-1250, oddělovač středník. |
| **Převod souřadnic je EPSG:5513, ne 5514.** | Ověřeno na třech nezávislých bodech. S EPSG:5514 padají body mimo ČR. PROJ navíc nabízí pro tento převod několik operací se shodnou deklarovanou přesností 1 m, mezi nimi i slovenskou; výběr proto fixuje `area_of_interest` ohraničený na ČR v `import/ruian.py`, aby byl výsledek reprodukovatelný napříč verzemi PROJ. Souřadnice se na výstupu zaokrouhlují na 7 desetinných míst (`SOURADNICE_DESETINNYCH_MIST` v `import/build_katalog.py`), což je ~1 cm a pojme rozlišení obou zdrojů. |
| **ÚZIS a MPSV uvádějí u téhož poskytovatele různý RÚIAN kód.** | Týká se zhruba poloviny záznamů druhu „Zdravotní péče v ústavech sociální p.“ Není to chyba určení organizace, ale systémový nesoulad mezi registry — tentýž areál má v každém registru jiný adresní bod. Řeší se dvoustupňovým párováním, viz 8.3. |

### 8.3 Rozhodnutí, která upřesňují rozhraní

Vzniklo z písemného feedbacku vývojáře klienta (2. 9. 2026) a z auditu před předáním. Popisuje, jak výstup funguje.

| Téma | Pravidlo |
|---|---|
| **ID místa** | `misto-<kodAdresnihoMista>` vždy, bez ohledu na zdroj — jeden adresní bod je jedno místo a jeden pin. Kde MPSV kód adresního místa neuvádí, ID je `misto-bezadresy-<portalId>-<otisk názvu zařízení>`; zařízení nemá v MPSV vlastní identifikátor, takže název je jediný rozlišovač. Před zápisem běží kontrola na duplicitní ID, při shodě se nepublikuje. |
| **Slučování mezi zdroji** | Podle `kodAdresnihoMista`. Shoda IČO+RÚIAN je vyhrazená jen pro příznak `poskytujeZdravotniPeci`. |
| **Zdravotnické licence domovů** | Druh „Zdravotní péče v ústavech sociální p.“ nikdy nevytvoří místo ani položku v `sluzby[]` (viz 3.4). Připojí se jako příznak `poskytujeZdravotniPeci` — nejdřív přes shodu IČO+RÚIAN, pak přes sdílený adresní bod. Záznam, který se nepřipojí ani tak, do výstupu nejde. Pravidlo je strukturální, je v `build_katalog.py`, ne v konfiguraci. |
| **Kapacita** | `kapacitaRegistrovana` je uvnitř každé položky `formy[]` zvlášť. Služba může být registrovaná ve víc formách s různou kapacitou (například odlehčovací služby pobytově i terénně) a společné pole by tu vazbu ztratilo. |
| **Doba poskytování** | `datumPoskytovaniOd` a `datumPoskytovaniDo` jsou ve výstupu. `Od` je vyplněno u všech služeb, `Do` zhruba u 15 % (ukončené registrace). |
| **Územní působnost terénních služeb se nedoplňuje** | MPSV eviduje jen `rozsirenePusobnostiVKraji`, vyplněné u 24 % terénních seniorských služeb a jen na úrovni kraje — pro vyhledávání v okruhu je to příliš hrubé. Odvozovat pokrytí z okresu sídla by znamenalo domýšlet data, která v registru nejsou (pravidlo 0.2). `adresa.kraj`, `adresa.okres` a `adresa.obec` jsou u každého místa, takže si vlastní heuristiku může postavit příjemce. |
| **Prahová pojistka a záměrné změny** | Kontrola z 5.2 bod 3 hlídá rozbitý zdroj. Když se záměrně změní pravidla zpracování na naší straně, práh zabere také; překročit ho lze jen ručně přepínačem `--zamerna-velka-zmena`. Workflow ho nikdy nepředává, v automatice tedy pojistka platí bez výjimky. |
