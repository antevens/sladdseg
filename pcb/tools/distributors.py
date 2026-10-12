"""Live stock check and list upload at DigiKey and Mouser for the parts in the order lists (order_bom.py).

Usage:
  python3 pcb/tools/distributors.py stock                       report, build/stock.md; exit 1 if a part breaks D-84
  python3 pcb/tools/distributors.py push [na|eu|both] [PLATES] [--primary=digikey|mouser] [--dry-run] [--no-price-breaks]
                                                                exactly the parts for PLATES plates (default: na 1; both:
                                                                PLATES of each), no spares; the primary distributor gets
                                                                every part it carries, the other one the rest; with
                                                                DigiKey keys a line goes up to a price break where that
                                                                costs less

Keys come from the environment only (never stored in the repo):
  DIGIKEY_CLIENT_ID, DIGIKEY_CLIENT_SECRET   DigiKey Product Information v4 (developer.digikey.com app, client credentials)
  MOUSER_SEARCH_KEY                          Mouser Search API key (My Mouser > APIs)
  MOUSER_CART_KEY                            Mouser Cart API key
  DIGIKEY_SITE / DIGIKEY_CURRENCY            default CA / CAD
  MOUSER_COUNTRY / MOUSER_CURRENCY           default CA / CAD
The DigiKey myLists upload needs no key: it returns a single-use link that opens the list (cart or myLists).
A distributor whose keys are missing is skipped with a note.

Parts rule (D-84): every part active (not NRND, end of life, obsolete) and in stock or normally stocked at DigiKey or
Mouser. A part passes when one distributor lists it active with stock; "active, 0 in stock" is reported for review.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import order_bom as ob  # noqa: E402

ROOT = ob.ROOT
REPORT = ROOT / "build" / "stock.md"
DK_TOKEN = "https://api.digikey.com/v1/oauth2/token"
DK_DETAILS = "https://api.digikey.com/products/v4/search/{}/productdetails"
DK_MYLISTS = "https://www.digikey.com/mylists/api/thirdparty"
MS_SEARCH = "https://api.mouser.com/api/v1/search/partnumber"
MS_CART = "https://api.mouser.com/api/v1/cart/items/insert"
MS_PAUSE = 2.1                       # Mouser Search API: 30 calls per minute
INACTIVE = ("obsolete", "end of life", "eol", "not recommended", "nrnd", "discontinued", "last time buy")


def env(name, default=None):
    v = os.environ.get(name, default)
    return v.strip() if isinstance(v, str) else v


def http(url, data=None, headers=None, form=False):
    """JSON request; returns (status, parsed body or text)."""
    body = None
    hdr = {"Accept": "application/json", **(headers or {})}
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            hdr["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            hdr["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdr, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw, status = r.read().decode(), r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read().decode(errors="replace"), e.code
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw


class DigiKey:
    def __init__(self):
        self.cid, self.secret = env("DIGIKEY_CLIENT_ID"), env("DIGIKEY_CLIENT_SECRET")
        self.ok = bool(self.cid and self.secret)
        self.token = None

    def headers(self):
        if not self.token:
            s, r = http(DK_TOKEN, {"client_id": self.cid, "client_secret": self.secret,
                                   "grant_type": "client_credentials"}, form=True)
            if s != 200 or not isinstance(r, dict) or "access_token" not in r:
                raise SystemExit(f"DigiKey token request failed ({s}): {r}")
            self.token = r["access_token"]
        return {"X-DIGIKEY-Client-Id": self.cid, "Authorization": f"Bearer {self.token}",
                "X-DIGIKEY-Locale-Site": env("DIGIKEY_SITE", "CA"),
                "X-DIGIKEY-Locale-Currency": env("DIGIKEY_CURRENCY", "CAD")}

    def lookup(self, pn):
        """dict(pn, stock, status, lead) or None when DigiKey does not list it."""
        for attempt in range(3):                          # retry server errors
            s, r = http(DK_DETAILS.format(urllib.parse.quote(pn, safe="")), headers=self.headers())
            if s < 500:
                break
            time.sleep(2 * (attempt + 1))
        if s == 404:
            return None
        if s != 200 or not isinstance(r, dict) or "Product" not in r:
            return dict(pn="?", stock=None, status=f"error {s}", lead="")
        p = r["Product"]
        status = (p.get("ProductStatus") or {}).get("Status") or ""
        if p.get("Discontinued"):
            status += " (discontinued)"
        if p.get("EndOfLife"):
            status += " (end of life)"
        dkpn = next((v.get("DigiKeyProductNumber") for v in p.get("ProductVariations") or []
                     if v.get("DigiKeyProductNumber")), "")
        return dict(pn=dkpn, stock=p.get("QuantityAvailable") or 0, status=status.strip(),
                    lead=f"{p['ManufacturerLeadWeeks']} wk" if p.get("ManufacturerLeadWeeks") else "")


    def price_breaks(self, pn):
        """[(break quantity, unit price)] for the packaging pn names (or the cut tape / first one for an MPN)."""
        for attempt in range(3):
            s, r = http(DK_DETAILS.format(urllib.parse.quote(pn, safe="")), headers=self.headers())
            if s < 500:
                break
            time.sleep(2 * (attempt + 1))
        if s != 200 or not isinstance(r, dict) or "Product" not in r:
            return []
        vs = r["Product"].get("ProductVariations") or []
        v = next((v for v in vs if v.get("DigiKeyProductNumber") == pn), None) or \
            next((v for v in vs if "Cut Tape" in ((v.get("PackageType") or {}).get("Name") or "")), None) or \
            (vs[0] if vs else None)
        if not v:
            return []
        return sorted((int(b["BreakQuantity"]), float(b["UnitPrice"])) for b in v.get("StandardPricing") or []
                      if b.get("BreakQuantity") and b.get("UnitPrice") is not None)


def best_quantity(n, breaks):
    """(quantity, cost at n, cost at the quantity): the quantity >= n with the lowest extended price, n on a tie."""
    def cost(q):
        unit = next((u for b, u in reversed(breaks) if b <= q), None)
        return None if unit is None else q * unit
    base = cost(n)
    if base is None:
        return n, None, None
    best = min([n] + [b for b, _ in breaks if b > n], key=lambda q: (round(cost(q), 4), q))
    return best, base, cost(best)


class Mouser:
    def __init__(self):
        self.search_key, self.cart_key = env("MOUSER_SEARCH_KEY"), env("MOUSER_CART_KEY")
        self.ok = bool(self.search_key)
        self.last = 0.0

    def search(self, pn):
        """Parts list for an exact part-number search (Mouser or manufacturer number)."""
        wait = MS_PAUSE - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)
        self.last = time.monotonic()
        s, r = http(f"{MS_SEARCH}?apiKey={self.search_key}",
                    {"SearchByPartRequest": {"mouserPartNumber": pn, "partSearchOptions": "Exact"}})
        if s != 200 or not isinstance(r, dict):
            raise SystemExit(f"Mouser search failed ({s}): {r}")
        if r.get("Errors"):
            raise SystemExit(f"Mouser search error for {pn}: {r['Errors']}")
        return (r.get("SearchResults") or {}).get("Parts") or []

    def lookup(self, pn, mpn):
        """dict(pn, stock, status, lead) for the part whose manufacturer number is mpn (or Mouser number pn)."""
        parts = self.search(pn)
        norm = lambda x: (x or "").replace("-", "").replace(" ", "").upper()
        hit = next((p for p in parts if norm(p.get("MouserPartNumber")) == norm(pn)), None) or \
            next((p for p in parts if norm(p.get("ManufacturerPartNumber")) == norm(mpn)), None)
        if not hit:
            return None
        stock = hit.get("AvailabilityInStock")
        try:
            stock = int(str(stock).replace(",", "")) if stock not in (None, "") else 0
        except ValueError:
            stock = None
        return dict(pn=hit.get("MouserPartNumber", ""), stock=stock, status=hit.get("LifecycleStatus") or "",
                    lead=hit.get("LeadTime") or "", avail=hit.get("Availability") or "")


def dk_pn(mpn):
    """DigiKey part number for an MPN: the DIGIKEY table's entry, the MPN where it has none (or an empty one), None
    where DigiKey does not carry it."""
    pn = ob.DIGIKEY.get(mpn, mpn)
    return mpn if pn == "" else pn


def active(status):
    s = (status or "").lower()
    return not any(k in s for k in INACTIVE)


def parts_rule(dk, ms):
    """'ok', 'review' (active, none in stock) or 'FAIL' (inactive or not listed at either)."""
    listed = [x for x in (dk, ms) if x and not str(x.get("status", "")).startswith("error")]
    if not listed or not any(active(x["status"]) for x in listed):
        return "FAIL"
    if any(active(x["status"]) and (x.get("stock") or 0) > 0 for x in listed):
        return "ok"
    return "review"


def stock():
    dk, ms = DigiKey(), Mouser()
    if not dk.ok and not ms.ok:
        raise SystemExit("no keys: set DIGIKEY_CLIENT_ID / DIGIKEY_CLIENT_SECRET and/or MOUSER_SEARCH_KEY")
    lines, _ = ob.collect({"NA": 1, "EU": 1})
    rows, bad = [], []
    fmt = lambda x: "-" if x is None else f"{x['stock'] if x['stock'] is not None else '?'} {x['status']}".strip()
    for mpn, line in lines.items():
        dkpn, mspn = dk_pn(mpn), ob.MOUSER.get(mpn, mpn) or mpn
        d = dk.lookup(dkpn) if dk.ok and dkpn is not None else None
        m = ms.lookup(mspn, mpn) if ms.ok and ob.MOUSER.get(mpn, "") is not None else None
        rule = parts_rule(d, m) if (dk.ok and ms.ok) else ("ok" if parts_rule(d, m) == "ok" else "partial")
        rows.append((mpn, line["mfr"], d, m, rule))
        if rule == "FAIL":
            bad.append(mpn)
        print(f"{rule:7s} {mpn:28s} DK {fmt(d):32s} MS {fmt(m)}", flush=True)
    out = [f"# Stock check {date.today().isoformat()}", "",
           f"DigiKey ({env('DIGIKEY_SITE', 'CA')}): {'queried' if dk.ok else 'skipped (no keys)'}; "
           f"Mouser: {'queried' if ms.ok else 'skipped (no key)'}. Parts rule: D-84.", "",
           "| Rule | MPN | Maker | DigiKey PN | DK stock | DK status | DK lead | Mouser PN | MS stock | MS status | MS lead |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    cell = lambda x, k: "" if x is None else str(x.get(k) if x.get(k) is not None else "?")
    for mpn, mfr, d, m, rule in rows:
        out.append(f"| {rule} | {mpn} | {mfr} | {cell(d, 'pn')} | {cell(d, 'stock')} | {cell(d, 'status')} | "
                   f"{cell(d, 'lead')} | {cell(m, 'pn')} | {cell(m, 'stock')} | {cell(m, 'status')} | {cell(m, 'lead')} |")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(out) + "\n")
    print(f"wrote {REPORT}")
    if bad:
        print("parts rule (D-84) not met: " + ", ".join(bad))
        sys.exit(1)


def push(na, eu, primary, dry):
    plates = {"NA": na, "EU": eu}
    lines, _ = ob.collect(plates)
    name = "smart-wallplate v0.5 " + " ".join(f"{k}{n}" for k, n in (("NA", na), ("EU", eu)) if n) + \
        f" {date.today().isoformat()}"
    dk_parts, ms_items = [], []
    for mpn, line in lines.items():
        n = sum(k * plates[v] for v, k in line["per"].items())   # exact: no spares
        ref = ("WP " + " ".join(sorted({r.split()[0] for r in line["refs"]})) + " " + line["refs"][0].split()[-1])[:48]
        dkpn, mspn = dk_pn(mpn), ob.MOUSER.get(mpn, "")
        mfr, note = line["mfr"], line["desc"]
        to_dk = dkpn is not None and (primary == "digikey" or mspn is None)
        if to_dk:
            dk_parts.append({"requestedPartNumber": dkpn, "manufacturerName": mfr,
                             "referenceDesignator": ", ".join(sorted({r.split()[-1] for r in line["refs"]}))[:200],
                             "customerReference": ref, "notes": note[:200], "quantities": [{"quantity": n}]})
        elif mspn is not None:
            ms_items.append((mpn, mspn, n, ref))
        else:
            print(f"  {mpn}: carried by neither list, left out")
    dk = DigiKey()
    if dk.ok and dk_parts and "--no-price-breaks" not in sys.argv:          # a larger quantity that costs less
        saved = 0.0
        for part in dk_parts:
            n = part["quantities"][0]["quantity"]
            q, c0, c1 = best_quantity(n, dk.price_breaks(part["requestedPartNumber"]))
            if q != n:
                part["quantities"][0]["quantity"] = q
                saved += c0 - c1
                print(f"  {part['requestedPartNumber']}: {n} -> {q} at a price break ({c0:.2f} -> {c1:.2f} "
                      f"{env('DIGIKEY_CURRENCY', 'CAD')})")
        if saved:
            print(f"  price breaks save {saved:.2f} {env('DIGIKEY_CURRENCY', 'CAD')}")
    elif dk_parts:
        print("  price breaks not checked (no DigiKey keys)")
    print(f"DigiKey myLists '{name}': {len(dk_parts)} lines")
    if not dk_parts:
        pass
    elif dry:
        print(json.dumps({"listName": name, "parts": dk_parts}, indent=1)[:4000])
    else:
        s, r = http(f"{DK_MYLISTS}?{urllib.parse.urlencode({'listName': name})}", dk_parts)
        if s >= 300:
            raise SystemExit(f"DigiKey myLists upload failed ({s}): {r}")
        print(f"DigiKey list link (single use): {r}")
    print(f"Mouser cart: {len(ms_items)} lines")
    ms = Mouser()
    if not ms_items:
        return
    if not ms.cart_key or not ms.ok:
        print("Mouser cart skipped: set MOUSER_SEARCH_KEY (part numbers) and MOUSER_CART_KEY; lines:")
        for mpn, mspn, n, ref in ms_items:
            print(f"  {mspn or mpn} x {n} ({ref})")
        return
    items = []
    for mpn, mspn, n, ref in ms_items:
        hit = ms.lookup(mspn or mpn, mpn)
        if not hit:
            print(f"  Mouser has no {mpn}: left out")
            continue
        items.append({"MouserPartNumber": hit["pn"], "Quantity": n, "CustomerPartNumber": ref})
    if dry:
        print(json.dumps(items, indent=1))
        return
    q = urllib.parse.urlencode({"apiKey": ms.cart_key, "countryCode": env("MOUSER_COUNTRY", "CA"),
                                "currencyCode": env("MOUSER_CURRENCY", "CAD")})
    key = ""
    for i in range(0, len(items), 100):                    # 100 items per request
        s, r = http(f"{MS_CART}?{q}", {"CartKey": key, "CartItems": items[i:i + 100]})
        if s != 200 or not isinstance(r, dict) or r.get("Errors"):
            raise SystemExit(f"Mouser cart insert failed ({s}): {r}")
        key = r.get("CartKey", key)
    print(f"Mouser cart key: {key} ({len(items)} lines); open it in My Mouser (Cart)")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or args[0] not in ("stock", "push"):
        raise SystemExit(__doc__)
    if args[0] == "stock":
        stock()
    else:
        primary = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--primary=")), "digikey")
        if primary not in ("digikey", "mouser"):
            raise SystemExit("--primary must be digikey or mouser")
        variant = args[1] if len(args) > 1 else "na"
        if variant not in ("na", "eu", "both"):
            raise SystemExit("variant must be na, eu or both")
        n = int(args[2]) if len(args) > 2 else 1
        if n < 1:
            raise SystemExit("PLATES must be 1 or more")
        push(n if variant in ("na", "both") else 0, n if variant in ("eu", "both") else 0, primary,
             "--dry-run" in sys.argv)


if __name__ == "__main__":
    main()
