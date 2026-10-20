"""Run one step of the lab.

  python run.py 1                 wait for a price drop (edit the feed or run tools/drop_price.py)
  python run.py 1 --auto-drop 3   the price drops by itself after 3 seconds (one-screen demo)
  python run.py 2                 broken: two agents, no rules
  python run.py 3                 fix 1: one owner per task
  python run.py 4 --chaos         fix 2: budget stops a runaway loop
  python run.py 5                 fix 3: human approval before checkout
  python run.py 5 --chaos         all three fixes together

Steps 2-5 fire the event immediately. Add --watch to wait for a real price change instead.
"""
import argparse
import importlib

from langgraph.errors import GraphRecursionError
from langgraph.types import Command
from rich.prompt import Prompt

from lab import feed, llm
from lab.core import console, header, note, say, summary

STEPS = {1: "step1_trigger", 2: "step2_broken", 3: "step3_owner", 4: "step4_budget", 5: "step5_approval"}
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
    p.add_argument("--yes", action="store_true", help="step 5: approve without asking (for testing)")
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

    # Step 5: the graph paused at interrupt() and is waiting for a human.
    while getattr(mod, "NEEDS_CHECKPOINT", False) and graph.get_state(config).next:
        proposal = graph.get_state(config).tasks[0].interrupts[0].value
        console.print()
        console.print(f"[bold white]{'You':>9}[/] [bold]APPROVAL[/]     Buy {proposal['quantity']} × {proposal['item']} "
                      f"for ₹{proposal['price']} from {proposal['store']}? (proposed by {proposal['proposed_by']} agent)")
        answer = "approve" if args.yes else Prompt.ask(f"{'':>9} Approve or deny", choices=["approve", "deny"],
                                                       default="approve")
        human_inputs += 1
        state, _ = stream(graph, Command(resume=answer), config, state)

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
