"""Step 4 · Fix 2: a budget and a stop.

Owner rule from step 3, plus a hard limit on turns and tokens.
Run with --chaos: the owner keeps re-checking prices forever.
Without this fix it would loop until the framework kills it. With it, it stops and escalates.
"""
from langgraph.graph import END, START, StateGraph

from lab import llm
from lab.core import State, note, say, watcher_node

TITLE = "Fix 2 · Budget and stop"
SUBTITLE = "Hard limits on turns and tokens. When hit, stop and hand over to a human."

ROLE = {
    "deal": "You are the Deal agent. You are responsible for buying good deals quickly.",
    "budget": "You are the Budget agent. You are responsible for all purchases.",
}
ACTIONS = ["claim", "stand_down", "buy", "recheck"]

# NEW ─────────────────────────────────────────────────────────────
MAX_TURNS = 6
MAX_TOKENS = 3_000


def within_budget(state: State):
    return state.get("turn", 0) < MAX_TURNS and state.get("tokens", 0) < MAX_TOKENS
# ─────────────────────────────────────────────────────────────────


def claim(state: State, name: str):
    owner = state.get("owner")
    return name if owner in (None, name) else None


def make_agent(name, chaos=False):
    def agent(state: State):
        ctx = {"event": state["event"], "other_last": state.get("last"), "turn": state.get("turn", 0),
               "owner": state.get("owner"), "owner_rule": True, "chaos": chaos}
        reply, tok = llm.ask(name, ROLE[name], ctx, ACTIONS)
        update = {"turn": state.get("turn", 0) + 1, "tokens": state.get("tokens", 0) + tok}
        if reply["action"] in ("claim", "buy"):
            owner = claim(state, name)
            if owner is None:
                reply = {"action": "stand_down", "say": f"Rejected by code: {state['owner']} agent owns this task."}
            else:
                update["owner"] = owner
        say(name, reply, tok)
        update.update(last={"from": name, **reply}, log=[{"from": name, **reply}])
        return update
    return agent


def checkout(state: State):
    item = state["event"]
    say("checkout", {"action": "ordered", "say": f"Simulated order: 1 × {item['name']} at ₹{item['price']}."})
    note("Bought with no human approval. (Rahul's approval gate covers this.)", "yellow")
    return {"cart": [{"sku": item["sku"], "by": state["owner"]}], "outcome": "Bought 1 item. Nobody approved it."}


# NEW ─────────────────────────────────────────────────────────────
def escalate(state: State):
    say("guard", {"action": "stopped", "say": f"Budget hit: {state['turn']} turns, ~{state['tokens']:,} tokens. "
                                               "Stopping and asking a human."})
    return {"outcome": "Stopped by budget. Escalated to a human."}
# ─────────────────────────────────────────────────────────────────


def route(state: State):
    if not within_budget(state):       # NEW: check the budget before every hop
        return "escalate"
    last = state["last"]
    if last["action"] == "buy":
        return "checkout"
    if last["action"] == "stand_down":
        return state["owner"]
    if last["action"] == "recheck":
        return last["from"]
    return "budget" if last["from"] == "deal" else "deal"


def build(chaos=False):
    g = StateGraph(State)
    g.add_node("watcher", watcher_node)
    g.add_node("deal", make_agent("deal", chaos))
    g.add_node("budget", make_agent("budget", chaos))
    g.add_node("checkout", checkout)
    g.add_node("escalate", escalate)
    g.add_edge(START, "watcher")
    g.add_edge("watcher", "deal")
    g.add_conditional_edges("deal", route, ["deal", "budget", "checkout", "escalate"])
    g.add_conditional_edges("budget", route, ["deal", "budget", "checkout", "escalate"])
    g.add_edge("checkout", END)
    g.add_edge("escalate", END)
    return g.compile()
