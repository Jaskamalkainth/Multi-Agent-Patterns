"""Level 0 in CrewAI · a sequential crew. A developer wrote three tasks; Process.sequential runs them in order.

    search task → filter task → pick task        (each task's output is the next one's context)

Same weakness as the LangGraph pipeline: the tasks never mention "running" or "size 9", and the agents
never see the query, so those requirements disappear. Difference: in CrewAI each step is an LLM agent
reading the previous output, not code, so even a fixed pipeline spends a model call per step.
"""
from crewai import Crew, Process

from crews import kit
from crews.contracts import Choice, Shortlist
from patterns import common as c
from patterns import world

TITLE = "Level 0 · Sequential crew"
HUMAN_STEPS = 4
BUDGET = world.GOAL["max_price"]


def build():
    black = lambda: world.search_catalog("black")                                     # noqa: E731
    cheap = lambda: [i for i in black() if world.price(i) <= BUDGET]                  # noqa: E731
    search = kit.agent("search", "Search", "List listings whose name contains 'black'.", Shortlist,
                       lambda: Shortlist(listing_ids=black(), note=f"{len(black())} listings with “black”"))
    filt = kit.agent("filter", "Filter", f"Keep listings priced at or under ₹{BUDGET:,}.", Shortlist,
                     lambda: Shortlist(listing_ids=cheap(), note=f"{len(cheap())} under ₹{BUDGET:,}"))
    pick = kit.agent("pick", "Pick", "Choose the cheapest listing.", Choice,
                     lambda: Choice(listing_id=kit.cheapest(cheap()), reason="Cheapest listing left."))

    def done(me, nxt, state, model):
        def cb(output):
            v = kit.value(output, model)
            if model is Shortlist:
                c.listing(v.listing_ids, state)
                c.status(me, "done", v.note)
                c.msg(me, nxt, "data", v.note)
            else:
                c.listing(v.listing_id, "pick", v.reason)
                c.status(me, "done", world.name(v.listing_id))
                c.msg(me, nxt, "task", f"buy {world.name(v.listing_id)}")
        return cb

    t1 = kit.task("Listings: {listings}\nReturn the IDs of listings whose name contains 'black'.", search, Shortlist,
                  callback=done("search", "filter", "checked", Shortlist))
    t2 = kit.task(f"Listings: {{listings}}\nKeep only the IDs from the previous step priced at or under ₹{BUDGET:,}.",
                  filt, Shortlist, context=[t1], callback=done("filter", "pick", "kept", Shortlist))
    t3 = kit.task("Listings: {listings}\nReturn the cheapest of the IDs from the previous step.", pick, Choice,
                  context=[t2], callback=done("pick", "checkout", "pick", Choice))
    return Crew(agents=[search, filt, pick], tasks=[t1, t2, t3], process=Process.sequential, verbose=False)


def run():
    for id, label in (("search", "Search"), ("filter", "Filter"), ("pick", "Pick")):
        c.agent(id, label)
    c.step("A developer wrote three tasks; Process.sequential runs them in order")
    c.msg("you", "search", "task", world.QUERY)
    result = build().kickoff(inputs={"listings": kit.listings()})
    pick = kit.bought(kit.value(result, Choice).listing_id)
    if pick is None:
        c.status("checkout", "bad", "nothing to buy")
        return {"pick": None, "answer": "Nothing found."}
    c.status("checkout", "done", "ordered")
    c.listing(pick, "bought")
    c.say("checkout", f"Simulated order: 1 × {world.label(pick)}")
    c.note(f"No task mentions {world.dropped_text()}, and no agent sees the query. The requirement disappears.", "bad")
    return {"pick": pick, "answer": kit.value(result, Choice).reason}
