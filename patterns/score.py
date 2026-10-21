"""Grade a purchase against the query, the same way for every level and both frameworks.

Demo stores, four checks:            Live sites, four checks (a search page can't show size):
  black running shoe   type, colour     black running shoe   "black" and "running" in the evidence
  size 9 in stock      the user's size  under ₹1,000         the observed price
  under ₹1,000         the price paid   verified evidence    the store's own site, product page read,
  genuine seller       not a reseller                        not a search-index fallback, fresh
                                        cheapest match       no cheaper listing passes the other three
In the demo stores the cheapest-match check isn't needed: the traps are built into the data.
"""
from patterns import world


def checks(lid):
    x, g = world.LISTINGS[lid], world.GOAL
    seller = world.SELLERS[x["seller"]]
    c = {"black running shoe": (x["type"] == g["type"] and x["color"] == g["color"],
                                f"{x['color']} {x['type']}" if world.SOURCE["kind"] == "demo"
                                else ("“black” and “running” in the evidence" if x["type"] == "running" and x["color"] == "black"
                                      else f"evidence says: {'running' if x['type'] == 'running' else 'not running'}, "
                                           f"{'black' if x['color'] == 'black' else 'not black'}"))}
    if g.get("size"):
        c[f"size {g['size']} in stock"] = (g["size"] in (x["sizes"] or []),
                                           "sizes " + ", ".join(map(str, x["sizes"])) if x["sizes"] else "size unverified")
    c[f"under ₹{g['max_price']:,}"] = (world.price(lid) <= g["max_price"], f"₹{world.price(lid):,}")
    who = "genuine seller" if world.SOURCE["kind"] == "demo" else "verified evidence"
    c[who] = (seller["verified"], f"{x['seller']}: {seller['note']}" if world.SOURCE["kind"] == "demo" else seller["note"])
    if world.SOURCE["kind"] != "demo":
        ok = [i for i in world.LISTINGS if _passes(i)]
        best = min((world.price(i) for i in ok), default=None)
        c["cheapest match"] = (best is not None and lid in ok and world.price(lid) == best,
                               f"cheapest match is ₹{best:,}" if best is not None else "nothing passes")
    return c


def _passes(lid):
    x, g = world.LISTINGS[lid], world.GOAL
    return (x["type"] == g["type"] and x["color"] == g["color"] and world.price(lid) <= g["max_price"]
            and world.SELLERS[x["seller"]]["verified"])


def grade(lid):
    """None if nothing was bought, or the pick isn't a listing in this world (a model can invent an id)."""
    if lid not in world.LISTINGS:
        return None
    x, c = world.LISTINGS[lid], checks(lid)
    ok = {k: v[0] for k, v in c.items()}
    return {"pick": lid, "name": x["name"], "store": x["store"], "price": world.price(lid), "url": x.get("url"),
            "checks": ok, "why": {k: v[1] for k, v in c.items()}, "score": sum(ok.values()), "of": len(ok)}
