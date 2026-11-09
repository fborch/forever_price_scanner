#!/usr/bin/env python3
"""Export Auctionator's price database to this repo's CSV layout. Standalone: Python 3, no packages.

Usage:
  python3 tools/auctionator_to_csv.py <path to SavedVariables/Auctionator.lua> <scanner name> [repo dir] [--realm-dir NAME] [--key KEY]

Writes data/<realm-dir>/<YYYY-MM-DD>/<scanner>.csv for every day Auctionator still remembers (~21 days),
overwriting only this scanner's own files, and adds unknown item ids to items.csv (never overwrites names).
"""
import re, sys, os, csv, struct, datetime, argparse

ap = argparse.ArgumentParser()
ap.add_argument('auctionator_lua'); ap.add_argument('scanner'); ap.add_argument('repo', nargs='?', default='.')
ap.add_argument('--realm-dir', default='CAMWOW-EU5-Realm-3-PvE_Alliance',
                help='folder under data/: <Realm>_<Faction> with spaces as dashes')
ap.add_argument('--key', default='', help="Auctionator realm key to read (default: the one with most data; on CAMWOW EU5 it is 'PvE')")
A = ap.parse_args()
if not re.fullmatch(r'[a-z0-9_-]+', A.scanner): sys.exit('scanner name: lowercase letters, digits, - or _ only')

class Cbor:
    def __init__(s, b): s.b = b; s.i = 0
    def u(s, ai):
        if ai < 24: return ai
        n = {24: 1, 25: 2, 26: 4, 27: 8}[ai]; v = int.from_bytes(s.b[s.i:s.i + n], 'big'); s.i += n; return v
    def r(s):
        ib = s.b[s.i]; s.i += 1; mt = ib >> 5; ai = ib & 31
        if mt == 7:
            if ai in (20, 21, 22): return {20: False, 21: True, 22: None}[ai]
            fmt, n = {25: ('>e', 2), 26: ('>f', 4), 27: ('>d', 8)}[ai]
            v = struct.unpack(fmt, s.b[s.i:s.i + n])[0]; s.i += n; return v
        v = s.u(ai)
        if mt == 0: return v
        if mt == 1: return -1 - v
        if mt in (2, 3): x = s.b[s.i:s.i + v]; s.i += v; return x
        if mt == 4: return [s.r() for _ in range(v)]
        if mt == 5: return {s.r(): s.r() for _ in range(v)}
        if mt == 6: return s.r()

raw = open(A.auctionator_lua, 'rb').read()
sec = raw[raw.find(b'AUCTIONATOR_PRICE_DATABASE'):]
end = sec.find(b'AUCTIONATOR_POSTING_HISTORY'); end = end if end > 0 else len(sec)
cands = [(m.group(1), m.end()) for m in re.finditer(rb'\["([^"\]]+)"\] = "', sec[:end]) if not m.group(1).startswith(b'__')]
if A.key: cands = [c for c in cands if c[0] == A.key.encode()]
if not cands: sys.exit('No Auctionator price data found. Scan at the auction house, then /reload in game.')
def blen(start):
    j = start
    while True:
        j = sec.find(b'"', j)
        if sec[j - 1] != 0x5c: return j - start
        j += 1
key, k = max(cands, key=lambda c: blen(c[1]))
# Unescape the Lua string into the raw CBOR bytes.
out = bytearray(); ESC = {ord('n'): 10, ord('r'): 13, ord('t'): 9, ord('\\'): 92, ord('"'): 34, ord("'"): 39, 10: 10, 13: 13,
                          ord('a'): 7, ord('b'): 8, ord('f'): 12, ord('v'): 11}
while True:
    c = sec[k]
    if c == 0x22: break
    if c == 0x5c:
        n = sec[k + 1]
        if 48 <= n <= 57:
            m = re.match(rb'\d{1,3}', sec[k + 1:k + 4]).group(); out.append(int(m)); k += 1 + len(m); continue
        if n == 0x0d and sec[k + 2] == 0x0a: out.append(10); k += 3; continue
        out.append(ESC[n]); k += 2; continue
    out.append(c); k += 1
db = Cbor(bytes(out)).r()
s = lambda x: x.decode('latin1') if isinstance(x, bytes) else str(x)

D0 = datetime.date(2020, 1, 1)
days = {}
for item, v in db.items():
    if not isinstance(v, dict): continue
    v = {s(a): b for a, b in v.items()}
    h = v.get('h') if isinstance(v.get('h'), dict) else {}
    l = v.get('l') if isinstance(v.get('l'), dict) else {}
    a = v.get('a') if isinstance(v.get('a'), dict) else {}
    for d, hv in h.items():
        low = min(hv, l.get(d, hv))
        if low and low > 0: days.setdefault(int(s(d)), []).append((s(item), low, hv, a.get(d) or 0))

ids = set(); rows = 0
for d, lst in sorted(days.items()):
    p = os.path.join(A.repo, 'data', A.realm_dir, (D0 + datetime.timedelta(days=d)).isoformat()); os.makedirs(p, exist_ok=True)
    with open(os.path.join(p, A.scanner + '.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['item_key', 'item_id', 'min_buyout', 'max_of_min', 'quantity'])
        for item, low, hv, q in sorted(lst):
            iid = int(item.split(':')[1] if item.startswith('gr:') else item); ids.add(iid)
            w.writerow([item, iid, low, hv, q]); rows += 1

ipath = os.path.join(A.repo, 'items.csv'); known = set(); old = []
if os.path.exists(ipath):
    with open(ipath, encoding='utf-8') as f:
        r = csv.reader(f); next(r, None); old = [x for x in r if x]; known = {int(x[0]) for x in old}
new = [[i, '', '', '', '', ''] for i in sorted(ids - known)]
with open(ipath, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['item_id', 'name', 'quality', 'item_level', 'class_id', 'subclass_id'])
    for x in sorted(old + new, key=lambda x: int(x[0])): w.writerow(x)
print(f"key {s(key)!r}: {rows} prices over {len(days)} days -> data/{A.realm_dir}/*/{A.scanner}.csv; {len(new)} new item ids added to items.csv")
