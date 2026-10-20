"""Step 2 · Break it.

Two agents react to the same event. Both were told purchases are their job.
No ownership rule, no budget, no approval. They argue and both add to cart.
LangGraph's recursion limit is the only thing that stops them.
In the wild: in 2011 two Amazon pricing bots kept reacting to each other
until a textbook was listed at $23.7 million.
"""
from langgraph.graph import START, StateGraph

from lab import llm
from lab.core import State, note, say, watcher_node

TITLE = "Two agents, no rules"
SUBTITLE = "Both agents think the purchase is theirs. Watch the turns, tokens and cart."

ROLE = {
    "deal": "You are the Deal agent. You are responsible for buying good deals quickly.",
    "budget": "You are the Budget agent. You are responsible for all purchases.",
}
ACTIONS = ["claim", "dispute", "add_to_cart"]


def make_agent(name):
    def agent(state: State):
        ctx = {"event": state["event"], "other_last": state.get("last"), "turn": state.get("turn", 0),
               "i_added": any(c["by"] == name for c in state.get("cart", []))}
        reply, tok = llm.ask(name, ROLE[name], ctx, ACTIONS)
        say(name, reply, tok)
        update = {"turn": state.get("turn", 0) + 1, "tokens": state.get("tokens", 0) + tok,
                  "last": {"from": name, **reply}, "log": [{"from": name, **reply}]}
        if reply["action"] == "add_to_cart":
            update["cart"] = [{"sku": state["event"]["sku"], "by": name}]
            note(f"cart now has {len(state.get('cart', [])) + 1} item(s)", "red")
        return update
    return agent


def route(state: State):
    # Whoever spoke last, the other one replies. Nothing ever ends the loop.
    return "budget" if state["last"]["from"] == "deal" else "deal"


def build(chaos=False):
    g = StateGraph(State)
    g.add_node("watcher", watcher_node)
    g.add_node("deal", make_agent("deal"))
    g.add_node("budget", make_agent("budget"))
    g.add_edge(START, "watcher")
    g.add_edge("watcher", "deal")
    g.add_conditional_edges("deal", route, ["deal", "budget"])
    g.add_conditional_edges("budget", route, ["deal", "budget"])
    return g.compile()
