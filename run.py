"""Run one step of the lab.

  python run.py 1                 wait for a price drop (edit the feed or run tools/drop_price.py)
  python run.py 1 --auto-drop 3   the price drops by itself after 3 seconds (one-screen demo)
  python run.py 2                 broken: two agents, no rules
  python run.py 3                 fix 1: one owner per task
  python run.py 4 --chaos         fix 2: budget stops a runaway loop

Steps 2-4 fire the event immediately. Add --watch to wait for a real price change instead.
"""
import argparse
import importlib

from langgraph.errors import GraphRecursionError

from lab import feed, llm
from lab.core import console, header, note, say, summary

STEPS = {1: "step1_trigger", 2: "step2_broken", 3: "step3_owner", 4: "step4_budget"}
RECURSION_LIMIT = 24   # LangGraph's own safety net (default is 25)


def get_event(args):
    feed.reset_feed()
    goal = feed.GOAL
    note(f"Saved goal: {goal['item']} under ₹{goal['max_price']:,}. Mode: {llm.MODE}.")
    if args.watch:
        how = f"auto drop in {args.auto_drop}s" if args.auto_drop is not None else \
              "edit data/price_feed.json or run: python tools/drop_price.py"
        console.print(f"[magenta]{'Watcher':>9}[/] [bold]WATCHING[/]     store feed… nobody is typing ({how})")
        return feed.watch(auto_drop=args.auto_drop)
    before = feed.read_feed()
    feed.drop_price()
    return feed.find_event(before, feed.read_feed())


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("step", type=int, choices=STEPS)
    p.add_argument("--chaos", action="store_true", help="owner agent keeps re-checking forever")
    p.add_argument("--watch", action="store_true", help="wait for a price change in the feed")
    p.add_argument("--auto-drop", type=float, default=None, help="seconds until the price drops by itself")
    args = p.parse_args()
    if args.step == 1 or args.auto_drop is not None:
        args.watch = True

    mod = importlib.import_module(f"steps.{STEPS[args.step]}")
    header(args.step, mod.TITLE, mod.SUBTITLE + ("  [red](--chaos)[/]" if args.chaos else ""))
    graph = mod.build(chaos=args.chaos)

    event = get_event(args)
    config = {"recursion_limit": RECURSION_LIMIT, "configurable": {"thread_id": f"step{args.step}"}}
    human_inputs = 0

    state, killed = stream(graph, {"event": event}, config)
    if killed:
        say("guard", {"action": "killed", "say": f"LangGraph recursion limit ({RECURSION_LIMIT}) hit. "
                                                  "The agents never decided."})
        summary(state, human_inputs, ended="[red]Killed by the framework. Nobody decided.[/]")
        return


    summary(state, human_inputs)


def stream(graph, inp, config, state=None):
    """Run the graph, keeping the latest state. Returns (state, killed_by_recursion_limit)."""
    try:
        for state in graph.stream(inp, config, stream_mode="values"):
            pass
        return state, False
    except GraphRecursionError:
        return state, True


if __name__ == "__main__":
    main()
