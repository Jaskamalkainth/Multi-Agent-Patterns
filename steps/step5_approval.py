"""Step 5 · Fix 3: human approval before money moves.

Owner rule + budget, plus a pause before checkout.
LangGraph's interrupt() saves the state and stops. The run resumes when a human answers.
"""
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from lab import llm
from lab.core import State, note, say, watcher_node

TITLE = "Fix 3 · Human approval"
SUBTITLE = "Agents can start on their own. Money moves only when a human says yes."
NEEDS_CHECKPOINT = True

ROLE = {
    "deal": "You are the Deal agent. You are responsible for buying good deals quickly.",
    "budget": "You are the Budget agent. You are responsible for all purchases.",
}
ACTIONS = ["claim", "stand_down", "buy", "recheck"]
MAX_TURNS = 6
MAX_TOKENS = 3_000


def within_budget(state: State):
    return state.get("turn", 0) < MAX_TURNS and state.get("tokens", 0) < MAX_TOKENS


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


# NEW ─────────────────────────────────────────────────────────────
def checkout(state: State):
    item = state["event"]
    proposal = {"item": item["name"], "price": item["price"], "store": item["store"],
                "quantity": 1, "proposed_by": state["owner"]}
    # Same gate as Rahul's n8n flow. Replit's agent deleted a production
    # database in 2025 because nothing like this stood in its way.
    answer = interrupt(proposal)          # pause here; state is saved; resume with a human answer
    if answer != "approve":
        say("checkout", {"action": "cancelled", "say": "Human said no. Nothing ordered."})
        return {"outcome": "Cancelled by human."}
    say("checkout", {"action": "ordered", "say": f"Simulated order: 1 × {item['name']} at ₹{item['price']}."})
    return {"cart": [{"sku": item["sku"], "by": state["owner"]}], "outcome": "Bought 1 item, approved by a human."}
# ─────────────────────────────────────────────────────────────────


def escalate(state: State):
    say("guard", {"action": "stopped", "say": f"Budget hit: {state['turn']} turns, ~{state['tokens']:,} tokens. "
                                               "Stopping and asking a human."})
    return {"outcome": "Stopped by budget. Escalated to a human."}


def route(state: State):
    if not within_budget(state):
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
    return g.compile(checkpointer=MemorySaver())   # NEW: saved state makes pause/resume possible
