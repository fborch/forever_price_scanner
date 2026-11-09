# Forever price scanner

Shared auction house price history for **WoW Forever**, collected from Auctionator scans.

## Layout

```
items.csv                                   item_id, name, quality, item_level, class_id, subclass_id
data/<realm>_<faction>/<YYYY-MM-DD>/<scanner>.csv
```

- One file per day per person who scanned (`anders.csv`, `<brother>.csv`, ...). Two people can push the same day without merge conflicts.
- Realm folder: `CAMWOW-EU5-Realm-3-PvE_Alliance`. Use a separate folder for another faction or realm (the auction houses are separate).

## Daily price file columns

| Column | Meaning |
|---|---|
| `item_key` | Auctionator key: the item id, or `gr:<id>:<suffix>` for random-suffix greens ("of the Bear" etc.) |
| `item_id` | Base item id (join with `items.csv`) |
| `min_buyout` | Lowest buyout per item seen that day, in **copper** (10000 = 1g) |
| `max_of_min` | Highest of that day's lowest prices (when the item was scanned more than once in the day) |
| `quantity` | Number listed in the scan |

To get "the" price for an item and day with several scanners, take the lowest `min_buyout` across the files.

## Source

Exported from Auctionator's `AUCTIONATOR_PRICE_DATABASE` (SavedVariables). Anyone can add their own scans with `tools/auctionator_to_csv.py` (standalone, Python 3 only); see **CLAUDE_SETUP.md** for setting up Claude to do it after every scan. `tools/export_repo.py` is Anders' exporter from his long-term archive. Auctionator keeps only ~21 days itself; this repo is the long-term history. Day boundaries follow Auctionator's day count (UTC).
