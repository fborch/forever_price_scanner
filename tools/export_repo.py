# Export the price archive to the shared repo layout:
#   data/<realm>/<YYYY-MM-DD>/<scanner>.csv  item_key,item_id,min_buyout,max_of_min,quantity   (copper)
#   items.csv                                 item_id,name,quality,item_level,class_id,subclass_id
import sqlite3, sys, re, os, csv, datetime
db, itemdb, cgsv, out, scanner = sys.argv[1:6]
REALM_DIR = 'CAMWOW-EU5-Realm-3-PvE_Alliance'
D0 = datetime.date(2020, 1, 1)
c = sqlite3.connect(db)
info = {}
for line in open(itemdb, encoding='utf-8', errors='replace'):
    m = re.match(r"\[(\d+)\] = \{'((?:[^'\\]|\\.)*)'(.*)\},?\s*$", line)
    if m:
        t = re.findall(r'(-?\d+|nil)', m.group(3).split('}')[-1])
        try: info[int(m.group(1))] = [m.group(2).replace("\\'", "'"), '', t[0] if False else '', int(t[-2]), int(t[-1])]
        except Exception: info[int(m.group(1))] = [m.group(2).replace("\\'", "'"), '', '', '', '']
sv = open(cgsv, encoding='utf-8', errors='replace').read()
for m in re.finditer(r'\[(\d+)\] = \{\s*"((?:[^"\\]|\\.)*)",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)', sv):
    i = int(m.group(1)); info[i] = [m.group(2), m.group(6), m.group(3), int(m.group(4)), int(m.group(5))]
used = set(); n = 0
for (d,) in c.execute("select distinct day from prices where realm='PvE' order by day"):
    date = (D0 + datetime.timedelta(days=d)).isoformat()
    p = os.path.join(out, 'data', REALM_DIR, date); os.makedirs(p, exist_ok=True)
    with open(os.path.join(p, scanner + '.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['item_key', 'item_id', 'min_buyout', 'max_of_min', 'quantity'])
        for item, low, high, qty in c.execute("select item,low,high,qty from prices where realm='PvE' and day=? and low>0 order by item", (d,)):
            iid = int(item.split(':')[1] if item.startswith('gr:') else item)
            used.add(iid); w.writerow([item, iid, low, high, qty or 0]); n += 1
# Merge into items.csv: never drop rows or overwrite values others added; only fill empty fields.
ipath = os.path.join(out, 'items.csv'); rows = {}
if os.path.exists(ipath):
    with open(ipath, encoding='utf-8') as f:
        r = csv.reader(f); next(r, None)
        for x in r:
            if x: rows[int(x[0])] = (x + [''] * 6)[:6]
for i in used:
    x = info.get(i); mine = [str(i)] + ([str(v) for v in x[:5]] if x else [''] * 5)
    cur = rows.get(i)
    rows[i] = [str(i)] + [(cur[k] if cur and cur[k] != '' else mine[k]) for k in range(1, 6)]
with open(ipath, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['item_id', 'name', 'quality', 'item_level', 'class_id', 'subclass_id'])
    for i in sorted(rows): w.writerow(rows[i])
print('rows', n, 'items', len(used))
