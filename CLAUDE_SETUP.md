# Oppsett: få Claude til å skanne AH-priser inn i dette repoet

Denne filen er skrevet for at **Fredrik (eller hvem som helst) skal kunne gi sin egen Claude det samme oppsettet som Anders har**:
Claude leser Auctionator-dataene fra spillmappen på PC-en og legger dagens AH-priser inn i dette repoet.

Del 1 er det **du** gjør én gang. Del 2 er teksten du limer inn til **Claude**. Del 3 er det du gjør hver gang du har skannet.

---

## Del 1 – Forberedelser (én gang)

1. **Installer Auctionator** i WoW Forever (`_forever_\Interface\AddOns\Auctionator`). Start spillet helt på nytt etter installering (ikke bare `/reload`).
2. **Claude desktop-appen** på PC-en, og en Claude-samtale (gjerne et eget Project, f.eks. «Wow finance»).
3. **Gi Claude tilgang til WoW-mappen**: i desktop-appen, legg til mappen `C:\Program Files (x86)\World of Warcraft` (eller der WoW er installert) som tilkoblet mappe. Claude trenger å lese `_forever_\WTF\Account\<KONTO>\SavedVariables\Auctionator.lua`.
4. **GitHub-tilgang til repoet** – én av to:
   - **Anbefalt:** koble GitHub-kontoen din til Claude (Settings → Connectors → GitHub) og sørg for at kontoen har skrivetilgang til `fborch/forever_price_scanner`.
   - **Alternativ:** lag en *fine-grained personal access token* på GitHub (Settings → Developer settings → Personal access tokens → Fine-grained), **kun for dette repoet**, med rettigheten *Contents: Read and write*. Ikke lim nøkkelen inn i offentlige steder, og lag en ny hvis den har vært delt.
5. Velg et **skannernavn** (små bokstaver, f.eks. `fredrik`). Dine filer heter da `fredrik.csv`, Anders sine `anders.csv`.

## Del 2 – Lim dette inn til Claude (første gang)

```text
Jeg spiller WoW Forever og skanner auksjonshuset med Auctionator. Jeg vil at du legger AH-prisene
mine inn i det delte GitHub-repoet fborch/forever_price_scanner hver gang jeg sier "skannet" eller "reloaded".

Fakta:
- Spillmappen er tilkoblet. Prisene ligger i
  <WoW>\_forever_\WTF\Account\<KONTO>\SavedVariables\Auctionator.lua (finn riktig kontomappe selv).
- Skannernavnet mitt er: fredrik
- Server og fraksjon: CAMWOW EU5 Realm 3 PvE, <Alliance eller Horde>.
  Realm-mappe i repoet: CAMWOW-EU5-Realm-3-PvE_<Alliance eller Horde>
- Repoet har README.md (format) og tools/auctionator_to_csv.py (eksportskriptet). Les README først.

Slik gjør du det hver gang:
1. Klon eller pull repoet (main).
2. Kjør:
   python3 tools/auctionator_to_csv.py "<sti til Auctionator.lua>" fredrik . --realm-dir CAMWOW-EU5-Realm-3-PvE_<fraksjon>
   Skriptet skriver data/<realm-dir>/<dato>/fredrik.csv for alle dager Auctionator husker (~21 dager)
   og legger nye item-id-er til i items.csv uten å endre eksisterende navn.
3. Endre aldri andres filer (f.eks. anders.csv). Bare legg til / oppdater dine egne.
4. Commit med en kort melding ("fredrik: prices <dato>") og push til main. Ved konflikt: pull --rebase og push igjen.
5. Si kort fra hvor mange priser og dager som ble lastet opp.

Viktig:
- Auctionator lagrer bare til disk ved /reload eller utlogging. Har jeg ikke gjort /reload etter skanningen,
  er dataene gamle – si fra.
- Sjekk TimeOfLastBrowseScan / TimeOfLastReplicateScan i Auctionator.lua for å se når siste skanning var.
- Hvis git-push fra skyen blir blokkert, kjør git fra PC-en min (shell på PC-en) i stedet.
- Skriv aldri GitHub-nøkkelen inn i filer i repoet eller i notater.
```

Hvis du bruker en token i stedet for å koble GitHub: gi Claude nøkkelen i samme melding, eller lagre den i en fil på PC-en som Claude kan lese (f.eks. utenfor repoet), og si hvor den ligger.

## Del 3 – Hver gang du har skannet

1. Åpne auksjonshuset og la Auctionator skanne (eller søk i flere kategorier).
2. Skriv `/reload` i spillet (da lagres dataene til disk).
3. Si til Claude: **«skannet og reloaded»**.

---

## Teknisk bakgrunn (for Claude)

- `AUCTIONATOR_PRICE_DATABASE` i Auctionator.lua har én nøkkel per realm. **På CAMWOW EU5 heter nøkkelen bare `"PvE"`**, ikke "<Realm> <Faction>". Skriptet velger nøkkelen med mest data, eller den du gir med `--key`.
- Verdien er en CBOR-blob i en escapet Lua-streng. Per item-nøkkel: `m` = siste laveste buyout, `h`/`l` = dagens høyeste/laveste av laveste pris, `a` = antall til salgs per dag. Dagnummer telles fra 2020-01-01. `gr:<id>:<suffix>` er grønne med tilfeldig suffiks («of the Bear»).
- `min_buyout` i CSV = min(h, l) for dagen; `max_of_min` = h; `quantity` = a. Alle priser i copper.
- WoW Forever bruker det moderne auksjonshuset; Auctionator registrerer priser fra søk (`TimeOfLastBrowseScan`).
- Navn i `items.csv`: Auctionator lagrer ikke navn. Nye id-er legges inn med tomt navn; Anders' oppsett fyller navn fra spillets item-database.
