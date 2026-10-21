"""The agents' world: stores, their listings, a seller register and a price feed.

Two kinds of world, same shape, so every pattern and both frameworks run unchanged on either:

  demo        data/shoes.json. Three demo stores with ordinary traps: a cheap black shoe that isn't a running
              shoe, a running shoe without size 9, and a ₹699 "Sparx" from a reseller nobody has checked.
  live        real listings from Amazon.in, Flipkart and Myntra, collected by patterns/live.py in your Chrome.
              Type and colour come from the evidence text. Size can't be seen on a search page, so it is not
              part of the query and stays unverified. The "seller register" becomes an evidence check: the
              store's own host, the product page read, not a search-index fallback, fresh.
  recording   the last live collection, replayed: for a stage without network. Labelled as recorded.

use(kind) switches the world in place, so modules that imported GOAL or LISTINGS see the new one.
"""
import json
import threading
from datetime import datetime
from pathlib import Path

DEMO = json.loads((Path(__file__).resolve().parent.parent / "data" / "shoes.json").read_text(encoding="utf-8"))
HOSTS = {"Amazon": "amazon.in", "Flipkart": "flipkart.com", "Myntra": "myntra.com"}

GOAL, LISTINGS, SELLERS, EVENT, STORES, SOURCE = {}, {}, {}, {}, [], {}
QUERY = ""
_prices = {}
_dropped = threading.Event()


def use(kind="demo", progress=lambda text: None, headless=None, fresh=False):
    """Switch the world. kind: demo, live (collect if the last collection is over 15 minutes old, or fresh=True)
    or recording. headless: hide Chrome while collecting (None: MARKETPLACE_BROWSER_HEADLESS, default shown)."""
    global QUERY
    if kind == "demo":
        goal, listings, sellers, event, stores = (dict(DEMO["goal"]), DEMO["listings"], DEMO["sellers"], DEMO["event"],
                                                  sorted({x["store"] for x in DEMO["listings"]}))
        source = {"kind": "demo", "label": "Demo stores"}
    else:
        from patterns import live
        evidence = live.latest(sample=kind == "recording")   # live never reuses the shipped sample
        if kind == "live" and (fresh or evidence is None or live.age_seconds(evidence) > live.FRESH_SECONDS):
            if not live.available():
                raise RuntimeError("Playwright is not installed: pip install -r requirements-live.txt")
            progress("Collecting live evidence in Chrome: Amazon, Flipkart, Myntra…")
            evidence = live.collect(DEMO["goal"]["max_price"], headless=headless, progress=progress)
        if evidence is None:
            raise RuntimeError("No recording yet. Run a live collection first.")
        goal, listings, sellers, event, stores = _from_evidence(evidence, recorded=kind == "recording")
        when = datetime.fromisoformat(evidence["observed_at"]).astimezone()
        source = {"kind": kind, "label": ("Live sites" if kind == "live" else "Live · recording") + f" · {when:%d %b %H:%M}",
                  "observed_at": evidence["observed_at"], "sites": evidence.get("sources", [])}
    GOAL.clear(), GOAL.update(goal)
    LISTINGS.clear(), LISTINGS.update({x["id"]: x for x in listings})
    SELLERS.clear(), SELLERS.update(sellers)
    EVENT.clear(), EVENT.update(event)
    STORES[:] = stores
    SOURCE.clear(), SOURCE.update(source)
    QUERY = goal["query"]
    reset()
    return SOURCE


def _from_evidence(ev, recorded):
    """Map the collector's candidates onto listings. Nothing is invented: unknown stays unknown."""
    from patterns import live
    budget = ev.get("budget", DEMO["goal"]["max_price"])
    goal = {"query": f"Black running shoes under ₹{budget:,}", "color": "black", "type": "running", "size": None,
            "max_price": budget}
    listings, sellers = [], {}
    for c in ev["candidates"]:
        lines = []                       # brand and name, up to the first line that carries a price
        for line in c["product_name"].splitlines():
            if "₹" in line or "%" in line:
                break
            lines.append(line)
        name = " ".join(" ".join(lines).split())[:90] or c["marketplace"] + " listing"
        text = (c["product_name"] + " " + c.get("source_excerpt", "")[:400]).lower()
        problems = []
        if not live.on_host(c["source_url"], HOSTS[c["marketplace"]]):
            problems.append("not on the store's own site")
        if c.get("evidence_mode") == "search_index_fallback":
            problems.append("seen only in a search engine's index")
        if c.get("detail_status") != "OBSERVED":
            problems.append("product page not read")
        if not recorded and (datetime.now().astimezone() - datetime.fromisoformat(c["observed_at"])).total_seconds() > live.FRESH_SECONDS:
            problems.append("evidence older than 15 minutes")
        listings.append({"id": c["offer_id"], "store": c["marketplace"], "name": name, "price": round(c["observed_price_inr"]),
                         "type": "running" if "running" in text else "other", "color": "black" if "black" in text else "other",
                         "sizes": None, "seller": c["offer_id"], "url": c["source_url"],
                         "evidence": "product page read" if c.get("detail_status") == "OBSERVED" else
                                     "search index" if c.get("evidence_mode") == "search_index_fallback" else "search page"})
        sellers[c["offer_id"]] = {"verified": not problems,
                                  "note": "; ".join(problems) if problems else f"{c['marketplace']} product page, read just now"
                                  if not recorded else f"{c['marketplace']} product page (recorded)"}
    stores = [s["marketplace"] for s in ev.get("sources", [])] or sorted(HOSTS)
    ok = [x for x in listings if sellers[x["id"]]["verified"] and x["price"] <= budget] or listings or [None]
    pick = min(ok, key=lambda x: x["price"]) if ok[0] else None
    # There is no real price feed: in a live world the event is a scheduled re-check of the stores.
    event = {"id": pick["id"], "old_price": pick["price"], "new_price": pick["price"]} if pick else {}
    return goal, listings, sellers, event, stores


def reset():
    _prices.clear()
    _prices.update({i: x["price"] for i, x in LISTINGS.items()})
    _dropped.clear()


def name(lid):
    return LISTINGS[lid]["name"] if lid in LISTINGS else str(lid)


def price(lid):
    return _prices.get(lid, LISTINGS[lid]["price"])


def label(lid):
    return f"{name(lid)} · ₹{price(lid):,} · {LISTINGS[lid]['store']}" if lid in LISTINGS else str(lid)


def view():
    """What the page draws in its store panel."""
    return [{**x, "price": price(x["id"])} for x in LISTINGS.values()]


def size_text():
    return f"size {GOAL['size']}" if GOAL.get("size") else "size (unverified)"


def dropped_text():
    """What a script that never checks type or size silently drops."""
    return "“running” or “size 9”" if GOAL.get("size") else "“running”"


def proposal(lid):
    """What checkout asks the human, in this world."""
    x = LISTINGS[lid]
    if SOURCE.get("kind") == "demo":
        return f"Verified seller, size {GOAL['size']} in stock, {x['store']}. Buy it?"
    return (f"Product page read on {x['store']}. Size, stock, delivery and the checkout total are not verified: "
            "check them before you buy.")


def event_text(e):
    if e["old_price"] != e["new_price"]:
        return f"{e['name']}: ₹{e['old_price']:,} → ₹{e['new_price']:,}"
    return f"scheduled re-check: {e['name']} at ₹{e['new_price']:,}"


# ---------------------------------------------------------------- tools

def search_catalog(keyword):
    """Keyword search over listing names, the way a store's search box works."""
    return [i for i, x in LISTINGS.items() if keyword.lower() in x["name"].lower()]


def search_store(store, kind=None, color=None):
    """One store's listings, optionally by type and colour."""
    return [i for i, x in LISTINGS.items() if x["store"] == store
            and (kind is None or x["type"] == kind) and (color is None or x["color"] == color)]


def in_stock(lid, size):
    """No size in the query (live sites): nothing to check. A size the page can't show stays unverified."""
    if size is None:
        return True
    return LISTINGS[lid]["sizes"] is not None and size in LISTINGS[lid]["sizes"]


def seller_check(lid):
    s = LISTINGS[lid]["seller"]
    return {"seller": s if s in DEMO["sellers"] else LISTINGS[lid]["store"], **SELLERS[s]}


# ---------------------------------------------------------------- the price feed (Level 3)

def drop_price():
    if EVENT:
        _prices[EVENT["id"]] = EVENT["new_price"]
    _dropped.set()


def wait_for_drop(timeout=None):
    """Block until the price drops (live: until the scheduled re-check). Returns the event, or None on timeout."""
    if not _dropped.wait(timeout) or not EVENT:
        return None
    return {**EVENT, "name": name(EVENT["id"]), "store": LISTINGS[EVENT["id"]]["store"]}


use("demo")
