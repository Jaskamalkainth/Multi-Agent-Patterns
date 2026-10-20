"""Step 3 · Fix 1: one owner per task.

Same two agents, same prompts. New: a claim rule in code.
The first agent to claim the task owns it. Any other claim is rejected.
"""
from langgraph.graph import END, START, StateGraph

from lab import llm
from lab.core import State, note, say, watcher_node

TITLE = "Fix 1 · One owner per task"
SUBTITLE = "Same agents, same prompts. Code decides who owns the purchase."

ROLE = {
    "deal": "You are the Deal agent. You are responsible for buying good deals quickly.",
    "budget": "You are the Budget agent. You are responsible for all purchases.",
}
ACTIONS = ["claim", "stand_down", "buy", "recheck"]


# NEW ─────────────────────────────────────────────────────────────
def claim(state: State, name: str):
    """First claim wins. Code enforces it, whatever the model says.

    Anthropic's research agents duplicated each other's work until each one
    had a clearly owned task.
    """
    owner = state.get("owner")
    return name if owner in (None, name) else None
# ─────────────────────────────────────────────────────────────────


def make_agent(name, chaos=False):
    def agent(state: State):
        ctx = {"event": state["event"], "other_last": state.get("last"), "turn": state.get("turn", 0),
               "owner": state.get("owner"), "owner_rule": True, "chaos": chaos}
        reply, tok = llm.ask(name, ROLE[name], ctx, ACTIONS)
        update = {"turn": state.get("turn", 0) + 1, "tokens": state.get("tokens", 0) + tok}

        # NEW: claims and purchases go through the ownership rule
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
    order = {"sku": item["sku"], "by": state["owner"]}
    say("checkout", {"action": "ordered", "say": f"Simulated order: 1 × {item['name']} at ₹{item['price']}."})
    note("No human was asked before buying.", "yellow")
    return {"cart": [order], "outcome": "Bought 1 item. Nobody approved it."}


def route(state: State):
    last = state["last"]
    if last["action"] == "buy":
        return "checkout"
    if last["action"] == "stand_down":
        return state["owner"]          # hand back to the owner
    if last["action"] == "recheck":
        return last["from"]            # owner keeps working
    return "budget" if last["from"] == "deal" else "deal"


def build(chaos=False):
    g = StateGraph(State)
    g.add_node("watcher", watcher_node)
    g.add_node("deal", make_agent("deal", chaos))
    g.add_node("budget", make_agent("budget", chaos))
    g.add_node("checkout", checkout)
    g.add_edge(START, "watcher")
    g.add_edge("watcher", "deal")
    g.add_conditional_edges("deal", route, ["deal", "budget", "checkout"])
    g.add_conditional_edges("budget", route, ["deal", "budget", "checkout"])
    g.add_edge("checkout", END)
    return g.compile()
