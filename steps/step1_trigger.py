"""Step 1 · Self-starting.

Nobody types a prompt. A price change in the world starts the graph.
In production: AWS DevOps Agent starts investigating the moment an alert fires.
watcher → evaluator → done
"""
from langgraph.graph import END, START, StateGraph

from lab import llm
from lab.core import State, say, watcher_node

TITLE = "Self-starting agents"
SUBTITLE = "No prompt, no form. A price change in the world starts the agents."


def evaluator(state: State):
    reply, tok = llm.ask("evaluator", "You are an Evaluator agent. Check the item against the saved goal.",
                         {"event": state["event"]}, ["recommend", "reject"])
    say("evaluator", reply, tok)
    return {"turn": state.get("turn", 0) + 1, "tokens": state.get("tokens", 0) + tok,
            "log": [{"from": "evaluator", **reply}], "outcome": "Recommendation ready. Nobody asked for it."}


def build(chaos=False):
    g = StateGraph(State)
    g.add_node("watcher", watcher_node)
    g.add_node("evaluator", evaluator)
    g.add_edge(START, "watcher")
    g.add_edge("watcher", "evaluator")
    g.add_edge("evaluator", END)
    return g.compile()
